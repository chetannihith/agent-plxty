# Callback-Based Monitoring Integration Guide

This guide explains how to integrate the comprehensive callback-based logging and monitoring system into your Resume Optimizer workflow.

## 🎯 Overview

The monitoring system uses **Google ADK callbacks** to track:
- Agent lifecycle (start/complete)
- LLM interactions (requests/responses)  
- Tool executions
- Performance metrics
- Errors and warnings
- State changes

## 📁 Files Created

```
monitoring/
├── __init__.py           # Module initialization
├── callback_logger.py    # Core callback implementation
├── log_analyzer.py       # Log analysis utility
├── README.md            # Monitoring system docs
└── INTEGRATION.md       # This file

logs/                    # Auto-created on first run
├── agent_workflow.log
├── workflow_execution.jsonl
└── execution_report.txt
```

## 🔧 Integration Steps

### Step 1: Import the Callback Logger

Add to your orchestrator file (`resume_optimizer/workflow/orchestrator.py`):

```python
from monitoring import get_callback_logger
```

### Step 2: Initialize in Workflow Class

In the `__init__` method:

```python
class ResumeOptimizerWorkflow:
    def __init__(self, model: str = "gemini-2.0-flash", vector_store_path: str = "./data/vector_db"):
        self.model = model
        self.vector_store_path = vector_store_path
        
        # Initialize callback logger
        self.callback_logger = get_callback_logger("resume_workflow.jsonl")
        
        # Rest of initialization...
        self._init_agents()
        self.workflow = self._build_workflow()
```

### Step 3: Add Callbacks to LlmAgents

For each LlmAgent, add callback parameters to the factory functions:

**Example - skills_matcher_agent.py:**

```python
def create_skills_matcher_agent(
    model: str = "gemini-2.0-flash",
    # Add callback parameters
    before_agent_callback=None,
    after_agent_callback=None,
    before_model_callback=None,
    after_model_callback=None,
    before_tool_callback=None,
    after_tool_callback=None
) -> LlmAgent:
    
    return LlmAgent(
        name="skills_matcher_agent",
        model=model,
        description="...",
        instruction="...",
        output_key="skills_analysis",
        # Attach callbacks
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
        before_model_callback=before_model_callback,
        after_model_callback=after_model_callback,
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback
    )
```

**Update agent initialization in orchestrator:**

```python
def _init_agents(self):
    # ... other agents ...
    
    self.skills_matcher = create_skills_matcher_agent(
        model=self.model,
        before_agent_callback=self.callback_logger.before_agent_callback,
        after_agent_callback=self.callback_logger.after_agent_callback,
        before_model_callback=self.callback_logger.before_model_callback,
        after_model_callback=self.callback_logger.after_model_callback,
        before_tool_callback=self.callback_logger.before_tool_callback,
        after_tool_callback=self.callback_logger.after_tool_callback
    )
```

### Step 4: Add Callbacks to BaseAgents

For custom agents inheriting from `BaseAgent`, pass callbacks to the constructor:

**Example - ProfileRAGAgent:**

```python
self.profile_rag = ProfileRAGAgent(
    name="profile_rag_agent",
    before_agent_callback=self.callback_logger.before_agent_callback,
    after_agent_callback=self.callback_logger.after_agent_callback
)
```

If the agent class doesn't accept these parameters, you can modify the `__init__`:

```python
class ProfileRAGAgent(BaseAgent):
    def __init__(
        self, 
        name: str = "profile_rag_agent",
        before_agent_callback=None,
        after_agent_callback=None
    ):
        super().__init__(
            name=name,
            before_agent_callback=before_agent_callback,
            after_agent_callback=after_agent_callback
        )
```

### Step 5: Generate Execution Summary

At the end of workflow execution, generate a summary:

```python
def run_workflow(self, ...):
    # ... workflow execution ...
    
    # Generate execution summary
    summary = self.callback_logger.generate_execution_summary()
    
    # Include in results
    final_results = {
        # ... other results ...
        "execution_summary": summary
    }
    
    return final_results
```

## 📊 Using the Monitoring System

### View Real-Time Logs

```bash
# Human-readable log
tail -f logs/agent_workflow.log

# Structured JSONL
tail -f logs/workflow_execution.jsonl
```

### Analyze After Execution

```python
from monitoring.log_analyzer import analyze_logs

# Generate and display report
analyze_logs("resume_workflow.jsonl")
```

### Programmatic Access

```python
from monitoring.log_analyzer import LogAnalyzer
from pathlib import Path

# Load logs
analyzer = LogAnalyzer(Path("./logs/workflow_execution.jsonl"))

# Get agent statistics
stats = analyzer.get_agent_statistics()
print(f"Profile RAG Agent: {stats['profile_rag_agent']}")

# Get timeline
timeline = analyzer.get_execution_timeline()
for event in timeline[:5]:
    print(f"{event['timestamp']}: {event['event_type']}")
```

## 🎨 Callback Types and Use Cases

### Agent Lifecycle Callbacks

```python
before_agent_callback  # Log agent start, track invocations
after_agent_callback   # Log completion, measure execution time
```

**When triggered:**
- Before/after each agent's `_run_async_impl()` executes

### LLM Interaction Callbacks

```python
before_model_callback  # Log prompts, track token usage
after_model_callback   # Log responses, capture errors
```

**When triggered:**
- Before/after each LLM API call

### Tool Execution Callbacks

