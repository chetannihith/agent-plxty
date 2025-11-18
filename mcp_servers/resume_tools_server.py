"""
MCP Server for Resume Optimization Tools
Implements Model Context Protocol (MCP) specification for tool discovery and execution.
"""
from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Any, Optional
import asyncio
import re
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from resume_optimizer.tools.mcp_tools import (
    ATSScoringTool,
    KeywordExtractorTool,
    ResumeParserTool
)

# Placeholder for MarkdownValidatorTool (to be implemented)
class MarkdownValidatorTool:
    def validate_markdown(self, markdown_content: str) -> Dict:
        """Validate Markdown content"""
        # Basic validation - check for common issues
        errors = []
        warnings = []
        suggestions = []
        
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for broken links
            if '[' in line and ']' in line and '(' in line and ')' in line:
                if line.count('[') != line.count(']') or line.count('(') != line.count(')'):
                    errors.append(f"Line {i}: Malformed link syntax")
            
            # Check for proper header formatting
            if line.startswith('#'):
                if not line.startswith('# ') and len(line) > 1:
                    warnings.append(f"Line {i}: Header should have space after #")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "line_numbers": [i+1 for i in range(len(lines))]
        }

# Initialize MCP Server
mcp = FastMCP("resume-optimizer-tools")


# ============================================
# TOOL 1: ATS Scoring
# ============================================
@mcp.tool()
async def calculate_ats_score(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:
    """
    Calculate ATS (Applicant Tracking System) compatibility score between resume and job description.
    
    This tool analyzes how well a resume matches a job description using multiple scoring dimensions:
    - Keyword matching (35% weight)
    - Skills alignment (30% weight)
    - Experience relevance (25% weight)
    - Format quality (10% weight)
    
    Args:
        resume_text: The full text content of the resume to analyze
        job_description: The job posting description text with requirements
        
    Returns:
        Dictionary containing:
        - overall_score: Combined score (0-100)
        - keyword_score: Keyword match percentage
        - skills_score: Skills alignment percentage
        - experience_score: Experience relevance percentage
        - format_score: Format quality score
        - grade: Letter grade (A-F)
        - recommendations: List of improvement suggestions
    """
    tool = ATSScoringTool()
    
    try:
        result = await asyncio.to_thread(
            tool.calculate_score,
            resume_text=resume_text,
            job_description=job_description
        )
        
        return {
            "overall_score": result.get("overall_score", 0),
            "keyword_score": result.get("keyword_score", 0),
            "skills_score": result.get("skills_score", 0),
            "experience_score": result.get("experience_score", 0),
            "format_score": result.get("format_score", 0),
            "grade": result.get("grade", "F"),
            "recommendations": result.get("recommendations", []),
            "missing_keywords": result.get("missing_keywords", []),
            "matched_keywords": result.get("matched_keywords", [])
        }
    except Exception as e:
        return {
            "error": str(e),
            "overall_score": 0,
            "status": "error"
        }


# ============================================
# TOOL 2: Keyword Extraction
# ============================================
@mcp.tool()
async def extract_keywords(text: str) -> Dict[str, Any]:
    """
    Extract technical skills, soft skills, and action verbs from job description text.
    
    This tool performs NLP analysis to identify:
    - Technical skills (programming languages, frameworks, tools)
    - Soft skills (leadership, communication, teamwork)
    - Action verbs (managed, developed, implemented)
    - Keyword density and frequency analysis
    
    Args:
        text: Job description text to analyze for keywords
        
    Returns:
        Dictionary containing:
        - technical_skills: List of technical skill keywords
        - soft_skills: List of soft skill keywords
        - action_verbs: List of action verbs found
        - keyword_density: Frequency analysis of top keywords
        - total_keywords: Total number of unique keywords extracted
    """
    tool = KeywordExtractorTool()
    
    try:
        result = await asyncio.to_thread(
            tool.extract_keywords,
            text=text
        )
        
        return {
            "technical_skills": result.get("technical_skills", []),
            "soft_skills": result.get("soft_skills", []),
            "action_verbs": result.get("action_verbs", []),
            "keyword_density": result.get("keyword_density", {}),
            "total_keywords": len(result.get("technical_skills", [])) + 
                            len(result.get("soft_skills", [])),
            "categories": result.get("categories", {})
        }
    except Exception as e:
        return {
            "error": str(e),
            "technical_skills": [],
            "soft_skills": [],
            "action_verbs": []
        }


# ============================================
# TOOL 3: Markdown Validation
# ============================================
@mcp.tool()
async def validate_markdown(markdown_content: str) -> Dict[str, Any]:
    """
    Validate Markdown syntax and structure for resume formatting.
    
    This tool checks Markdown documents for:
    - Syntax errors (malformed headers, broken links)
    - Structural issues (missing sections, inconsistent formatting)
    - Formatting warnings
    - Best practice violations
    
    Args:
        markdown_content: The Markdown document content to validate
        
    Returns:
        Dictionary containing:
        - is_valid: Boolean indicating if Markdown is valid
        - errors: List of syntax/structural errors found
        - warnings: List of potential issues/warnings
        - suggestions: Improvement recommendations
        - line_numbers: Error locations in source
    """
    tool = MarkdownValidatorTool()
    
    try:
        result = await asyncio.to_thread(
            tool.validate_markdown,
            markdown_content=markdown_content
        )
        
        return {
            "is_valid": result.get("is_valid", False),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
            "suggestions": result.get("suggestions", []),
            "line_numbers": result.get("line_numbers", []),
            "character_count": len(markdown_content)
        }
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [str(e)],
            "warnings": [],
            "suggestions": []
        }


