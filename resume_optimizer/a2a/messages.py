"""
A2A Protocol Message Structures
Compliant with official specification
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class ContentPartType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImagePart(BaseModel):
    type: Literal["image"] = "image"
    url: str
    mimeType: Optional[str] = None


class FilePart(BaseModel):
    type: Literal["file"] = "file"
    url: str
    mimeType: str
    filename: Optional[str] = None


class ToolCallPart(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResultPart(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    id: str  # References tool_call id
    result: Any
    error: Optional[str] = None


ContentPart = Union[TextPart, ImagePart, FilePart, ToolCallPart, ToolResultPart]


class A2AMessage(BaseModel):
    """
    A2A Protocol Message Format
    Used in JSON-RPC message/send calls
    """
    role: MessageRole
    author: str = Field(..., description="Agent ID or user identifier")
    parts: List[ContentPart] = Field(..., description="Message content parts")
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class A2ATask(BaseModel):
    """
    A2A Protocol Task
    Used for async task management
    """
    id: str
    status: TaskStatus
    skill_id: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# JSON-RPC 2.0 Models

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request"""
    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Union[str, int]


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 Error"""
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response"""
    jsonrpc: Literal["2.0"] = "2.0"
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    id: Union[str, int, None]


# JSON-RPC Error Codes (from spec)
class JSONRPCErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # A2A-specific errors
    TASK_NOT_FOUND = -32001
    SKILL_NOT_FOUND = -32002
    AUTHENTICATION_FAILED = -32003
    INSUFFICIENT_PERMISSIONS = -32004
    RATE_LIMIT_EXCEEDED = -32005