```python
before_tool_callback  # Log tool calls, validate arguments
after_tool_callback   # Log results, track failures
```

**When triggered:**
- Before/after each tool function execution

## 📈 Example Output

### Console Log (agent_workflow.log)

```
2025-11-18 10:30:45,123 - INFO - ResumeOptimizer.Callbacks - 🚀 Starting new workflow execution: abc-123
2025-11-18 10:30:45,456 - INFO - ResumeOptimizer.Callbacks - 📥 [Invocation: inv-001] Agent 'profile_rag_agent' starting (call #1)
2025-11-18 10:30:46,789 - INFO - ResumeOptimizer.Callbacks - ✅ [Invocation: inv-001] Agent 'profile_rag_agent' completed in 1.33s
2025-11-18 10:30:47,012 - INFO - ResumeOptimizer.Callbacks - 🤖 [Invocation: inv-002] LLM call #1 for agent 'skills_matcher_agent' - Prompt: 1523 chars
```

### Structured Log (workflow_execution.jsonl)

```jsonl
{"timestamp": "2025-11-18T10:30:45.123", "execution_id": "abc-123", "event_type": "agent_start", "details": {"agent_name": "profile_rag_agent", "invocation_id": "inv-001", "call_count": 1}}
{"timestamp": "2025-11-18T10:30:46.789", "execution_id": "abc-123", "event_type": "agent_complete", "details": {"agent_name": "profile_rag_agent", "execution_time_seconds": 1.333}}
{"timestamp": "2025-11-18T10:30:47.012", "execution_id": "abc-123", "event_type": "llm_call", "details": {"agent_name": "skills_matcher_agent", "llm_call_number": 1, "prompt_length_chars": 1523}}
```

### Analysis Report (execution_report.txt)

```
================================================================================
WORKFLOW EXECUTION ANALYSIS REPORT
================================================================================

Total Events Logged: 47
Total Agents: 10

--------------------------------------------------------------------------------
AGENT STATISTICS
--------------------------------------------------------------------------------

profile_rag_agent:
  Calls: 1
  LLM Calls: 0
  Tool Calls: 1
  Avg Execution Time: 1.33s
  Max Execution Time: 1.33s

skills_matcher_agent:
  Calls: 1
  LLM Calls: 2
  Tool Calls: 0
  Avg Execution Time: 3.45s
  Max Execution Time: 3.45s

================================================================================
```

## 🔍 Troubleshooting

### Callbacks Not Firing

**Issue:** No logs being generated

**Solutions:**
1. Verify callback logger is initialized in workflow
2. Check that callbacks are passed to agent constructors
3. Ensure `logs/` directory has write permissions

### Missing Agent Statistics

**Issue:** Some agents not appearing in reports

**Solutions:**
1. Confirm agent has callbacks attached
2. Check agent name matches expected value
3. Verify agent is actually being executed

### Large Log Files

**Issue:** JSONL files growing too large

**Solutions:**
1. Implement log rotation
2. Archive old executions
3. Add log cleanup to workflow

```python
# Example cleanup
import shutil
from datetime import datetime, timedelta

def cleanup_old_logs(days=7):
    log_dir = Path("./logs")
    cutoff = datetime.now() - timedelta(days=days)
    
    for log_file in log_dir.glob("*.jsonl"):
        if log_file.stat().st_mtime < cutoff.timestamp():
            log_file.unlink()
```

## 🎓 Best Practices

1. **✅ Review logs after each run** - Identify issues early
2. **✅ Archive important executions** - Keep successful runs for reference
3. **✅ Set up log rotation** - Prevent disk space issues
4. **✅ Monitor error rates** - Track quality over time
5. **✅ Use execution_id** - Include in bug reports for traceability
6. **✅ Analyze performance** - Identify bottlenecks for optimization

## 📚 Advanced Usage

### Custom Event Logging

Add custom events to track domain-specific metrics:

```python
# In your workflow code
self.callback_logger._log_event("custom_event", {
    "metric_name": "resume_quality_score",
    "value": 87.5,
    "threshold": 80.0
})
```

### Integration with Monitoring Tools

Export to external monitoring systems:

```python
import requests

def send_to_monitoring_service(summary):
    """Send execution summary to external service"""
    requests.post(
        "https://monitoring.example.com/api/metrics",
        json=summary
    )

# After workflow
summary = self.callback_logger.generate_execution_summary()
send_to_monitoring_service(summary)
```

### Real-Time Dashboards

Use tools like Grafana or Datadog to visualize:

```bash
# Stream JSONL to monitoring pipeline
tail -f logs/workflow_execution.jsonl | \
  jq -c '. | select(.event_type == "agent_complete")' | \
  curl -X POST -d @- http://monitoring-service/ingest
```

## ✅ Checklist

Before deploying with monitoring:

- [ ] Callback logger initialized in workflow
- [ ] All LlmAgents have callbacks attached
- [ ] Custom BaseAgents support callback parameters
- [ ] Execution summary generated at workflow end
- [ ] Log directory created and writable
- [ ] .gitignore updated to exclude logs
- [ ] Log rotation configured (if needed)
- [ ] Team trained on log analysis

## 🆘 Support

For questions or issues:

1. Check the monitoring README.md
2. Review example implementations
3. Verify ADK version compatibility (requires ADK >= 1.4.0)
4. Check logs for callback errors

The monitoring system is production-ready and requires no changes to existing agent logic! 🎉
