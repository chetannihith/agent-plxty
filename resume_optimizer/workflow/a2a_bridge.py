"""
Agent-to-Agent (A2A) Protocol Bridge

Wraps CrewAI agents for seamless integration with Google ADK workflow
"""
from typing import Dict, Any
from pydantic import BaseModel


class A2AEnvelope(BaseModel):
    """
    Agent-to-Agent communication envelope
    
    Standardizes communication between different agent frameworks
    """
    source_framework: str  # "google_adk" or "crewai"
    target_framework: str  # "google_adk" or "crewai"
    agent_name: str
    agent_role: str
    request: Dict[str, Any]
    response: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class A2ABridge:
    """
    Bridge between CrewAI and Google ADK
    
    Enables CrewAI agents to participate in Google ADK workflows
    """
    
    @staticmethod
    def wrap_crewai_output(
        agent_name: str,
        agent_role: str,
        crew_output: Any,
        request_data: Dict[str, Any]
    ) -> A2AEnvelope:
        """
        Wrap CrewAI output in A2A envelope
        
        Args:
            agent_name: Name of CrewAI agent
            agent_role: Role description
            crew_output: Output from CrewAI Crew.kickoff()
            request_data: Original request sent to CrewAI
        
        Returns:
            A2AEnvelope with standardized format
        """
        
        # Parse CrewAI output (typically string)
        if hasattr(crew_output, 'raw_output'):
            output_str = crew_output.raw_output
        else:
            output_str = str(crew_output)
        
        # Try to parse as JSON if possible
        import json
        try:
            response_data = json.loads(output_str)
        except:
            response_data = {"raw_output": output_str}
        
        envelope = A2AEnvelope(
            source_framework="crewai",
            target_framework="google_adk",
            agent_name=agent_name,
            agent_role=agent_role,
            request=request_data,
            response=response_data,
            metadata={
                "protocol_version": "1.0",
                "timestamp": None,  # Add timestamp if needed
                "framework_versions": {
                    "crewai": "latest",
                    "google_adk": "1.4.1"
                }
            }
        )
        
        return envelope
    
    @staticmethod
    def unwrap_for_google_adk(envelope: A2AEnvelope) -> Dict[str, Any]:
        """
        Extract response data for Google ADK context
        
        Args:
            envelope: A2A envelope from CrewAI
        
        Returns:
            Dict ready to store in ctx.session.state
        """
        return envelope.response
    
    @staticmethod
    def wrap_google_adk_request(
        agent_name: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare Google ADK data for CrewAI consumption
        
        Args:
            agent_name: Name of Google ADK agent
            request_data: Data from ctx.session.state
        
        Returns:
            Dict formatted for CrewAI input
        """
        
        envelope = A2AEnvelope(
            source_framework="google_adk",
            target_framework="crewai",
            agent_name=agent_name,
            agent_role="data_provider",
            request=request_data,
            metadata={
                "protocol_version": "1.0",
                "framework_versions": {
                    "google_adk": "1.4.1",
                    "crewai": "latest"
                }
            }
        )
        
        return envelope.dict()


# Example usage in workflow:
"""
# In orchestrator.py Stage 1:

from .a2a_bridge import A2ABridge, A2AEnvelope

# Prepare request
request_data = {"job_url": job_url}

# Call CrewAI agent
crew_output = self.job_extractor.extract_job_description(job_url)

# Wrap in A2A envelope
envelope = A2ABridge.wrap_crewai_output(
    agent_name="job_description_extractor",
    agent_role="web_scraper",
    crew_output=crew_output,
    request_data=request_data
)

# Store in Google ADK context
ctx.session.state["job_description"] = A2ABridge.unwrap_for_google_adk(envelope)
ctx.session.state["a2a_envelope_stage1"] = envelope.dict()  # For auditing
"""
