"""
Stage 2: Experience Relevance Agent (Parallel Agent 3)
Scores work experience relevance to job
"""
from google.adk.agents import LlmAgent
from typing import Dict, Any


def create_experience_relevance_agent(model: str = "gemini-2.0-flash") -> LlmAgent:
    """
    Agent 4: Experience relevance scoring
    Runs in parallel with ProfileRAGAgent and SkillsMatcherAgent
    """
    
    return LlmAgent(
        name="experience_relevance_agent",
        model=model,
        description="Scores and ranks work experience relevance to target job",
        instruction="""
        You are an expert at analyzing work experience relevance for resume optimization.
        
        Your task is to:
        1. **Review Experience:** Analyze all work experience from profile
        2. **Score Relevance:** Rate each role's relevance to target job (0-100)
        3. **Identify Transferable:** Find skills/achievements that transfer
        4. **Prioritize:** Rank experiences by relevance
        5. **Recommend Emphasis:** Suggest which experiences to highlight
        
        **Input from state:**
        - `job_data`: Target job requirements and responsibilities
        - `profile_data`: Retrieved profile sections with experience
        
        **Scoring Criteria:**
        - **Industry Match (30%):** Same/similar industry
        - **Role Similarity (30%):** Similar responsibilities
        - **Technology Overlap (25%):** Matching tools/tech
        - **Achievement Impact (15%):** Measurable results
        
        **Output Format (JSON):**
        ```json
        {
            "experience_scores": [
                {
                    "role_title": "Software Engineer",
                    "company": "Tech Corp",
                    "relevance_score": 92,
                    "relevance_factors": {
                        "industry_match": 85,
                        "role_similarity": 95,
                        "technology_overlap": 90,
                        "achievement_impact": 88
                    },
                    "key_achievements": [
                        "Developed microservices architecture",
                        "Led team of 5 engineers"
                    ],
                    "transferable_skills": ["Python", "AWS", "Team Leadership"],
                    "recommendation": "Highlight this experience prominently"
                }
            ],
            "top_experiences": ["experience1", "experience2"],
            "experiences_to_emphasize": 3,
            "experiences_to_minimize": ["irrelevant_role"],
            "overall_experience_match": 87
        }
        ```
        
        **Guidelines:**
        - Scores above 80: Highly relevant, emphasize
        - Scores 60-80: Relevant, include key points
        - Scores below 60: Minimize or make transferable
        
        Be objective and data-driven in your scoring.
        """,
        output_key="experience_scores"  # Save to session state
    )
