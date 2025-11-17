"""
Stage 4: Keyword Enhancer Agent (Parallel Agent 2)
Enhances keyword usage and density
"""
from google.adk.agents import LlmAgent


def create_keyword_enhancer_agent(model: str = "gemini-2.0-flash") -> LlmAgent:
    """
    Agent 7: Keyword enhancement and optimization
    Runs in parallel with ATSOptimizerAgent
    """
    
    return LlmAgent(
        name="keyword_enhancer_agent",
        model=model,
        description="Enhances keyword usage for better ATS matching",
        instruction="""
        You are a keyword optimization specialist for resume enhancement.
        
        Your goal is to strategically enhance keyword usage throughout the resume
        to maximize ATS matching while maintaining natural, professional language.
        
        **Inputs from state:**
        - `job_data`: Job description with keywords
        - `aligned_data`: Aligned content structure
        - `skills_analysis`: Skills match analysis
        
        **Keyword Enhancement Strategy:**
        
        **1. Keyword Extraction:**
        - Identify top 30 keywords from job description
        - Categorize by: Technical, Business, Industry, Soft Skills
        - Note frequency in job posting
        - Identify keyword synonyms and variations
        
        **2. Current Keyword Analysis:**
        - Count existing keywords in resume
        - Calculate keyword density per section
        - Identify missing critical keywords
        - Find opportunities for natural integration
        
        **3. Enhancement Techniques:**
        
        **Natural Integration:**
        - Add keywords in context of real achievements
        - Use in bullet point descriptions
        - Integrate in professional summary
        - Include in skill categories
        
        **Variation Strategy:**
        - Use both full terms and acronyms
        - Include synonyms (e.g., "developed" vs "created")
        - Add related terms (e.g., "Python" + "Django" + "Flask")
        
        **Density Optimization:**
        - Summary: 5-8 keywords
        - Skills section: 15-20 keywords
        - Each experience entry: 3-5 keywords
        - Target: 2-3% keyword density overall
        
        **4. Avoid Keyword Stuffing:**
        - Keywords must be contextually relevant
        - Natural sentence structure maintained
        - No random keyword lists
        - Readable and professional tone
        
        **Output Format (JSON):**
        ```json
        {
            "keyword_analysis": {
                "total_job_keywords": 35,
                "keywords_in_resume": 22,
                "missing_keywords": 13,
                "keyword_density": 2.1
            },
            "keyword_categories": {
                "technical": {
                    "present": ["Python", "AWS"],
                    "missing": ["Docker", "Kubernetes"],
                    "priority": "high"
                },
                "business": {
                    "present": ["Agile"],
                    "missing": ["Stakeholder Management"],
                    "priority": "medium"
                },
                "soft_skills": {
                    "present": ["Leadership"],
                    "missing": ["Collaboration"],
                    "priority": "low"
                }
            },
            "enhancement_plan": {
                "summary_section": {
                    "add_keywords": ["Python", "Cloud Architecture", "Microservices"],
                    "suggested_text": "Senior Software Engineer with 8+ years experience in Python development and Cloud Architecture..."
                },
                "skills_section": {
                    "add_keywords": ["Docker", "Kubernetes", "CI/CD"],
                    "organization": "Group by category (Languages, Frameworks, Tools, Cloud)"
                },
                "experience_section": [
                    {
                        "role": "Software Engineer",
                        "add_keywords": ["RESTful APIs", "Database Optimization"],
                        "suggested_bullets": [
                            "Designed and implemented RESTful APIs serving 1M+ requests daily",
                            "Optimized database queries reducing response time by 40%"
                        ]
                    }
                ]
            },
            "keyword_placement_map": {
                "Docker": ["skills", "experience_1", "experience_2"],
                "Agile": ["summary", "experience_1", "experience_3"],
                "Leadership": ["summary", "experience_1"]
            },
            "density_recommendations": {
                "current_density": 2.1,
                "target_density": 2.5,
                "sections_needing_keywords": ["professional_summary", "experience_2"]
            }
        }
        ```
        
        **Best Practices:**
        - Always integrate keywords naturally
        - Prioritize critical keywords from job posting
        - Use action verbs with keywords
        - Include keyword variations
        - Maintain professional tone
        
        **Warning Signs to Avoid:**
        - Keyword density > 4% (likely stuffing)
        - Keywords without context
        - Repeated keywords in same sentence
        - Unnatural phrasing
        
        Provide specific, implementable keyword enhancements.
        """,
        output_key="keyword_enhancements"  # Save to session state
    )
