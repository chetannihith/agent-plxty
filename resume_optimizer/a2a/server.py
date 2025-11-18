"""
A2A Protocol HTTP Server
FastAPI implementation with JSON-RPC support
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional
import json
import time

from .agent_card import RESUME_OPTIMIZER_AGENT_CARD
from .messages import JSONRPCRequest, JSONRPCResponse
from .jsonrpc_handler import A2AJSONRPCHandler


app = FastAPI(
    title="Resume Optimizer A2A Agent",
    description="A2A-compliant AI agent for resume optimization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handler (workflow will be set later)
jsonrpc_handler = A2AJSONRPCHandler()


@app.on_event("startup")
async def startup_event():
    """Initialize workflow on startup"""
    try:
        # Import here to avoid circular dependencies
        from ..workflow.orchestrator import ResumeOptimizerWorkflow
        workflow = ResumeOptimizerWorkflow()
        jsonrpc_handler.set_workflow(workflow)
        print(" Server started with workflow integration")
    except Exception as e:
        print(f" Warning: Could not initialize workflow: {e}")
        print(" Server will run with demo responses")


@app.get("/")
async def root():
    """Root endpoint with agent info"""
    return {
        "agent": RESUME_OPTIMIZER_AGENT_CARD.name,
        "version": RESUME_OPTIMIZER_AGENT_CARD.version,
        "description": RESUME_OPTIMIZER_AGENT_CARD.description,
        "agent_card": "/.well-known/agent-card.json",
        "endpoints": RESUME_OPTIMIZER_AGENT_CARD.endpoints,
        "documentation": "/docs"
    }


@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    """
    Agent Card Discovery Endpoint
    REQUIRED by A2A Protocol
    """
    return RESUME_OPTIMIZER_AGENT_CARD.dict()


@app.post("/v1/message:send")
async def send_message(request: Request):
    """
    JSON-RPC 2.0 Endpoint
    Main communication endpoint for A2A
    """
    start_time = time.time()
    
    try:
        body = await request.json()
        
        # Parse JSON-RPC request
        rpc_request = JSONRPCRequest(**body)
        
        # Handle request
        response = await jsonrpc_handler.handle_request(rpc_request)
        
        # Add timing info if result exists
        if response.result and isinstance(response.result, dict):
            response.result.setdefault("metadata", {})
            response.result["metadata"]["execution_time_ms"] = int((time.time() - start_time) * 1000)
        
        return JSONResponse(content=response.dict())
        
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error: Invalid JSON"
                },
                "id": None
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": None
            }
        )


@app.post("/v1/message:send/stream")
async def send_message_stream(request: Request):
    """
    Streaming JSON-RPC Endpoint
    Uses Server-Sent Events (SSE) for streaming responses
    """
    try:
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)
        
        async def event_generator():
            """Generate SSE events"""
            # Start event
            yield f"data: {json.dumps({'status': 'started', 'method': rpc_request.method})}\n\n"
            
            # Progress updates (placeholder - implement actual progress tracking)
            for progress in [25, 50, 75]:
                yield f"data: {json.dumps({'status': 'in_progress', 'progress': progress})}\n\n"
            
            # Execute and get result
            response = await jsonrpc_handler.handle_request(rpc_request)
            
            # Send final result
            if response.error:
                yield f"data: {json.dumps({'status': 'error', 'error': response.error.dict()})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'completed', 'result': response.result})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/v1/tasks/{task_id}")
async def get_task(task_id: str):
    """
    Get Task Status
    A2A Protocol task management
    """
    rpc_request = JSONRPCRequest(
        method="tasks/get",
        params={"task_id": task_id},
        id=f"req-{task_id}"
    )
    
    response = await jsonrpc_handler.handle_request(rpc_request)
    
    if response.error:
        raise HTTPException(
            status_code=404 if response.error.code == -32001 else 500,
            detail=response.error.message
        )
    
    return response.result


@app.post("/v1/tasks")
async def create_task(request: Request):
    """
    Create Task
    A2A Protocol async task creation
    """
    try:
        body = await request.json()
        
        rpc_request = JSONRPCRequest(
            method="tasks/create",
            params=body,
            id=f"req-create-{time.time()}"
        )
        
        response = await jsonrpc_handler.handle_request(rpc_request)
        
        if response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return response.result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List Tasks
    A2A Protocol task management
    """
    rpc_request = JSONRPCRequest(
        method="tasks/list",
        params={
            "status": status,
            "limit": limit,
            "offset": offset
        },
        id="req-list-tasks"
    )
    
    response = await jsonrpc_handler.handle_request(rpc_request)
    return response.result


@app.delete("/v1/tasks/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel Task
    A2A Protocol task cancellation
    """
    rpc_request = JSONRPCRequest(
        method="tasks/cancel",
        params={"task_id": task_id},
        id=f"req-cancel-{task_id}"
    )
    
    response = await jsonrpc_handler.handle_request(rpc_request)
    
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    
    return response.result


@app.get("/v1/skills")
async def list_skills():
    """
    List Agent Skills
    Returns all available skills/capabilities
    """
    rpc_request = JSONRPCRequest(
        method="skills/list",
        params={},
        id="req-list-skills"
    )
    
    response = await jsonrpc_handler.handle_request(rpc_request)
    return response.result


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_id": RESUME_OPTIMIZER_AGENT_CARD.id,
        "version": RESUME_OPTIMIZER_AGENT_CARD.version,
        "workflow_initialized": jsonrpc_handler.workflow is not None,
        "tasks_count": len(jsonrpc_handler.tasks)
    }


@app.get("/v1/agent/info")
async def agent_info():
    """Get detailed agent information"""
    rpc_request = JSONRPCRequest(
        method="agent/info",
        params={},
        id="req-agent-info"
    )
    
    response = await jsonrpc_handler.handle_request(rpc_request)
    return response.result


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the A2A server"""
    print(f"\nStarting Resume Optimizer A2A Agent Server on {host}:{port}")
    print(f"Agent Card: http://{host}:{port}/.well-known/agent-card.json")
    print(f"JSON-RPC: http://{host}:{port}/v1/message:send")
    print(f"Documentation: http://{host}:{port}/docs")
    print(f"Health: http://{host}:{port}/health\n")
    
    uvicorn.run(
        "resume_optimizer.a2a.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
