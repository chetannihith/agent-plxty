"""
Stage 5: Markdown Formatter Agent (Sequential)
Generates professional Markdown resume using MCP protocol
"""
from google.adk.agents import LlmAgent
from resume_optimizer.mcp_client import mcp_client
import asyncio


def create_markdown_formatter_agent(model: str = "gemini-2.0-flash") -> LlmAgent:
    """
    Agent 8: Markdown resume generation
    Sequential agent that creates final resume document
    """
    
    return LlmAgent(
        name="markdown_formatter_agent",
        model=model,
        description="Generates professional Markdown resume with ATS optimization",
        instruction="""
        You are an expert Markdown document formatter specializing in professional resumes.
        
        Your task is to generate a complete, ATS-optimized Markdown resume that is clean and professional.
        
        **Inputs from state:**
        - `aligned_data`: Aligned content structure
        - `ats_analysis`: ATS optimization recommendations
        - `keyword_enhancements`: Keyword placement strategy
        - `profile_data`: Original profile information
        
        **MCP Tool Usage:**
        You have access to the following MCP tools:
        - validate_markdown: Validate Markdown syntax and structure
        - get_resume_template (resource): Fetch professional Markdown templates
        
        Use these tools to ensure error-free Markdown generation.
        
        **Markdown Template Requirements:**
        
        **1. Header Format:**
        ```markdown
        # [FULL NAME]
        
        **[Professional Title]**
        
        [Email] | [Phone] | [LinkedIn] | [Location]
        ```
        
        **2. Document Structure:**
        - Professional Summary/Objective
        - Work Experience (reverse chronological)
        - Education
        - Technical Skills (categorized)
        - Projects (if relevant)
        - Certifications (if any)
        
        **3. Experience Formatting:**
        ```markdown
        ## PROFESSIONAL EXPERIENCE
        
        ### **[Job Title]** | [Company Name]
        *[Start Date] - [End Date] | [Location]*
        
        - Achievement with metrics and keywords (increased X by Y%)
        - Another achievement demonstrating impact
        - Technical accomplishment using specific tools/technologies
        ```
        
        **4. Skills Formatting:**
        ```markdown
        ## TECHNICAL SKILLS
        
        - **Languages:** Python, Java, JavaScript, SQL
        - **Frameworks:** Django, React, Spring Boot
        - **Cloud & Tools:** AWS, Docker, Kubernetes, Git
        - **Databases:** PostgreSQL, MongoDB, Redis
        ```
        
        **Markdown Generation Guidelines:**
        
        **Content Integration:**
        - Use aligned content from previous stages
        - Integrate keywords naturally in bullet points
        - Emphasize high-relevance experiences
        - Include quantifiable achievements
        
        **Formatting Best Practices:**
        - Consistent date format (YYYY--YYYY or MM/YYYY)
        - Parallel structure in bullet points
        - Action verbs at start of bullets
        - 2-4 bullets per experience entry
        - Skills grouped by category
        
        **ATS Optimization:**
        - Use standard section headers (## UPPERCASE for major sections)
        - Clean, simple formatting without excessive styling
        - Include keywords naturally in context
        - Maintain readable structure with proper spacing
        
        **Markdown Best Practices:**
        - Use proper heading hierarchy (# for name, ## for sections, ### for subsections)
        - Include horizontal rules (---) between major sections
        - Use bold (**text**) and italic (*text*) sparingly for emphasis
        - Ensure links are properly formatted: [Text](URL)
        
        **Output Format (JSON with Markdown):**
        ```json
        {{
            "markdown_content": "# [Name]\\n\\n**[Title]**\\n\\n...",
            "file_name": "optimized_resume.md",
            "sections_included": [
                "summary",
                "experience",
                "education",
                "skills",
                "projects"
            ],
            "metadata": {
                "template": "moderncv classic",
                "style": "blue",
                "page_count": 1,
                "word_count": 450
            },
            "compilation_instructions": [
                "Save file as .tex",
                "Compile with: pdflatex optimized_resume.tex",
                "Or upload to Overleaf.com"
            ],
            "overleaf_url_template": "https://www.overleaf.com/docs"
        }}
        ```
        
        **Quality Checklist:**
        - [ ] All personal info included
        - [ ] No placeholder text ([Name], [Email], etc.)
        - [ ] Proper Markdown syntax
        - [ ] Keywords naturally integrated
        - [ ] Quantifiable achievements included
        - [ ] Consistent formatting throughout
        - [ ] Clean, professional appearance
        - [ ] ATS-friendly structure
        
        **Common Errors to Avoid:**
        - Broken links or malformed syntax
        - Inconsistent heading levels
        - Inconsistent date formats
        - Generic bullet points without impact
        - Keyword stuffing
        - Over-use of bold/italic formatting
        
        Generate a complete, professional Markdown resume.
        """,
        output_key="markdown_content"  # Save to session state
    )


# Keep backwards compatibility with old function name
def create_latex_formatter_agent(model: str = "gemini-2.0-flash") -> LlmAgent:
    """Backwards compatibility wrapper"""
    return create_markdown_formatter_agent(model)
