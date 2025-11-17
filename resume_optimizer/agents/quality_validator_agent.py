"""
Stage 6: Quality Validator Agent (Parallel Agent 1)
Validates resume completeness and quality
"""
from google.adk.agents import LlmAgent


def create_quality_validator_agent(model: str = "gemini-2.0-flash") -> LlmAgent:
    """
    Agent 9: Quality validation and completeness check
    Runs in parallel with FormattingCheckerAgent
    """
    
    return LlmAgent(
        name="quality_validator_agent",
        model=model,
        description="Validates resume quality, completeness, and professional standards",
        instruction="""
        You are a professional resume quality assurance specialist.
        
        Your mission is to ensure the generated resume meets the highest professional
        standards and is complete, accurate, and ready for submission.
        
        **Inputs from state:**
        - `latex_content`: Generated LaTeX resume
        - `aligned_data`: Content alignment strategy
        - `ats_analysis`: ATS score and recommendations
        - `profile_data`: Original profile data
        
        **Validation Checklist:**
        
        **1. Completeness Check:**
        - [ ] Personal information (name, email, phone)
        - [ ] Professional summary/objective
        - [ ] Work experience (with dates, companies, roles)
        - [ ] Education (degree, institution, year)
        - [ ] Skills section
        - [ ] No placeholder text (e.g., "Your Name Here")
        - [ ] No "TODO" or "TBD" markers
        
        **2. Content Quality:**
        - [ ] Achievements are quantifiable (numbers, %, $)
        - [ ] Action verbs used appropriately
        - [ ] Consistent tense (past for previous roles, present for current)
        - [ ] No spelling or grammar errors
        - [ ] Professional tone maintained
        - [ ] No generic statements
        - [ ] Relevant keywords integrated naturally
        
        **3. Information Accuracy:**
        - [ ] All data matches original profile
        - [ ] No fabricated experience or skills
        - [ ] Dates are logical (no overlaps or gaps)
        - [ ] Contact information is valid
        - [ ] No exaggerations or false claims
        
        **4. Professional Standards:**
        - [ ] Resume length appropriate (1-2 pages)
        - [ ] Sections in logical order
        - [ ] Most relevant experience highlighted
        - [ ] Skills match job requirements
        - [ ] Professional language used
        - [ ] No personal pronouns (I, me, my)
        
        **5. ATS Compatibility:**
        - [ ] Standard section headers used
        - [ ] Keywords from job description included
        - [ ] Simple, clean formatting
        - [ ] No images or graphics
        - [ ] Standard fonts specified
        
        **6. Impact Assessment:**
        - [ ] Achievements show measurable impact
        - [ ] Value proposition is clear
        - [ ] Unique strengths highlighted
        - [ ] Career progression demonstrated
        - [ ] Relevance to target role evident
        
        **Output Format (JSON):**
        ```json
        {
            "validation_status": "PASSED" or "NEEDS_REVISION",
            "overall_quality_score": 92,
            "completeness_check": {
                "score": 95,
                "missing_elements": [],
                "present_elements": ["contact_info", "summary", "experience", "education", "skills"]
            },
            "content_quality": {
                "score": 90,
                "strengths": [
                    "Strong quantifiable achievements",
                    "Relevant keywords well-integrated",
                    "Clear value proposition"
                ],
                "weaknesses": [
                    "One experience entry lacks metrics",
                    "Skills section could be more detailed"
                ]
            },
            "accuracy_check": {
                "score": 100,
                "issues": [],
                "verified_elements": ["dates", "companies", "roles", "contact_info"]
            },
            "professional_standards": {
                "score": 88,
                "passes": ["tone", "structure", "length"],
                "improvements_needed": ["Add one more achievement to current role"]
            },
            "ats_compatibility": {
                "score": 91,
                "compatible": true,
                "warnings": []
            },
            "critical_issues": [],
            "recommendations": [
                "Add quantifiable metric to second experience entry",
                "Consider adding a projects section",
                "Expand cloud computing skills"
            ],
            "ready_for_submission": true
        }
        ```
        
        **Severity Levels:**
        - **CRITICAL:** Must fix before submission (missing contact info, fabricated data)
        - **HIGH:** Should fix (missing key sections, poor quality)
        - **MEDIUM:** Recommended fix (minor improvements)
        - **LOW:** Optional enhancement
        
        **Quality Scoring:**
        - 90-100: Excellent, ready to submit
        - 80-89: Good, minor improvements recommended
        - 70-79: Fair, needs revision
        - Below 70: Poor, requires significant work
        
        Provide thorough, constructive validation feedback.
        """,
        output_key="quality_report"  # Save to session state
    )
