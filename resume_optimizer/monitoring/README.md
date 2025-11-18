# Simple Callback-Based Logging System

A lightweight logging system for the Resume Optimizer multi-agent workflow that records all agent activities to timestamped log files.

## Features

✅ **Event-Based Logging**: Records workflow start/end, agent start/end, state updates, errors
✅ **Timestamped Files**: Auto-generates files like `logs/workflow_20251118_143052.log`
✅ **Console + File Output**: Logs to both terminal and file simultaneously
✅ **Stage Transitions**: Clear visual markers for pipeline stages
✅ **Error Tracking**: Captures and logs all exceptions with context
✅ **Streamlit Integration**: View logs directly in the web UI

## Log File Structure

```
logs/
└── workflow_20251118_143052.log  # Timestamped log files
```

## Usage

### In Workflow Orchestrator

The logging is **automatically integrated** into `orchestrator.py`:

```python
from resume_optimizer.monitoring.callbacks import (
    log_workflow_start,
    log_workflow_end,
    log_agent_start,
    log_agent_end,
    log_agent_error,
    log_state_update,
    log_stage_transition,
    log_custom,
    get_current_log_file
)

# Workflow logs automatically on:
# - Workflow start/end
# - Each agent start/end with timing
# - State updates
# - Stage transitions
# - Errors
```

### In Streamlit App

Logs are viewable in the UI:

```python
# After workflow completes
with st.expander("📋 View Logs"):
    st.info(f"Logs saved to: `{get_current_log_file()}`")
    
    with open(get_current_log_file(), 'r') as f:
        log_content = f.read()
    st.text_area("Log Output", value=log_content, height=300)
```

## Log Format

### Workflow Start
```
2025-11-18 14:30:52 | INFO | ================================================================================
2025-11-18 14:30:52 | INFO | WORKFLOW STARTED: ResumeOptimizer
2025-11-18 14:30:52 | INFO |   job_url: https://linkedin.com/jobs/view/123
2025-11-18 14:30:52 | INFO |   resume_path: ./data/uploads/resume.pdf
2025-11-18 14:30:52 | INFO |   model: gemini-2.0-flash-exp
2025-11-18 14:30:52 | INFO | ================================================================================
```

### Stage Transition
```
2025-11-18 14:30:52 | INFO | 
2025-11-18 14:30:52 | INFO | ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-11-18 14:30:52 | INFO | STAGE TRANSITION: START → Stage 1: Job Extraction
2025-11-18 14:30:52 | INFO | ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Agent Execution
```
2025-11-18 14:30:52 | INFO | 
2025-11-18 14:30:52 | INFO | ────────────────────────────────────────────────────────────
2025-11-18 14:30:52 | INFO | AGENT START: job_description_extractor (Stage 1)
2025-11-18 14:30:55 | INFO | AGENT COMPLETE: job_description_extractor
2025-11-18 14:30:55 | INFO |   Execution Time: 2.34s
2025-11-18 14:30:55 | INFO |   job_title: Software Engineer
2025-11-18 14:30:55 | INFO |   company: Google
2025-11-18 14:30:55 | INFO |   skills_count: 15
2025-11-18 14:30:55 | INFO | ────────────────────────────────────────────────────────────
```

### State Updates
```
2025-11-18 14:30:55 | INFO |   📦 STATE UPDATE: job_description_extractor
2025-11-18 14:30:55 | INFO |     Updated keys: ['job_description']
```

### Workflow End
```
2025-11-18 14:31:12 | INFO | ================================================================================
2025-11-18 14:31:12 | INFO | WORKFLOW COMPLETED: ResumeOptimizer
2025-11-18 14:31:12 | INFO |   status: SUCCESS
2025-11-18 14:31:12 | INFO |   ats_score: 87
2025-11-18 14:31:12 | INFO |   quality_score: 92
2025-11-18 14:31:12 | INFO |   validation_status: PASSED
2025-11-18 14:31:12 | INFO | ================================================================================
```

## Available Callback Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `log_workflow_start()` | Logs workflow initialization | Start of pipeline execution |
| `log_workflow_end()` | Logs workflow completion | End with success/failure status |
| `log_agent_start()` | Logs agent execution start | Agent begins processing |
| `log_agent_end()` | Logs agent completion with timing | Agent finishes with duration |
| `log_agent_error()` | Logs agent errors | Exception handling |
| `log_tool_call()` | Logs tool invocations | Tool execution tracking |
| `log_tool_result()` | Logs tool results | Tool output capture |
| `log_state_update()` | Logs session state changes | State modification tracking |
| `log_event()` | Logs generic events | Custom event logging |
| `log_stage_transition()` | Logs pipeline stage changes | Visual stage markers |
| `log_custom()` | Logs custom messages | Ad-hoc logging |
| `get_current_log_file()` | Returns current log file path | UI display |

## Custom Logging

Add custom log messages anywhere:

```python
from resume_optimizer.monitoring.callbacks import log_custom, log_event

