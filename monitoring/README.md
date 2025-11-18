# Monitoring and Logging System

Comprehensive callback-based logging and monitoring for the Resume Optimizer workflow using Google ADK best practices.

## Features

✅ **Agent Lifecycle Tracking** - Monitor when agents start and complete
✅ **LLM Call Monitoring** - Track all prompts and responses
✅ **Tool Execution Logging** - Record tool calls and results
✅ **Performance Metrics** - Execution times for each component
✅ **Error Tracking** - Capture and log all errors with context
✅ **Structured Logging** - JSONL format for easy parsing and analysis
✅ **Audit Trail** - Complete execution history for compliance

## Architecture

```
monitoring/
├── __init__.py              # Module exports
├── callback_logger.py       # Main callback handler
├── log_analyzer.py          # Log analysis utility
└── README.md               # This file

logs/                        # Auto-created
├── agent_workflow.log      # Human-readable log
├── workflow_execution.jsonl # Structured event log
└── execution_report.txt    # Analysis report
```

## Usage

### 1. Automatic Integration

The monitoring system is automatically integrated into the workflow. Simply use the system normally and logs will be generated.

### 2. Viewing Logs

**Real-time logs:**
```bash
tail -f logs/agent_workflow.log
```

**Structured event logs:**
```bash
cat logs/workflow_execution.jsonl | jq .
```

### 3. Analyzing Logs

```python
from monitoring.log_analyzer import analyze_logs

# Analyze most recent execution
analyze_logs("workflow_execution.jsonl")
```

Or run directly:
```bash
cd monitoring
python log_analyzer.py
```

### 4. Custom Callback Implementation

To add callbacks to new agents:

```python
from monitoring import get_callback_logger

# Get logger instance
logger = get_callback_logger()

# For LlmAgent
agent = LlmAgent(
    name="my_agent",
    model="gemini-2.0-flash",
    # Add callbacks
    before_agent_callback=logger.before_agent_callback,
    after_agent_callback=logger.after_agent_callback,
    before_model_callback=logger.before_model_callback,
    after_model_callback=logger.after_model_callback,
    before_tool_callback=logger.before_tool_callback,
    after_tool_callback=logger.after_tool_callback
)
```

## Log Event Types

| Event Type | Description |
|------------|-------------|
| `agent_start` | Agent begins execution |
| `agent_complete` | Agent finishes execution |
| `llm_call` | LLM request initiated |
| `llm_response` | LLM response received |
| `tool_call` | Tool execution starts |
| `tool_result` | Tool execution completes |
| `execution_summary` | Workflow summary generated |

## Example Log Entry

```json
{
  "timestamp": "2025-11-18T10:30:45.123456",
  "execution_id": "abc-123-def-456",
  "event_type": "agent_start",
  "details": {
    "agent_name": "skills_matcher_agent",
    "invocation_id": "inv-001",
    "call_count": 1,
    "session_state_keys": ["job_data", "profile_data"]
  }
}
```

## Metrics Tracked

- **Execution Time**: Total and per-agent timing
- **Agent Calls**: Number of times each agent is invoked
- **LLM Calls**: API calls made per agent
- **Tool Calls**: External tool usage
- **State Changes**: Session state modifications
- **Errors**: Failures and warnings with context

## Benefits

1. **Debugging**: Detailed traces help identify issues
2. **Performance**: Identify bottlenecks and optimize
3. **Monitoring**: Real-time visibility into workflow execution
4. **Analytics**: Post-execution analysis and reporting
5. **Audit**: Complete record for compliance
6. **Cost**: Track LLM API usage for budgeting

## Configuration

Logs are stored in `./logs/` directory by default. To change:

```python
from pathlib import Path
from monitoring import WorkflowCallbackLogger

# Custom log location
logger = WorkflowCallbackLogger(log_file="custom_logs.jsonl")
```

## Integration with External Tools

The JSONL format can be ingested by:

- **Elasticsearch**: For searchable log aggregation
- **Grafana**: For visualization dashboards
- **Datadog**: For monitoring and alerting
- **Custom Analytics**: Parse with Python/pandas

Example parsing:

```python
import json
import pandas as pd

# Load into DataFrame
with open('logs/workflow_execution.jsonl') as f:
    events = [json.loads(line) for line in f]

df = pd.DataFrame(events)
print(df.groupby('event_type').size())
```

## Best Practices

1. ✅ Review logs after each workflow run
2. ✅ Archive old logs periodically
3. ✅ Set up alerts for error events
4. ✅ Use log analysis for optimization
5. ✅ Include execution_id in bug reports

## Troubleshooting

**No logs generated?**
- Check that `./logs/` directory exists and is writable
- Verify callbacks are registered on agents

**Large log files?**
- Implement log rotation
- Archive old logs
- Compress JSONL files

**Missing events?**
- Ensure all agents have callbacks registered
- Check for exceptions during callback execution

## Support

For issues or questions:
1. Check the log files for error messages
2. Review callback registration in agent code
3. Verify ADK version compatibility