# ============================================
# TOOL 4: Resume Parser
# ============================================
@mcp.tool()
async def parse_resume(file_path: str) -> Dict[str, Any]:
    """
    Parse resume file (PDF/DOCX) and extract structured content.
    
    This tool processes resume files to extract:
    - Text content from PDF or DOCX formats
    - Structured sections (Experience, Education, Skills)
    - Metadata (file format, page count, dates)
    - Contact information
    
    Args:
        file_path: Absolute path to the resume file to parse
        
    Returns:
        Dictionary containing:
        - sections: Extracted resume sections with content
        - text: Full text content of resume
        - metadata: File metadata (format, size, pages)
        - contact_info: Extracted contact details
        - format: File format (pdf/docx)
    """
    tool = ResumeParserTool()
    
    try:
        result = await asyncio.to_thread(
            tool.parse_resume,
            file_path=file_path
        )
        
        return {
            "sections": result.get("sections", {}),
            "text": result.get("text", ""),
            "metadata": result.get("metadata", {}),
            "contact_info": result.get("contact_info", {}),
            "format": result.get("format", "unknown"),
            "page_count": result.get("page_count", 0)
        }
    except Exception as e:
        return {
            "error": str(e),
            "sections": {},
            "text": "",
            "format": "unknown"
        }