# Simple message
log_custom("Processing completed", level="INFO")

# With additional context
log_custom("Agent initialized", level="INFO", agent_name="profile_rag", model="gemini-2.0")

# Structured event
log_event(
    "custom_metric",
    "Resume quality calculated",
    score=92.5,
    criteria="ATS compliance"
)
```

## Log Levels

- **INFO**: Normal operational messages (default)
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **DEBUG**: Debugging information

Example:
```python
log_custom("This is a warning", level="WARNING")
log_custom("This is an error", level="ERROR")
```

## Benefits

✅ **Zero Complexity**: Just callbacks, no configuration needed
✅ **Complete Audit Trail**: Every action is logged with timestamps
✅ **Easy Debugging**: Trace execution flow and find issues quickly
✅ **Performance Tracking**: See execution times for each agent
✅ **Streamlit Integration**: View logs in the web interface
✅ **No External Dependencies**: Uses Python's built-in logging

## File Management

Logs accumulate in the `logs/` directory. To manage:

```bash
# View latest log
tail -f logs/workflow_*.log

# List all logs
ls -lh logs/

# Clean old logs (keep last 10)
ls -t logs/workflow_*.log | tail -n +11 | xargs rm
```

## Implementation Details

### Log File Creation
- Created automatically in `logs/` directory
- Filename format: `workflow_YYYYMMDD_HHMMSS.log`
- New file per import (session)

### Console + File Output
- Logs written to both console and file simultaneously
- Format: `TIMESTAMP | LEVEL | MESSAGE`
- UTF-8 encoding for special characters

### Thread Safety
- Python's logging module is thread-safe
- Safe for parallel agent execution
- No race conditions in file writing

## Troubleshooting

### Logs Not Appearing
```python
# Check log file path
from resume_optimizer.monitoring.callbacks import get_current_log_file
print(get_current_log_file())
```

### Permission Errors
```bash
# Ensure logs directory is writable
chmod 755 logs/
```

### Large Log Files
```python
# Logs can grow large - implement rotation if needed
# Currently: ~50KB per workflow execution
```

## Comparison with ADK Callbacks

This system is **simpler** than the full ADK callback system:

| Feature | This System | Full ADK Callbacks |
|---------|-------------|-------------------|
| Setup | Zero config | Callback registration required |
| LLM Tracking | No | Yes (prompts/responses) |
| Tool Tracking | No | Yes (tool calls/results) |
| Analysis | No | Yes (metrics/statistics) |
| File Size | Small | Larger (JSONL) |
| Complexity | Low | Medium |

**Use this system when**: You want simple event logging without complexity
**Use ADK callbacks when**: You need detailed LLM/tool tracking and analysis

## Next Steps

1. **Run the workflow**: Logs are created automatically
2. **View in Streamlit**: Check the "📋 View Logs" expander
3. **Analyze logs**: Review execution flow and timing
4. **Add custom events**: Use `log_custom()` for specific tracking needs

For questions or issues, check the logs directory and verify file permissions! 🚀
