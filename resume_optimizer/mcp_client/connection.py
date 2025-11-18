"""
MCP Client Connection Manager
Implements JSON-RPC 2.0 protocol for communicating with MCP servers
"""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, Any, Optional, List
import asyncio
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages connections to MCP servers and tool invocations.
    Implements proper MCP protocol with JSON-RPC 2.0.
    
    This class handles:
    - Server connection lifecycle (initialize, handshake, ready)
    - Tool discovery via JSON-RPC tools/list
    - Tool invocation via JSON-RPC tools/call
    - Resource fetching via JSON-RPC resources/read
    - Prompt retrieval via JSON-RPC prompts/get
    """
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_configs = self._load_server_configs()
        self._tools_cache: Dict[str, List[Dict]] = {}
    
    def _load_server_configs(self) -> Dict[str, StdioServerParameters]:
        """
        Load MCP server configurations.
        
        Returns:
            Dictionary mapping server names to their connection parameters
        """
        # Default configuration for resume tools server
        base_path = Path(__file__).parent.parent.parent
        
        return {
            "resume-tools": StdioServerParameters(
                command="python",
                args=[str(base_path / "mcp_servers" / "resume_tools_server.py")],
                env=None
            )
        }
    
    async def connect_server(self, server_name: str) -> ClientSession:
        """
        Establish MCP connection with proper initialization handshake.
        
        MCP Connection Lifecycle:
        1. Create STDIO transport
        2. Initialize ClientSession
        3. Perform protocol handshake
        4. Server becomes ready for requests
        
        Args:
            server_name: Name of the MCP server to connect to
            
        Returns:
            Active ClientSession instance
            
        Raises:
            ValueError: If server_name is not configured
            ConnectionError: If handshake fails
        """
        # Return existing session if already connected
        if server_name in self.sessions:
            logger.debug(f"Reusing existing session for {server_name}")
            return self.sessions[server_name]
        
        # Get server configuration
        server_params = self.server_configs.get(server_name)
        if not server_params:
            raise ValueError(
                f"Unknown server: {server_name}. "
                f"Available servers: {list(self.server_configs.keys())}"
            )
        
        try:
            # Phase 1: Create STDIO connection (transport layer)
            logger.info(f"Connecting to MCP server: {server_name}")
            
            # stdio_client returns an async context manager - enter it
            stdio_context = stdio_client(server_params)
            read_stream, write_stream = await stdio_context.__aenter__()
            
            # Phase 2: Create session
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()
            
            # Phase 3: MCP Protocol Initialize (JSON-RPC handshake)
            logger.info(f"Performing MCP handshake with {server_name}")
            await session.initialize()
            
            logger.info(f"MCP connection established for {server_name}")
            
            # Store active session and context for cleanup
            self.sessions[server_name] = session
            if not hasattr(self, '_contexts'):
                self._contexts = {}
            self._contexts[server_name] = (session, stdio_context)
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to {server_name}: {e}")
            raise ConnectionError(f"MCP connection failed for {server_name}: {e}")
    
    async def list_tools(self, server_name: str = "resume-tools") -> List[Dict[str, Any]]:
        """
        Discover available tools via JSON-RPC tools/list request.
        
        Implements MCP specification for tool discovery:
        Request: {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        Response: {"jsonrpc": "2.0", "result": {"tools": [...]}, "id": 1}
        
        Args:
            server_name: Target MCP server
            
        Returns:
            List of tool definitions with schemas:
            [
                {
                    "name": "tool_name",
                    "description": "Tool description",
                    "inputSchema": {...JSON Schema...}
                },
                ...
            ]
        """
        # Check cache first
        if server_name in self._tools_cache:
            logger.debug(f"Returning cached tools for {server_name}")
            return self._tools_cache[server_name]
        
        # Connect to server
        session = await self.connect_server(server_name)
        
        try:
            # JSON-RPC: tools/list
            logger.info(f"📋 Discovering tools from {server_name}")
            tools_response = await session.list_tools()
            
            # Parse response
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools_response.tools
            ]
            
            logger.info(f"[OK] Discovered {len(tools)} tools from {server_name}:")
            for tool in tools:
                logger.info(f"   - {tool['name']}: {tool['description'][:60]}...")
            
            # Cache the results
            self._tools_cache[server_name] = tools
            
            return tools
            
        except Exception as e:
            logger.error(f"❌ Failed to list tools from {server_name}: {e}")
            raise
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: str = "resume-tools"
    ) -> Any:
        """
        Invoke tool via JSON-RPC tools/call request.
        
        Implements MCP specification for tool invocation:
        Request: {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "tool_name", "arguments": {...}},
            "id": 2
        }
        Response: {
            "jsonrpc": "2.0",
            "result": {"content": [...]},
            "id": 2
        }
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool parameters (validated against JSON Schema)
            server_name: Target MCP server
            
        Returns:
            Tool execution result (parsed from response content)
            
        Raises:
            ValueError: If tool doesn't exist or arguments are invalid
            RuntimeError: If tool execution fails
        """
        # Connect to server
        session = await self.connect_server(server_name)
        
        try:
            # JSON-RPC: tools/call
            logger.info(f"[TOOL] Calling tool '{tool_name}' on {server_name}")
            logger.debug(f"   Arguments: {json.dumps(arguments, indent=2)[:200]}...")
            
            result = await session.call_tool(
                name=tool_name,
                arguments=arguments
            )
            
            # Parse result content
            if result.content:
                # Extract text content from response
                content = result.content[0]
                
                # Try to parse as JSON if possible
                try:
                    if hasattr(content, 'text'):
                        parsed = json.loads(content.text)
                        logger.info(f"[OK] Tool '{tool_name}' executed successfully")
                        return parsed
                    else:
                        logger.info(f"[OK] Tool '{tool_name}' executed successfully")
                        return content
                except json.JSONDecodeError:
                    # Return raw text if not JSON
                    logger.info(f"✅ Tool '{tool_name}' executed (non-JSON response)")
                    return content.text if hasattr(content, 'text') else str(content)
            else:
                logger.warning(f"⚠️ Tool '{tool_name}' returned empty content")
                return None
                
        except Exception as e:
            logger.error(f"❌ Tool call failed for '{tool_name}': {e}")
            raise RuntimeError(f"Tool '{tool_name}' execution failed: {e}")
    
    async def get_resource(
        self,
        uri: str,
        server_name: str = "resume-tools"
    ) -> str:
        """
        Fetch resource via JSON-RPC resources/read request.
        
        Implements MCP specification for resource access:
        Request: {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {"uri": "template://resume/professional"},
            "id": 3
        }
        
        Args:
            uri: Resource URI (e.g., template://resume/professional)
            server_name: Target MCP server
            
        Returns:
            Resource content as string
            
        Raises:
            ValueError: If resource URI is invalid or not found
        """
        # Connect to server
        session = await self.connect_server(server_name)
        
        try:
            # JSON-RPC: resources/read
            logger.info(f"[RESOURCE] Fetching resource: {uri}")
            
            resource = await session.read_resource(uri)
            
            # Extract content
            if resource.contents:
                content = resource.contents[0]
                result = content.text if hasattr(content, 'text') else str(content)
                logger.info(f"✅ Resource fetched: {len(result)} bytes")
                return result
            else:
                logger.warning(f"⚠️ Resource '{uri}' returned empty content")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch resource '{uri}': {e}")
            raise ValueError(f"Resource '{uri}' not found or invalid: {e}")
    
    async def get_prompt(
        self,
        prompt_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        server_name: str = "resume-tools"
    ) -> str:
        """
        Get prompt template via JSON-RPC prompts/get request.
        
        Implements MCP specification for prompt retrieval:
        Request: {
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {"name": "prompt_name", "arguments": {...}},
            "id": 4
        }
        
        Args:
            prompt_name: Name of the prompt template
            arguments: Prompt parameters for template rendering
            server_name: Target MCP server
            
        Returns:
            Rendered prompt text ready for LLM consumption
        """
        # Connect to server
        session = await self.connect_server(server_name)
        
        try:
            # JSON-RPC: prompts/get
            logger.info(f"[PROMPT] Getting prompt: {prompt_name}")
            
            prompt = await session.get_prompt(
                name=prompt_name,
                arguments=arguments or {}
            )
            
            # Extract prompt content
            if prompt.messages:
                message = prompt.messages[0]
                
                # Handle different message content types
                if hasattr(message.content, 'text'):
                    result = message.content.text
                elif isinstance(message.content, str):
                    result = message.content
                else:
                    result = str(message.content)
                
                logger.info(f"✅ Prompt retrieved: {len(result)} characters")
                return result
            else:
                logger.warning(f"⚠️ Prompt '{prompt_name}' returned no messages")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Failed to get prompt '{prompt_name}': {e}")
            raise ValueError(f"Prompt '{prompt_name}' not found or invalid: {e}")
    
    async def list_resources(self, server_name: str = "resume-tools") -> List[Dict[str, Any]]:
        """
        List available resources via JSON-RPC resources/list request.
        
        Args:
            server_name: Target MCP server
            
        Returns:
            List of available resources with URIs and descriptions
        """
        session = await self.connect_server(server_name)
        
        try:
            logger.info(f"📋 Listing resources from {server_name}")
            
            resources = await session.list_resources()
            
            result = [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": getattr(resource, 'description', '')
                }
                for resource in resources.resources
            ]
            
            logger.info(f"✅ Found {len(result)} resources")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to list resources: {e}")
            return []
    
    async def list_prompts(self, server_name: str = "resume-tools") -> List[Dict[str, Any]]:
        """
        List available prompts via JSON-RPC prompts/list request.
        
        Args:
            server_name: Target MCP server
            
        Returns:
            List of available prompts with names and descriptions
        """
        session = await self.connect_server(server_name)
        
        try:
            logger.info(f"📋 Listing prompts from {server_name}")
            
            prompts = await session.list_prompts()
            
            result = [
                {
                    "name": prompt.name,
                    "description": getattr(prompt, 'description', ''),
                    "arguments": getattr(prompt, 'arguments', [])
                }
                for prompt in prompts.prompts
            ]
            
            logger.info(f"✅ Found {len(result)} prompts")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to list prompts: {e}")
            return []
    
    async def disconnect_server(self, server_name: str):
        """
        Close connection to specific MCP server.
        
        Args:
            server_name: Name of server to disconnect
        """
        if server_name in self.sessions:
            try:
                # Clean up session and stdio context
                if hasattr(self, '_contexts') and server_name in self._contexts:
                    session, stdio_context = self._contexts[server_name]
                    await session.__aexit__(None, None, None)
                    await stdio_context.__aexit__(None, None, None)
                    del self._contexts[server_name]
                else:
                    session = self.sessions[server_name]
                    await session.__aexit__(None, None, None)
                
                logger.info(f"Disconnected from {server_name}")
            except Exception as e:
                logger.warning(f"Error during disconnect from {server_name}: {e}")
            finally:
                del self.sessions[server_name]
                if server_name in self._tools_cache:
                    del self._tools_cache[server_name]
    
    async def disconnect_all(self):
        """
        Close all active MCP sessions.
        
        Should be called during application shutdown to clean up resources.
        """
        logger.info(f"Disconnecting all MCP servers ({len(self.sessions)} active)")
        
        for server_name in list(self.sessions.keys()):
            await self.disconnect_server(server_name)
        
        logger.info("All MCP connections closed")
    
    def is_connected(self, server_name: str) -> bool:
        """
        Check if connected to specific server.
        
        Args:
            server_name: Name of server to check
            
        Returns:
            True if connected, False otherwise
        """
        return server_name in self.sessions


# Global singleton instance for application-wide use
mcp_client = MCPClientManager()
