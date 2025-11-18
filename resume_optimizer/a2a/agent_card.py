"""
Agent Card Implementation
Compliant with A2A Protocol Specification
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class TransportType(str, Enum):
    JSONRPC = "jsonrpc"
    GRPC = "grpc"
    HTTP_JSON = "http+json"


class SecurityScheme(BaseModel):
    type: str  # "bearer", "apiKey", "oauth2"
    scheme: Optional[str] = None
    bearerFormat: Optional[str] = None


class SkillInputOutput(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str] = []


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    inputSchema: SkillInputOutput
    outputSchema: SkillInputOutput
    examples: List[Dict[str, Any]] = []


class AgentCard(BaseModel):
    """
    A2A Protocol Agent Card
    Published at /.well-known/agent-card.json
    """
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent purpose and capabilities")
    version: str = Field(default="1.0.0", description="Agent version")
    url: str = Field(..., description="Base URL for agent endpoints")
    
    # Transport configuration
    preferredTransport: TransportType = TransportType.JSONRPC
    supportedTransports: List[TransportType] = [TransportType.JSONRPC]
    
    # Capabilities
    skills: List[AgentSkill] = Field(..., description="Agent skills/capabilities")
    
    # Security
    securitySchemes: Dict[str, SecurityScheme] = {}
    
    # Metadata
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    tags: List[str] = []
    
    # Service endpoints
    endpoints: Dict[str, str] = Field(
        default_factory=lambda: {
            "message": "/v1/message:send",
            "tasks": "/v1/tasks",
            "health": "/health"
        }
    )


# Define Resume Optimizer Agent Card
RESUME_OPTIMIZER_AGENT_CARD = AgentCard(
    id="resume-optimizer-agent",
    name="Resume Optimizer Agent",
    description="AI-powered multi-agent system that optimizes resumes for ATS compatibility and job descriptions using MCP tools and Google ADK agents",
    version="1.0.0",
    url="http://localhost:8000",  # Update for production
    preferredTransport=TransportType.JSONRPC,
    supportedTransports=[TransportType.JSONRPC, TransportType.HTTP_JSON],
    skills=[
        AgentSkill(
            id="optimize-resume",
            name="Optimize Resume",
            description="Optimize resume for a specific job description with ATS scoring, keyword enhancement, and Markdown formatting",
            inputSchema=SkillInputOutput(
                type="object",
                properties={
                    "resume_content": {
                        "type": "string",
                        "description": "Resume text or file content"
                    },
                    "job_description": {
                        "type": "string",
                        "description": "Target job description"
                    },
                    "job_url": {
                        "type": "string",
                        "description": "URL to job posting (optional)",
                        "format": "uri"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format (markdown, pdf, docx)",
                        "enum": ["markdown", "pdf", "docx"],
                        "default": "markdown"
                    }
                },
                required=["resume_content", "job_description"]
            ),
            outputSchema=SkillInputOutput(
                type="object",
                properties={
                    "optimized_resume": {
                        "type": "string",
                        "description": "Optimized resume in Markdown format"
                    },
                    "ats_score": {
                        "type": "number",
                        "description": "ATS compatibility score (0-100)"
                    },
                    "quality_score": {
                        "type": "number",
                        "description": "Overall quality score (0-100)"
                    },
                    "keyword_analysis": {
                        "type": "object",
                        "description": "Keyword extraction results"
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optimization recommendations"
                    },
                    "changes_made": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of changes applied"
                    }
                },
                required=["optimized_resume", "ats_score"]
            ),
            examples=[
                {
                    "input": {
                        "resume_content": "John Doe\nSoftware Engineer with 5 years experience in web development...",
                        "job_description": "Looking for Senior Python Developer with AWS experience..."
                    },
                    "output": {
                        "optimized_resume": "# John Doe\n## Senior Python Developer\n\n### Professional Summary\nSoftware Engineer specializing in Python development...",
                        "ats_score": 87,
                        "quality_score": 92,
                        "recommendations": [
                            "Added AWS and Python keywords",
                            "Restructured experience section for ATS"
                        ]
                    }
                }
            ]
        ),
        AgentSkill(
            id="extract-job-description",
            name="Extract Job Description",
            description="Extract structured job information from URL or text using web scraping and NLP",
            inputSchema=SkillInputOutput(
                type="object",
                properties={
                    "job_url": {
                        "type": "string",
                        "description": "URL to job posting",
                        "format": "uri"
                    },
                    "job_text": {
                        "type": "string",
                        "description": "Job description text (alternative to URL)"
                    }
                },
                required=[]
            ),
            outputSchema=SkillInputOutput(
                type="object",
                properties={
                    "job_title": {"type": "string"},
                    "company": {"type": "string"},
                    "location": {"type": "string"},
                    "required_skills": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "preferred_skills": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "experience_level": {"type": "string"},
                    "full_description": {"type": "string"}
                },
                required=["job_title", "required_skills"]
            ),
            examples=[
                {
                    "input": {
                        "job_url": "https://example.com/job/12345"
                    },
                    "output": {
                        "job_title": "Senior Python Developer",
                        "company": "Tech Corp",
                        "required_skills": ["Python", "AWS", "Docker", "REST APIs"],
                        "keywords": ["backend", "microservices", "cloud"]
                    }
                }
            ]
        ),
        AgentSkill(
            id="calculate-ats-score",
            name="Calculate ATS Score",
            description="Calculate ATS compatibility score for resume-job pair using MCP tools",
            inputSchema=SkillInputOutput(
                type="object",
                properties={
                    "resume_text": {
                        "type": "string",
                        "description": "Resume content"
                    },
                    "job_description": {
                        "type": "string",
                        "description": "Job description"
                    }
                },
                required=["resume_text", "job_description"]
            ),
            outputSchema=SkillInputOutput(
                type="object",
                properties={
                    "total_score": {
                        "type": "number",
                        "description": "Overall ATS score (0-100)"
                    },
                    "keyword_score": {
                        "type": "number",
                        "description": "Keyword match score"
                    },
                    "skills_score": {
                        "type": "number",
                        "description": "Skills match score"
                    },
                    "experience_score": {
                        "type": "number",
                        "description": "Experience relevance score"
                    },
                    "format_score": {
                        "type": "number",
                        "description": "Formatting quality score"
                    },
                    "missing_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords from job not found in resume"
                    },
                    "matched_skills": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                required=["total_score"]
            ),
            examples=[
                {
                    "input": {
                        "resume_text": "Python developer with AWS experience...",
                        "job_description": "Looking for Python developer..."
                    },
                    "output": {
                        "total_score": 87,
                        "keyword_score": 35,
                        "skills_score": 28,
                        "experience_score": 24
                    }
                }
            ]
        )
    ],
    securitySchemes={
        "bearerAuth": SecurityScheme(
            type="http",
            scheme="bearer",
            bearerFormat="JWT"
        )
    },
    author="Resume Optimizer Team",
    license="MIT",
    tags=["resume", "ats", "optimization", "career", "job-search", "ai-agent"]
)
