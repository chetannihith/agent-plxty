"""
Stage 5: Markdown Formatter Agent (Sequential)
Generates professional PURE Markdown resume from user's actual data
"""
from google.adk.agents import BaseAgent
from google.adk.events import Event
from typing import AsyncGenerator
from google.genai import types
from google.genai import Client


class MarkdownFormatterAgent(BaseAgent):
    """Custom agent that formats resume using actual profile data"""
    
    def __init__(self, model: str = "gemini-2.0-flash", name: str = "markdown_formatter_agent"):
        super().__init__(name=name)
        # Store model name in a private variable to avoid Pydantic conflicts
        object.__setattr__(self, '_model_name', model)
    
    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        """Generate markdown resume using actual profile data from session state"""
        
        # Get data from session state
        profile_data = ctx.session.state.get("profile_data", {})
        job_data = ctx.session.state.get("job_data", {})
        
        # Extract profile sections
        profile_sections = profile_data.get("relevant_sections", [])
        
        print(f"📝 [markdown_formatter_agent] Building resume from {len(profile_sections)} profile sections")
        
        # Combine all profile text
        full_profile_text = "\\n\\n".join(profile_sections) if profile_sections else "No profile data available"
        
        # Show preview of what we have
        print(f"📄 Profile preview: {full_profile_text[:300]}...")
        
        # Build prompt with actual data embedded
        job_title = job_data.get('job_title', 'Software Engineer')
        company = job_data.get('company', 'Unknown')
        required_skills = ', '.join(job_data.get('required_skills', [])[:10])
        keywords = ', '.join(job_data.get('keywords', [])[:10])
        
        prompt = f"""You are a resume formatter. Create a PURE MARKDOWN resume using the information below.

**USER'S ACTUAL RESUME CONTENT:**
```
{full_profile_text}
```

**TARGET JOB:**
- Title: {job_title}
- Company: {company}
- Required Skills: {required_skills}
- Keywords: {keywords}

**INSTRUCTIONS:**
1. Extract the person's ACTUAL name, education, work experience, and skills from the resume content above
2. Format it as clean Markdown (NO HTML tags)
3. Enhance descriptions with keywords from the target job
4. If information is truly missing, use "[Add your X]" placeholder

**FORMAT (Pure Markdown):**
```markdown
# [ACTUAL NAME FROM RESUME]

[email if found] | [phone if found] | [location if found]

## Professional Summary
[2-3 sentences highlighting relevant experience for {job_title}]

## Work Experience

### [ACTUAL JOB TITLE from resume] | [ACTUAL COMPANY from resume]
*[ACTUAL DATES from resume]*

- [Actual achievement, enhanced with job keywords]
- [Actual achievement]
- [Actual achievement]

[Repeat for other jobs found in resume]

## Technical Skills

**Languages:** [actual languages from resume]
**Frameworks/Tools:** [actual tools from resume]
**Other:** [other skills from resume]

## Education

### [ACTUAL DEGREE from resume] | [ACTUAL UNIVERSITY from resume]
*[ACTUAL YEAR from resume]*

[Major/GPA if mentioned]
```

OUTPUT: Return ONLY the markdown content, no JSON wrapper, no code blocks.
"""
        
        # Use Google GenAI Client directly (not ADK wrapper)
        try:
            # Get the model name
            model_name = object.__getattribute__(self, '_model_name')
            
            # Create client and generate content
            client = Client()
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            # Extract text from response
            if response.text:
                resume_content = response.text
                
                # Clean up any markdown code blocks if present
                if "```" in resume_content:
                    # Remove ```markdown or ```json wrappers
                    resume_content = resume_content.replace("```markdown", "").replace("```json", "").replace("```", "").strip()
                
                # Save to session state
                ctx.session.state["resume_content"] = resume_content
                
                print(f"✅ [markdown_formatter_agent] Generated {len(resume_content)} character resume")
                print(f"📄 Preview: {resume_content[:200]}...")
            else:
                print("❌ [markdown_formatter_agent] No response from LLM")
                ctx.session.state["resume_content"] = "# Error\n\nFailed to generate resume."
        
        except Exception as e:
            print(f"❌ [markdown_formatter_agent] Error: {e}")
            import traceback
            traceback.print_exc()
            ctx.session.state["resume_content"] = f"# Error\n\nFailed to generate resume: {str(e)}"
        
        # Yield completion event
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=None
        )


def create_markdown_formatter_agent(model: str = "gemini-2.0-flash"):
    """Factory function to create markdown formatter agent"""
    return MarkdownFormatterAgent(model=model)
