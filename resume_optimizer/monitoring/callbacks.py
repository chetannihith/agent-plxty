"""
Simple callback-based logging for agent workflow
Records all events to log file without analysis
"""
import logging
from datetime import datetime
from typing import Any, Dict
import json
from pathlib import Path

# Create logs directory
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
log_filename = LOG_DIR / f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ResumePipeline')


def log_workflow_start(workflow_name: str, **kwargs):
    """Callback: Workflow started"""
    logger.info(f"=" * 80)
    logger.info(f"WORKFLOW STARTED: {workflow_name}")
    for key, value in kwargs.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"=" * 80)


def log_workflow_end(workflow_name: str, **kwargs):
    """Callback: Workflow completed"""
    logger.info(f"=" * 80)
    logger.info(f"WORKFLOW COMPLETED: {workflow_name}")
    for key, value in kwargs.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"=" * 80)


def log_agent_start(agent_name: str, stage: str = "", **kwargs):
    """Callback: Agent execution started"""
    logger.info(f"\n{'─' * 60}")
    logger.info(f"AGENT START: {agent_name} {f'(Stage {stage})' if stage else ''}")
    for key, value in kwargs.items():
        if isinstance(value, (dict, list)):
            logger.info(f"  {key}: {json.dumps(value, indent=2)}")
        else:
            logger.info(f"  {key}: {value}")


def log_agent_end(agent_name: str, execution_time: float = 0, **kwargs):
    """Callback: Agent execution completed"""
    logger.info(f"AGENT COMPLETE: {agent_name}")
    logger.info(f"  Execution Time: {execution_time:.2f}s")
    for key, value in kwargs.items():
        if isinstance(value, (dict, list)):
            logger.info(f"  {key}: {json.dumps(value, indent=2)[:500]}...")
        else:
            logger.info(f"  {key}: {value}")
    logger.info(f"{'─' * 60}\n")


def log_agent_error(agent_name: str, error: str, **kwargs):
    """Callback: Agent encountered error"""
    logger.error(f"❌ AGENT ERROR: {agent_name}")
    logger.error(f"  Error: {error}")
    for key, value in kwargs.items():
        logger.error(f"  {key}: {value}")


def log_tool_call(agent_name: str, tool_name: str, **kwargs):
    """Callback: Tool invocation"""
    logger.info(f"  🔧 TOOL CALL: {tool_name} (called by {agent_name})")
    for key, value in kwargs.items():
        logger.info(f"    {key}: {value}")


def log_tool_result(agent_name: str, tool_name: str, result_preview: str, **kwargs):
    """Callback: Tool result received"""
    logger.info(f"  ✅ TOOL RESULT: {tool_name}")
    logger.info(f"    Result: {result_preview}")
    for key, value in kwargs.items():
        logger.info(f"    {key}: {value}")


def log_state_update(agent_name: str, state_keys: list, **kwargs):
    """Callback: Session state updated"""
    logger.info(f"  📦 STATE UPDATE: {agent_name}")
    logger.info(f"    Updated keys: {state_keys}")
    for key, value in kwargs.items():
        logger.info(f"    {key}: {value}")


def log_event(event_type: str, message: str, **kwargs):
    """Callback: Generic event logging"""
    logger.info(f"  📨 EVENT: {event_type}")
    logger.info(f"    {message}")
    for key, value in kwargs.items():
        if isinstance(value, (dict, list)):
            logger.info(f"    {key}: {json.dumps(value, indent=2)[:300]}...")
        else:
            logger.info(f"    {key}: {value}")


def log_stage_transition(from_stage: str, to_stage: str, **kwargs):
    """Callback: Pipeline stage transition"""
    logger.info(f"\n{'━' * 80}")
    logger.info(f"STAGE TRANSITION: {from_stage} → {to_stage}")
    logger.info(f"{'━' * 80}\n")


def log_custom(message: str, level: str = "INFO", **kwargs):
    """Callback: Custom log message"""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)
    for key, value in kwargs.items():
        log_func(f"  {key}: {value}")


# Export log file path for reference
def get_current_log_file():
    """Get path to current log file"""
    return str(log_filename)
