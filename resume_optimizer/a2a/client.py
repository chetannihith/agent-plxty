"""
A2A Protocol Client
For communicating with other A2A-compliant agents
"""
import httpx
from typing import Dict, Any, Optional, List
import json

from .messages import (
    JSONRPCRequest, JSONRPCResponse, A2AMessage, 
    MessageRole, TextPart, A2ATask
)
from .agent_card import AgentCard


class A2AClient:
    """
    Client for A2A Protocol communication
    Discovers agents and sends messages via JSON-RPC
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize A2A client
        
        Args:
            base_url: Base URL of the A2A agent (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.agent_card: Optional[AgentCard] = None
    
    async def discover_agent(self) -> AgentCard:
        """
        Discover agent via Agent Card
        Fetches /.well-known/agent-card.json
        
        Returns:
            AgentCard object with agent capabilities
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/.well-known/agent-card.json",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            self.agent_card = AgentCard(**response.json())
            return self.agent_card
    
    async def send_message(
        self,
        message: str,
        skill_id: Optional[str] = None,
        author: str = "client-user",
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send message to agent via JSON-RPC
        
        Args:
            message: Text message to send
            skill_id: Optional skill ID to invoke
            author: Message author identifier
            additional_params: Additional parameters to include
        
        Returns:
            Response from agent
        """
        # Create A2A message
        a2a_message = A2AMessage(
            role=MessageRole.USER,
            author=author,
            parts=[TextPart(text=message)]
        )
        
        # Build params
        params = {
            "message": json.loads(a2a_message.json()),
        }
        
        if skill_id:
            params["skill_id"] = skill_id
        
        if additional_params:
            params.update(additional_params)
        
        # Create JSON-RPC request
        rpc_request = JSONRPCRequest(
            method="message/send",
            params=params,
            id=f"req-{hash(message)}"
        )
        
        # Send request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/message:send",
                json=json.loads(rpc_request.json()),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            rpc_response = JSONRPCResponse(**response.json())
            
            if rpc_response.error:
                raise Exception(
                    f"RPC Error [{rpc_response.error.code}]: {rpc_response.error.message}"
                )
            
            return rpc_response.result
    
    async def invoke_skill(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        author: str = "client-user"
    ) -> Dict[str, Any]:
        """
        Invoke a specific skill with structured input
        
        Args:
            skill_id: Skill ID to invoke
            input_data: Structured input data matching skill schema
            author: Message author identifier
        
        Returns:
            Skill execution result
        """
        # Create message with structured input
        message_text = json.dumps(input_data)
        
        return await self.send_message(
            message=message_text,
            skill_id=skill_id,
            author=author,
            additional_params={"input": input_data}
        )
    
    async def create_task(
        self,
        skill_id: str,
        input_data: Dict[str, Any]
    ) -> A2ATask:
        """
        Create async task
        
        Args:
            skill_id: Skill ID to execute
            input_data: Input data for the skill
        
        Returns:
            Task object with tracking ID
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/tasks",
                json={
                    "skill_id": skill_id,
                    "input": input_data
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return A2ATask(**result["task"])
    
    async def get_task(self, task_id: str) -> A2ATask:
        """
        Get task status
        
        Args:
            task_id: Task ID to check
        
        Returns:
            Task object with current status
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/tasks/{task_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return A2ATask(**result["task"])
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[A2ATask]:
        """
        List tasks
        
        Args:
            status: Filter by status (pending, in_progress, completed, failed, cancelled)
            limit: Max number of tasks to return
            offset: Pagination offset
        
        Returns:
            List of tasks
        """
        async with httpx.AsyncClient() as client:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            
            response = await client.get(
                f"{self.base_url}/v1/tasks",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return [A2ATask(**task) for task in result["tasks"]]
    
    async def cancel_task(self, task_id: str) -> A2ATask:
        """
        Cancel a task
        
        Args:
            task_id: Task ID to cancel
        
        Returns:
            Updated task object
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/v1/tasks/{task_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return A2ATask(**result["task"])
    
    async def list_skills(self) -> List[Dict[str, Any]]:
        """
        List agent skills
        
        Returns:
            List of skill definitions
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/skills",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result["skills"]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check agent health
        
        Returns:
            Health status information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()


# Example usage
async def example_usage():
    """
    Example: Using A2A Client to communicate with Resume Optimizer Agent
    """
    # Create client
    client = A2AClient("http://localhost:8000")
    
    # Discover agent
    print("Discovering agent...")
    agent_card = await client.discover_agent()
    print(f"Connected to: {agent_card.name}")
    print(f"Description: {agent_card.description}")
    print(f"Skills: {[s.name for s in agent_card.skills]}\n")
    
    # List available skills
    print("Listing skills...")
    skills = await client.list_skills()
    for skill in skills:
        print(f"- {skill['name']}: {skill['description']}")
    print()
    
    # Invoke optimize-resume skill
    print("Invoking optimize-resume skill...")
    response = await client.invoke_skill(
        skill_id="optimize-resume",
        input_data={
            "resume_content": "John Doe\nSoftware Engineer with 5 years experience...",
            "job_description": "Looking for Senior Python Developer with AWS experience..."
        }
    )
    print(f"ATS Score: {response.get('result', {}).get('ats_score')}")
    print(f"Quality Score: {response.get('result', {}).get('quality_score')}\n")
    
    # Create async task
    print("Creating async task...")
    task = await client.create_task(
        skill_id="calculate-ats-score",
        input_data={
            "resume_text": "Python developer with cloud experience...",
            "job_description": "Looking for Python developer..."
        }
    )
    print(f"Task created: {task.id}")
    print(f"Status: {task.status}\n")
    
    # Check task status
    print("Checking task status...")
    task_status = await client.get_task(task.id)
    print(f"Task {task_status.id}: {task_status.status}")
    if task_status.output:
        print(f"Result: {task_status.output}")
    
    # Health check
    print("\nHealth check...")
    health = await client.health_check()
    print(f"Status: {health['status']}")
    print(f"Version: {health['version']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
