"""
Callback-based Logging and Monitoring System for Resume Optimizer
Implements Google ADK callback patterns for comprehensive agent tracking
"""
import logging
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types


# Configure logging
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "agent_workflow.log"),
        logging.StreamHandler()
    ]
)

# Create separate logger for callbacks
callback_logger = logging.getLogger("ResumeOptimizer.Callbacks")
callback_logger.setLevel(logging.DEBUG)


class WorkflowCallbackLogger:
    """
    Comprehensive callback handler for the Resume Optimization workflow.
    
    Implements ADK callback patterns for:
    - Agent lifecycle tracking
    - LLM call monitoring
    - Tool execution logging
    - State change tracking
    - Performance metrics
    - Error tracking
    """
    
    def __init__(self, log_file: str = "workflow_execution.jsonl"):
        """
        Initialize the callback logger.
        
        Args:
            log_file: Path to JSONL log file for structured logs
        """
        self.log_file = LOG_DIR / log_file
        self.execution_id = None
        self.start_time = None
        self.stage_timings = {}
        self.agent_call_counts = {}
        self.tool_call_counts = {}
        self.llm_call_counts = {}
        self.state_changes = []
        
        # Initialize log file
        with open(self.log_file, 'w') as f:
            f.write("")  # Clear file
        
        callback_logger.info(f"WorkflowCallbackLogger initialized. Logging to {self.log_file}")
    
    def _log_event(self, event_type: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a structured event to JSONL file and logger.
        
        Args:
            event_type: Type of event (e.g., "agent_start", "tool_call")
            details: Additional event details
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "execution_id": self.execution_id,
            "event_type": event_type,
            "details": details or {}
        }
        
        # Write to JSONL file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Also log to standard logger
        callback_logger.info(f"[{event_type}] {json.dumps(details, indent=None)}")
    
    # ==================== AGENT LIFECYCLE CALLBACKS ====================
    
    def before_agent_callback(
        self, 
        callback_context: CallbackContext,
        *args,
        **kwargs
    ) -> Optional[types.Content]:
        """
        Called BEFORE each agent starts execution.
        
        Use cases:
        - Initialize execution tracking
        - Log agent invocation
        - Track session state before agent runs
        
        Args:
            callback_context: Context with session state, agent info
            
        Returns:
            None to allow agent execution, or Content to skip agent
        """
        agent_name = callback_context.agent_name
        invocation_id = callback_context.invocation_id
        
        # Initialize execution tracking on first agent call
        if self.execution_id is None:
            self.execution_id = str(uuid.uuid4())
            self.start_time = time.time()
            callback_logger.info(f"🚀 Starting new workflow execution: {self.execution_id}")
        
        # Track agent call
        self.agent_call_counts[agent_name] = self.agent_call_counts.get(agent_name, 0) + 1
        
        # Log agent start
        self._log_event("agent_start", {
            "agent_name": agent_name,
            "invocation_id": invocation_id,
            "call_count": self.agent_call_counts[agent_name],
            "session_state_keys": list(callback_context.state.keys()) if hasattr(callback_context, 'state') else []
        })
        
        callback_logger.info(
            f"📥 [Invocation: {invocation_id}] Agent '{agent_name}' starting "
            f"(call #{self.agent_call_counts[agent_name]})"
        )
        
        # Record stage start time
        if agent_name not in self.stage_timings:
            self.stage_timings[agent_name] = {"start": time.time()}
        
        return None  # Allow agent to proceed
    
    def after_agent_callback(
        self,
        callback_context: CallbackContext,
        result: types.Content,
        *args,
        **kwargs
    ) -> Optional[types.Content]:
        """
        Called AFTER each agent completes execution.
        
        Use cases:
        - Log agent completion
        - Track execution time
        - Capture output
        - Monitor state changes
        
        Args:
            callback_context: Context with session state, agent info
            result: Agent's output Content
            
        Returns:
            None to use original result, or Content to replace result
        """
        agent_name = callback_context.agent_name
        invocation_id = callback_context.invocation_id
        
        # Calculate execution time
        if agent_name in self.stage_timings and "start" in self.stage_timings[agent_name]:
            execution_time = time.time() - self.stage_timings[agent_name]["start"]
            self.stage_timings[agent_name]["duration"] = execution_time
        else:
            execution_time = 0
        
        # Extract result text if available
        result_preview = ""
        if result and hasattr(result, 'parts') and result.parts:
            result_text = result.parts[0].text if hasattr(result.parts[0], 'text') else ""
            result_preview = result_text[:200] if result_text else "No text content"
        
        # Log agent completion
        self._log_event("agent_complete", {
            "agent_name": agent_name,
            "invocation_id": invocation_id,
            "execution_time_seconds": round(execution_time, 3),
            "result_preview": result_preview,
            "session_state_keys": list(callback_context.state.keys()) if hasattr(callback_context, 'state') else []
        })
        
        callback_logger.info(
            f"✅ [Invocation: {invocation_id}] Agent '{agent_name}' completed "
            f"in {execution_time:.2f}s"
        )
        
        return None  # Use original result
    
    # ==================== LLM INTERACTION CALLBACKS ====================
    
    def before_model_callback(
        self,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
        *args,
        **kwargs
    ) -> Optional[LlmResponse]:
        """
        Called BEFORE each LLM call.
        
        Use cases:
        - Log prompts sent to LLM
        - Track token usage estimates
        - Monitor model configuration
        - Implement guardrails (optional)
        
        Args:
            callback_context: Context with agent info
            llm_request: Request being sent to LLM
            
        Returns:
            None to proceed with LLM call, or LlmResponse to skip
        """
        agent_name = callback_context.agent_name
        invocation_id = callback_context.invocation_id
        
        # Track LLM calls
        self.llm_call_counts[agent_name] = self.llm_call_counts.get(agent_name, 0) + 1
        
        # Extract prompt info
        prompt_length = 0
        last_user_message = ""
        if llm_request.contents:
            for content in llm_request.contents:
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        if hasattr(part, 'text'):
                            text = part.text or ""
                            prompt_length += len(text)
                            if content.role == 'user':
                                last_user_message = text[:100]  # First 100 chars
        
        # Log LLM call
        self._log_event("llm_call", {
            "agent_name": agent_name,
            "invocation_id": invocation_id,
            "llm_call_number": self.llm_call_counts[agent_name],
            "model": llm_request.model if hasattr(llm_request, 'model') else "unknown",
            "prompt_length_chars": prompt_length,
            "last_user_message_preview": last_user_message,
            "system_instruction_present": bool(llm_request.config.system_instruction) if hasattr(llm_request, 'config') and llm_request.config else False
        })
        
        callback_logger.debug(
            f"🤖 [Invocation: {invocation_id}] LLM call #{self.llm_call_counts[agent_name]} "
            f"for agent '{agent_name}' - Prompt: {prompt_length} chars"
        )
        
        return None  # Allow LLM call to proceed
    
    def after_model_callback(
        self,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
        *args,
        **kwargs
    ) -> Optional[LlmResponse]:
        """
        Called AFTER receiving LLM response.
        
        Use cases:
        - Log LLM responses
        - Track response quality
        - Monitor errors
        - Extract structured data
        
        Args:
            callback_context: Context with agent info
            llm_response: Response from LLM
            
        Returns:
            None to use original response, or LlmResponse to replace
        """
        agent_name = callback_context.agent_name
        invocation_id = callback_context.invocation_id
        
        # Extract response info
        response_length = 0
        response_preview = ""
        has_tool_call = False
        
        if llm_response and hasattr(llm_response, 'content') and llm_response.content:
            if hasattr(llm_response.content, 'parts') and llm_response.content.parts:
                for part in llm_response.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_length += len(part.text)
                        if not response_preview:
                            response_preview = part.text[:150]
                    if hasattr(part, 'function_call'):
                        has_tool_call = True
        
        # Check for errors
        has_error = bool(llm_response.error_message if hasattr(llm_response, 'error_message') else False)
        
        # Log LLM response
        self._log_event("llm_response", {
            "agent_name": agent_name,
            "invocation_id": invocation_id,
            "response_length_chars": response_length,
            "response_preview": response_preview,
            "has_tool_call": has_tool_call,
            "has_error": has_error,
            "error_message": llm_response.error_message if has_error else None
        })
        
        callback_logger.debug(
            f"💬 [Invocation: {invocation_id}] LLM response for '{agent_name}' - "
            f"{response_length} chars, tool_call={has_tool_call}"
        )
        
        if has_error:
            callback_logger.error(
                f"❌ [Invocation: {invocation_id}] LLM error for '{agent_name}': "
                f"{llm_response.error_message}"
            )
        
        return None  # Use original response
    
    # ==================== TOOL EXECUTION CALLBACKS ====================
    
    def before_tool_callback(
        self,
        tool_context: ToolContext,
        *args,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Called BEFORE each tool execution.
        
        Use cases:
        - Log tool calls
        - Track tool usage
        - Validate arguments
        - Monitor external API calls
        
        Args:
            tool_context: Context with tool info and arguments
            
        Returns:
            None to execute tool, or dict to skip and return result
        """
        agent_name = tool_context.agent_name
        invocation_id = tool_context.invocation_id
        tool_name = getattr(tool_context, 'tool_name', 'unknown_tool')
        
        # Track tool calls
        self.tool_call_counts[tool_name] = self.tool_call_counts.get(tool_name, 0) + 1
        
        # Get tool arguments (sanitize sensitive data)
        tool_args = {}
        if hasattr(tool_context, 'arguments'):
            tool_args = {k: str(v)[:100] for k, v in (tool_context.arguments or {}).items()}
        
        # Log tool call
        self._log_event("tool_call", {
            "agent_name": agent_name,
            "invocation_id": invocation_id,
            "tool_name": tool_name,
            "tool_call_number": self.tool_call_counts[tool_name],
            "arguments": tool_args
        })
        
        callback_logger.info(
            f"🔧 [Invocation: {invocation_id}] Tool call #{self.tool_call_counts[tool_name]} "
            f"- '{tool_name}' by agent '{agent_name}'"
        )
        
        return None  # Allow tool execution
    
    def after_tool_callback(
        self,
        tool_context: ToolContext,
        tool_result: Dict[str, Any],
        *args,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Called AFTER tool execution completes.
        
        Use cases:
        - Log tool results
        - Track success/failure
        - Monitor performance
        - Post-process results
        
        Args:
            tool_context: Context with tool info
            tool_result: Result returned by tool
            
        Returns:
            None to use original result, or dict to replace result
        """
        agent_name = tool_context.agent_name
        invocation_id = tool_context.invocation_id
        tool_name = getattr(tool_context, 'tool_name', 'unknown_tool')
        
        # Extract result info
        result_preview = str(tool_result)[:200] if tool_result else "None"
        result_size = len(str(tool_result)) if tool_result else 0
        
        # Check for errors in result
        is_error = isinstance(tool_result, dict) and "error" in tool_result
        
        # Log tool result
        self._log_event("tool_result", {
            "agent_name": agent_name,
            "invocation_id": invocation_id,
            "tool_name": tool_name,
            "result_preview": result_preview,
            "result_size_chars": result_size,
            "is_error": is_error
        })
        
        if is_error:
            callback_logger.warning(
                f"⚠️ [Invocation: {invocation_id}] Tool '{tool_name}' returned error: "
                f"{tool_result.get('error', 'Unknown error')}"
            )
        else:
            callback_logger.info(
                f"✓ [Invocation: {invocation_id}] Tool '{tool_name}' completed - "
                f"{result_size} chars"
            )
        
        return None  # Use original result
    
    # ==================== WORKFLOW SUMMARY ====================
    
    def generate_execution_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the workflow execution.
        
        Returns:
            Dict with execution metrics and summary
        """
        total_time = time.time() - self.start_time if self.start_time else 0
        
        summary = {
            "execution_id": self.execution_id,
            "total_execution_time_seconds": round(total_time, 3),
            "total_agents_called": len(self.agent_call_counts),
            "total_agent_invocations": sum(self.agent_call_counts.values()),
            "total_llm_calls": sum(self.llm_call_counts.values()),
            "total_tool_calls": sum(self.tool_call_counts.values()),
            "agent_breakdown": self.agent_call_counts,
            "llm_call_breakdown": self.llm_call_counts,
            "tool_call_breakdown": self.tool_call_counts,
            "stage_timings": {
                agent: timing.get("duration", 0) 
                for agent, timing in self.stage_timings.items()
            }
        }
        
        # Log final summary
        self._log_event("execution_summary", summary)
        
        callback_logger.info("=" * 80)
        callback_logger.info(f"📊 WORKFLOW EXECUTION SUMMARY")
        callback_logger.info(f"   Execution ID: {self.execution_id}")
        callback_logger.info(f"   Total Time: {total_time:.2f}s")
        callback_logger.info(f"   Agents Called: {len(self.agent_call_counts)}")
        callback_logger.info(f"   LLM Calls: {sum(self.llm_call_counts.values())}")
        callback_logger.info(f"   Tool Calls: {sum(self.tool_call_counts.values())}")
        callback_logger.info("=" * 80)
        
        return summary


# ==================== HELPER FUNCTIONS ====================

def get_callback_logger(log_file: str = "workflow_execution.jsonl") -> WorkflowCallbackLogger:
    """
    Factory function to create a callback logger instance.
    
    Args:
        log_file: Name of log file
        
    Returns:
        Configured WorkflowCallbackLogger instance
    """
    return WorkflowCallbackLogger(log_file=log_file)
