"""
Resume Optimizer - Multi-Agent System

10-agent resume optimization system with 6-stage pipeline
"""
from .agents import (
    JobDescriptionExtractorCrew,
    ProfileRAGAgent,
    create_skills_matcher_agent,
    create_experience_relevance_agent,
    create_content_alignment_agent,
    create_ats_optimizer_agent,
    create_keyword_enhancer_agent,
    create_markdown_formatter_agent,
    create_quality_validator_agent,
    FormattingCheckerAgent
)

from .workflow import (
    ResumeOptimizerWorkflow,
    A2ABridge,
    A2AEnvelope
)

from .tools import (
    WebScraperTool,
    ATSScoringTool,
    KeywordExtractorToolEnhanced,
    ResumeParserTool,
    MCPToolRequest,
    MCPToolResponse
)

__version__ = "1.0.0"

__all__ = [
    # Agents
    "JobDescriptionExtractorCrew",
    "ProfileRAGAgent",
    "create_skills_matcher_agent",
    "create_experience_relevance_agent",
    "create_content_alignment_agent",
    "create_ats_optimizer_agent",
    "create_keyword_enhancer_agent",
    "create_markdown_formatter_agent",
    "create_quality_validator_agent",
    "FormattingCheckerAgent",
    
    # Workflow
    "ResumeOptimizerWorkflow",
    "A2ABridge",
    "A2AEnvelope",
    
    # Tools
    "WebScraperTool",
    "ATSScoringTool",
    "KeywordExtractorToolEnhanced",
    "ResumeParserTool",
    "MCPToolRequest",
    "MCPToolResponse",
]