# ============================================
# RESOURCE: Resume Templates
# ============================================
@mcp.resource("template://resume/{template_name}")
async def get_resume_template(template_name: str) -> str:
    """
    Provide Markdown resume templates for different styles.
    
    Available templates:
    - template://resume/professional - Standard professional format
    - template://resume/academic - Academic/research-focused format
    - template://resume/technical - Technical/engineering format
    - template://resume/creative - Creative industry format
    
    Args:
        template_name: Template type (professional, academic, technical, creative)
        
    Returns:
        Markdown template content as string
    """
    
    templates = {
        "professional": """# [YOUR NAME]

**[Professional Title]**

[Email] | [Phone] | [LinkedIn] | [Location]

---

## PROFESSIONAL SUMMARY

[Summary content highlighting key qualifications and career objectives]

---

## PROFESSIONAL EXPERIENCE

### **[Job Title]** | [Company Name]
*[Start Date] - [End Date] | [Location]*

- Achievement 1 with quantifiable results
- Achievement 2 demonstrating impact and skills
- Achievement 3 showcasing relevant experience

### **[Previous Job Title]** | [Previous Company]
*[Start Date] - [End Date] | [Location]*

- Key accomplishment highlighting technical skills
- Project delivery with measurable outcomes
- Leadership or collaboration examples

---

## EDUCATION

**[Degree Name]** | [University Name]
*Graduated: [Month Year] | [Location]*

- Relevant coursework or achievements
- GPA (if strong): X.XX/4.0

---

## TECHNICAL SKILLS

- **Languages:** Python, Java, JavaScript, SQL
- **Frameworks:** Django, React, Spring Boot, FastAPI
- **Cloud & Tools:** AWS, Docker, Kubernetes, Git
- **Databases:** PostgreSQL, MongoDB, Redis

---

## CERTIFICATIONS

- [Certification Name] | [Issuing Organization] | [Year]
- [Certification Name] | [Issuing Organization] | [Year]
""",
        
        "academic": """# [YOUR NAME]

*Curriculum Vitae*

[Email] | [Phone] | [Website/Portfolio] | [ORCID]

---

## RESEARCH INTERESTS

[Description of research areas, methodologies, and focus]

---

## EDUCATION

**Ph.D. in [Field]** | [University Name]
*[Start Year] - [End Year]*
- Dissertation: "[Title]"
- Advisor: Dr. [Name]

**M.S. in [Field]** | [University Name]
*[Start Year] - [End Year]*
- Thesis: "[Title]"

**B.S. in [Field]** | [University Name]
*[Graduation Year]*

---

## PUBLICATIONS

### Peer-Reviewed Journal Articles

1. [Authors]. ([Year]). [Title]. *[Journal Name]*, [Volume]([Issue]), [Pages]. DOI: [DOI]
2. [Authors]. ([Year]). [Title]. *[Journal Name]*, [Volume]([Issue]), [Pages].

### Conference Proceedings

1. [Authors]. ([Year]). [Title]. In *[Conference Name]* (pp. [Pages]). [Location].

---

## RESEARCH EXPERIENCE

**[Position Title]** | [Institution]
*[Start Date] - [End Date]*

- Research focus and methodologies
- Key findings and contributions
- Publications or presentations resulting from work

---

## TEACHING EXPERIENCE

**[Course Name/Number]** - [Role] | [Institution]
*[Semester Year]*

- Course description and student level
- Teaching responsibilities and innovations

---

## AWARDS AND HONORS

- **[Award Name]** - [Granting Organization], [Year]
- **[Fellowship Name]** - [Institution], [Year]

---

## PROFESSIONAL SERVICE

- Reviewer: [Journal Names]
- Committee Member: [Committee/Conference Names]
""",
        
        "technical": """# [YOUR NAME]

## Software Engineer

[Email] | [Phone] | [GitHub](https://github.com/username) | [Portfolio](https://portfolio.com)

---

## TECHNICAL SKILLS

| Category | Technologies |
|----------|-------------|
| **Languages** | Python, Java, JavaScript, TypeScript, Go, SQL |
| **Frontend** | React, Vue.js, Angular, HTML5, CSS3, Tailwind |
| **Backend** | Django, FastAPI, Spring Boot, Node.js, Express |
| **Cloud & DevOps** | AWS (EC2, S3, Lambda), Docker, Kubernetes, Jenkins |
| **Databases** | PostgreSQL, MongoDB, Redis, MySQL, Elasticsearch |
| **Tools** | Git, JIRA, CI/CD, Linux, Agile, REST APIs |

---

## PROJECTS

### **[Project Name]** | [Tech Stack]
*[Date] | [GitHub Link]*

- Built [description of project] using [technologies]
- Achieved [metric/outcome] resulting in [impact]
- Implemented [key feature] with [technology]
- **Tech:** Python, React, PostgreSQL, Docker, AWS

### **[Another Project]** | [Tech Stack]
*[Date] | [Live Demo Link]*

- Developed [feature/system] handling [scale/complexity]
- Optimized performance by [percentage/metric]
- Integrated [APIs/services] for [functionality]
- **Tech:** Node.js, MongoDB, Redis, Kubernetes

---

## EXPERIENCE

### **[Job Title]** | [Company Name]
*[Start Date] - [End Date] | [Location]*

- Engineered [system/feature] processing [volume] with [technology]
- Reduced [metric] by [percentage] through [optimization]
- Led development of [project] serving [users/scale]
- Collaborated with cross-functional teams on [initiative]

---

## EDUCATION

**[Degree]** in Computer Science | [University]
*Graduated: [Month Year]*

- Relevant Coursework: Data Structures, Algorithms, Database Systems
- GPA: X.XX/4.0
""",
        
        "creative": """\\documentclass[11pt,a4paper]{article}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{graphicx}
\\usepackage{xcolor}
\\usepackage{tikz}

\\definecolor{accent}{RGB}{0,102,204}

\\begin{document}

% Creative header with accent color
\\begin{center}
{\\Huge \\color{accent}\\textbf{[YOUR NAME]}}\\\\[5pt]
{\\large Creative Professional}\\\\[8pt]
[Portfolio URL] | [Email] | [Social Media]
\\end{center}

\\section*{ABOUT ME}
[Creative profile]

\\section*{PORTFOLIO HIGHLIGHTS}
[Project showcases]

\\section*{EXPERIENCE}
[Work history with creative focus]

\\section*{SKILLS \\& TOOLS}
[Creative skills and software]

\\end{document}"""
    }
    
    return templates.get(template_name, templates["professional"])


