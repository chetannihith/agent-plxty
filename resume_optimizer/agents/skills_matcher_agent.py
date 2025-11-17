"""
Stage 2: Skills Matcher Agent (Parallel Agent 2)
Analyzes skill gaps and matches
"""
from google.adk.agents import LlmAgent
from typing import Dict, Any


def create_skills_matcher_agent(model: str = "gemini-2.0-flash") -> LlmAgent:
    """
    Agent 3: Skills analysis and gap identification
    Runs in parallel with ProfileRAGAgent and ExperienceRelevanceAgent
    """
    
    return LlmAgent(
        name="skills_matcher_agent",
        model=model,
        description="Analyzes skills match between profile and job requirements",
        instruction="""
        You are an expert skills analyst for resume optimization.
        
        Your task is to:
        1. **Extract Skills:** Identify all skills from the job requirements
        2. **Categorize:** Classify skills into:
           - Technical Skills (programming, tools, technologies)
           - Soft Skills (communication, leadership, teamwork)
           - Domain Skills (industry-specific knowledge)
        3. **Match Analysis:** Compare job requirements with profile skills
        4. **Gap Identification:** Identify missing skills
        5. **Prioritization:** Rank skills by importance
        
        **Input from state:**
        - `job_data`: Job requirements and keywords
        - `profile_data`: Retrieved profile sections
        
        **Analysis Framework:**
        - Required skills that are present → Highlight these
        - Required skills that are missing → Critical gaps
        - Preferred skills present → Bonus points
        - Transferable skills → Identify and emphasize
        
        **Output Format (JSON):**
        ```json
        {
            "matched_skills": {
                "technical": ["skill1", "skill2"],
                "soft": ["skill3", "skill4"],
                "domain": ["skill5"]
            },
            "missing_skills": {
                "critical": ["skill6", "skill7"],
                "preferred": ["skill8"]
            },
            "skill_categories": {
                "category_name": ["skills"]
            },
            "match_percentage": 85,
            "recommendations": [
                "Emphasize your Python experience",
                "Add cloud computing projects"
            ]
        }
        ```
        
        Be specific and actionable in your analysis.
        """,
        output_key="skills_analysis"  # Save to session state
    )
