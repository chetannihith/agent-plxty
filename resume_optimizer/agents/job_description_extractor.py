"""
Stage 1: Job Description Extraction Agent
Uses CrewAI for web scraping and parsing (demonstrates A2A protocol)
"""
from typing import Dict, Any
from crewai import Agent as CrewAgent, Task, Crew
import os
import requests
from bs4 import BeautifulSoup
import re


class JobDescriptionExtractorCrew:
    """
    CrewAI-based job description extractor
    This will be wrapped with A2A protocol for Google ADK integration
    """
    
    def __init__(self, model: str = "groq/llama-3.1-8b-instant"):
        """
        Initialize the crew with Groq LLM
        
        Args:
            model: LLM model to use (default: Groq's Llama 3.1)
        """
        self.model = model
        
        # Set up Groq API key from environment if not already set
        if not os.environ.get("GROQ_API_KEY"):
            # Try to get from GOOGLE_API_KEY as fallback
            groq_key = os.environ.get("GOOGLE_API_KEY")
            if groq_key:
                os.environ["GROQ_API_KEY"] = groq_key
        
        self.crew = self._build_crew()
    
    def _build_crew(self) -> Crew:
        """Build CrewAI crew for job extraction using Groq"""
        
        # Define the web scraper agent
        web_scraper = CrewAgent(
            role="Job Posting Web Scraper",
            goal="Extract complete job posting information from URLs",
            backstory="""You are an expert web scraper specialized in extracting 
            job postings from various career websites. You understand HTML structure 
            and can identify key information like job title, company, requirements, 
            and responsibilities.""",
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )
        
        # Define the parser agent
        parser = CrewAgent(
            role="Job Description Parser",
            goal="Parse and structure job posting data into organized format",
            backstory="""You are a data parsing specialist who excels at structuring 
            unstructured job posting text into organized categories like requirements, 
            qualifications, responsibilities, and preferred skills.""",
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )
        
        return Crew(
            agents=[web_scraper, parser],
            tasks=[],  # Tasks will be added dynamically
            verbose=True
        )
    
    def _scrape_webpage(self, url: str) -> str:
        """Actually scrape the webpage content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            print(f"✅ Scraped {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            print(f"❌ Web scraping failed: {e}")
            return f"Failed to scrape URL: {url}. Error: {str(e)}"
    
    def extract_job_description(self, job_url: str) -> Dict[str, Any]:
        """
        Extract and parse job description from URL
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Structured job data
        """
        
        # First, actually scrape the webpage
        print(f"🌐 Scraping job posting from: {job_url}")
        scraped_content = self._scrape_webpage(job_url)
        
        if len(scraped_content) < 100:
            print("⚠️ Very little content scraped, using fallback")
            return self._create_fallback_job_data(job_url)
        
        # Define scraping task
        scrape_task = Task(
            description=f"""
            Here is the scraped content from job URL: {job_url}
            
            SCRAPED CONTENT:
            {scraped_content[:3000]}
            
            **Special Instructions for LinkedIn Jobs:**
            - Look for job title in <h1> or <h2> tags with class containing 'job-title'
            - Company name usually in <a> tags with class 'company-name' or similar
            - Skills section often has tags or keywords in lists
            - Responsibilities are typically in bullet points
            
            **For all job sites, extract:**
            - Job title (exact text, no modifications)
            - Company name and location
            - Complete job description/summary
            - Required qualifications (technical skills, experience, education)
            - Preferred/nice-to-have qualifications
            - Key responsibilities (bullet points)
            - Technical skills mentioned (programming languages, tools, frameworks)
            - Years of experience required
            - Education requirements (degree level)
            - Salary/compensation info (if available)
            - Benefits mentioned
            - Work arrangement (remote/hybrid/onsite)
            
            Return ALL extracted text preserving structure and formatting.
            """,
            agent=self.crew.agents[0],
            expected_output="Complete raw job posting text with all details preserved"
        )
        
        # Define parsing task
        parse_task = Task(
            description="""
            Parse the scraped job posting into a structured format.
            
            Extract and organize:
            1. **Basic Info:**
               - job_title
               - company
               - location
               - salary_range (if mentioned)
            
            2. **Requirements:**
               - required_skills (list)
               - preferred_skills (list)
               - required_experience (years)
               - education_level
            
            3. **Description:**
               - job_summary
               - responsibilities (list)
               - qualifications (list)
            
            4. **Keywords:**
               - Extract 20-30 important keywords from the job posting
            
            Format as JSON.
            """,
            agent=self.crew.agents[1],
            expected_output="Structured JSON with job details",
            context=[scrape_task]
        )
        
        # Update crew tasks
        self.crew.tasks = [scrape_task, parse_task]
        
        # Execute crew
        try:
            result = self.crew.kickoff()
            
            # Parse result
            import json
            import re
            
            result_str = str(result)
            job_data = None
            
            try:
                # Try direct JSON parsing
                job_data = json.loads(result_str)
            except:
                try:
                    # Try extracting JSON from markdown code blocks
                    json_match = re.search(r'```json\s*({.*?})\s*```', result_str, re.DOTALL)
                    if json_match:
                        job_data = json.loads(json_match.group(1))
                    elif '{' in result_str:
                        # Try finding JSON object in text
                        start = result_str.index('{')
                        end = result_str.rindex('}') + 1
                        job_data = json.loads(result_str[start:end])
                except Exception as parse_err:
                    print(f"⚠️ JSON parsing failed: {parse_err}")
            
            if not job_data:
                # Fallback: create structured data from text
                print("⚠️ Using fallback parsing for job data")
                job_data = {
                    "job_title": "Position from " + job_url.split('/')[2],
                    "company": "See job posting",
                    "location": "Not specified",
                    "job_summary": result_str[:500] if len(result_str) > 500 else result_str,
                    "required_skills": self._extract_skills_from_text(result_str),
                    "preferred_skills": [],
                    "responsibilities": [],
                    "qualifications": [],
                    "keywords": self._extract_keywords_from_text(result_str),
                    "raw_output": result_str
                }
            
            # Ensure required fields exist
            job_data.setdefault('required_skills', [])
            job_data.setdefault('keywords', [])
            job_data.setdefault('job_title', 'Software Engineer')
            job_data.setdefault('company', 'Unknown Company')
            
            return job_data
            
        except Exception as e:
            print(f"❌ Error in CrewAI job extraction: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "job_title": "Software Engineer",
                "company": "Tech Company",
                "location": "Remote",
                "required_skills": ["Python", "JavaScript", "SQL"],
                "keywords": ["software", "engineer", "developer", "programming"],
                "job_summary": "Software engineering position"
            }
    
    def _extract_skills_from_text(self, text: str) -> list:
        """Extract common technical skills from text"""
        common_skills = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Ruby', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring', 'Express',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
            'Git', 'Agile', 'Scrum', 'REST', 'GraphQL', 'API', 'Microservices'
        ]
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills[:15]  # Return top 15
    
    def _extract_keywords_from_text(self, text: str) -> list:
        """Extract important keywords from text"""
        import re
        # Remove special characters and split into words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        # Filter common words
        stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'will', 'have', 'your', 'about'}
        keywords = [w for w in set(words) if w not in stopwords]
        return keywords[:25]  # Return top 25
    
    def _create_fallback_job_data(self, job_url: str) -> Dict[str, Any]:
        """Create fallback job data when scraping fails"""
        return {
            "job_title": "Software Engineer",
            "company": "Tech Company (from " + job_url.split('/')[2] + ")",
            "location": "Remote/Hybrid",
            "job_summary": "Software engineering position requiring technical skills and experience.",
            "required_skills": ["Python", "JavaScript", "SQL", "Git", "REST APIs"],
            "preferred_skills": ["React", "Node.js", "AWS", "Docker"],
            "responsibilities": [
                "Develop and maintain software applications",
                "Collaborate with cross-functional teams",
                "Write clean, maintainable code"
            ],
            "qualifications": [
                "Bachelor's degree in Computer Science or related field",
                "2+ years of software development experience"
            ],
            "keywords": ["software", "engineer", "developer", "programming", "coding", "technical"],
            "raw_output": "Scraped content not available",
            "note": "Fallback data used - actual job posting not accessible"
        }