# ============================================
# PROMPT: Resume Optimization Workflow
# ============================================
@mcp.prompt()
async def optimize_resume_prompt(
    job_title: str,
    company: str,
    experience_level: str = "mid"
) -> List[Dict[str, str]]:
    """
    Generate a comprehensive prompt for resume optimization workflow.
    
    Args:
        job_title: Target job position title
        company: Target company name
        experience_level: Career level - 'entry', 'mid', 'senior', 'lead'
        
    Returns:
        List of message dictionaries for LLM consumption
    """
    
    experience_guidance = {
        "entry": "Focus on education, projects, internships, and transferable skills.",
        "mid": "Emphasize 3-7 years of experience with quantified achievements and technical depth.",
        "senior": "Highlight 7+ years, leadership, strategic impact, and mentorship.",
        "lead": "Showcase technical leadership, architecture decisions, and team/org-level impact."
    }
    
    prompt_text = f"""You are an expert resume optimization specialist with deep knowledge of ATS systems and recruiting best practices.

**TARGET POSITION**
- Job Title: {job_title}
- Company: {company}
- Experience Level: {experience_level}

**YOUR OPTIMIZATION MISSION**

{experience_guidance.get(experience_level, experience_guidance["mid"])}

**STEP-BY-STEP OPTIMIZATION PROCESS**

1. **Keyword Analysis** (use extract_keywords tool)
   - Extract all technical skills, soft skills, and action verbs from job description
   - Identify must-have vs nice-to-have qualifications
   - Note keyword density for top requirements

2. **ATS Scoring** (use calculate_ats_score tool)
   - Score current resume against job requirements
   - Identify keyword gaps and format issues
   - Calculate improvement potential

3. **Content Optimization**
   - Rewrite bullet points to include target keywords naturally
   - Add quantified achievements (%, $, #, time saved)
   - Use strong action verbs (Led, Architected, Optimized, Delivered)
   - Align experience descriptions with job requirements

4. **Format Optimization**
   - Use standard ATS-friendly section headers (EXPERIENCE, EDUCATION, SKILLS)
   - Avoid tables, text boxes, headers/footers
   - Ensure proper date formatting (MM/YYYY)
   - Include both acronyms and full terms (e.g., "ML (Machine Learning)")

5. **LaTeX Generation & Validation** (use validate_latex tool)
   - Generate clean, professional LaTeX document
   - Validate syntax and structure
   - Ensure PDF will compile correctly

**SUCCESS CRITERIA**
✓ ATS Score ≥ 85% (target: 90-95%)
✓ All critical keywords included in context
✓ Quantified achievements in 80%+ of bullet points
✓ Error-free LaTeX compilation
✓ Professional, readable formatting

**OUTPUT FORMAT**
Provide:
1. ATS analysis summary
2. Optimized resume content sections
3. LaTeX source code
4. Before/after comparison metrics
5. Final recommendations

Begin optimization now."""

    return [
        {
            "role": "user",
            "content": prompt_text
        }
    ]


# ============================================
# PROMPT: ATS Keyword Matching Strategy
# ============================================
@mcp.prompt()
async def ats_keyword_strategy(
    job_description: str,
    current_score: int = 0
) -> List[Dict[str, str]]:
    """
    Generate strategic guidance for improving ATS keyword matching.
    
    Args:
        job_description: The full job posting text
        current_score: Current ATS score (0-100)
        
    Returns:
        List of message dictionaries with keyword strategy
    """
    
    prompt_text = f"""You are an ATS optimization expert specializing in keyword strategy.

**CURRENT ATS SCORE**: {current_score}%
**TARGET SCORE**: 90%+

**JOB DESCRIPTION**
{job_description}

**KEYWORD OPTIMIZATION STRATEGY**

1. **Extract & Categorize Keywords** (use extract_keywords tool)
   - Must-have technical skills (hard requirements)
   - Preferred qualifications (nice-to-have)
   - Industry terminology and buzzwords
   - Action verbs from job responsibilities

2. **Keyword Placement Strategy**
   - **Professional Summary**: Top 5 keywords (highest density)
   - **Skills Section**: All technical keywords with proficiency levels
   - **Experience Section**: Keywords in context with achievements
   - **Project Descriptions**: Domain-specific terminology

3. **Keyword Density Rules**
   - Critical keywords: 3-5 mentions across resume
   - Secondary keywords: 2-3 mentions
   - Long-tail keywords: 1-2 mentions
   - Avoid keyword stuffing (keep context natural)

4. **Synonym & Variation Strategy**
   - Include both acronyms and full terms
   - Use industry synonyms (e.g., "AI/ML/Artificial Intelligence")
   - Cover plural and singular forms
   - Include related technologies in same ecosystem

**ACTION PLAN**
Generate a prioritized list of keywords to add, with specific placement recommendations for maximum ATS impact while maintaining readability."""

    return [
        {
            "role": "user",
            "content": prompt_text
        }
    ]


# ============================================
# Run MCP Server
# ============================================
if __name__ == "__main__":
    # Run with STDIO transport for local agent communication
    mcp.run(transport="stdio")
