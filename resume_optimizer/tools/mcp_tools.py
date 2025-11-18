"""
MCP Tools for Resume Optimization Pipeline
Implements Model Context Protocol compliant tools for Google ADK
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json


class MCPToolRequest(BaseModel):
    """MCP-compliant tool request schema."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    context_id: str = ""


class MCPToolResponse(BaseModel):
    """MCP-compliant tool response schema."""
    tool_name: str
    status: str
    result: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebScraperTool:
    """
    MCP Tool for web scraping job postings
    Extracts job descriptions from URLs
    """
    
    def __init__(self):
        self.name = "web_scraper_tool"
        self.description = "Scrapes job posting content from URLs"
    
    def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """Execute web scraping"""
        url = request.arguments.get("url", "")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Try to extract structured data
            job_data = {
                "raw_text": text,
                "title": self._extract_title(soup),
                "company": self._extract_company(soup),
                "description": text[:5000]  # Limit to 5000 chars
            }
            
            return MCPToolResponse(
                tool_name=self.name,
                status="success",
                result=job_data,
                metadata={"url": url, "length": len(text)}
            )
            
        except Exception as e:
            return MCPToolResponse(
                tool_name=self.name,
                status="error",
                result={"error": str(e)},
                metadata={"url": url}
            )
    
    def _extract_title(self, soup) -> str:
        """Extract job title from HTML"""
        # Try common patterns
        title_tags = soup.find_all(['h1', 'h2'], class_=re.compile(r'(job|title|position)', re.I))
        if title_tags:
            return title_tags[0].get_text().strip()
        
        title = soup.find('title')
        return title.get_text().strip() if title else "Unknown Position"
    
    def _extract_company(self, soup) -> str:
        """Extract company name from HTML"""
        company_tags = soup.find_all(class_=re.compile(r'company', re.I))
        if company_tags:
            return company_tags[0].get_text().strip()
        return "Unknown Company"


class ATSScoringTool:
    """
    MCP Tool for ATS (Applicant Tracking System) scoring
    Calculates how well a resume matches a job description
    """
    
    def __init__(self):
        self.name = "ats_scoring_tool"
        self.description = "Calculates ATS compatibility score between resume and job"
    
    def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """Calculate ATS score"""
        resume_text = request.arguments.get("resume_text", "")
        job_text = request.arguments.get("job_text", "")
        
        try:
            # Calculate various scoring components
            keyword_score = self._calculate_keyword_match(resume_text, job_text)
            skill_score = self._calculate_skill_match(resume_text, job_text)
            semantic_score = self._calculate_semantic_similarity(resume_text, job_text)
            format_score = self._calculate_format_score(resume_text)
            
            # Weighted average
            final_score = (
                keyword_score * 0.35 +
                skill_score * 0.30 +
                semantic_score * 0.25 +
                format_score * 0.10
            )
            
            result = {
                "overall_score": round(final_score, 2),
                "keyword_score": round(keyword_score, 2),
                "skill_score": round(skill_score, 2),
                "semantic_score": round(semantic_score, 2),
                "format_score": round(format_score, 2),
                "grade": self._get_grade(final_score),
                "recommendations": self._generate_recommendations(
                    keyword_score, skill_score, semantic_score, format_score
                )
            }
            
            return MCPToolResponse(
                tool_name=self.name,
                status="success",
                result=result,
                metadata={"method": "multi_factor_analysis"}
            )
            
        except Exception as e:
            return MCPToolResponse(
                tool_name=self.name,
                status="error",
                result={"error": str(e)},
                metadata={}
            )
    
    def _calculate_keyword_match(self, resume: str, job: str) -> float:
        """Calculate keyword overlap"""
        resume_words = set(re.findall(r'\b\w+\b', resume.lower()))
        job_words = set(re.findall(r'\b\w+\b', job.lower()))
        
        if not job_words:
            return 0.0
        
        overlap = len(resume_words & job_words)
        score = (overlap / len(job_words)) * 100
        return min(score, 100.0)
    
    def _calculate_skill_match(self, resume: str, job: str) -> float:
        """Calculate technical skill match"""
        # Common technical skills
        common_skills = [
            'python', 'java', 'javascript', 'sql', 'aws', 'azure', 'docker',
            'kubernetes', 'react', 'angular', 'node', 'machine learning',
            'data science', 'agile', 'scrum', 'git', 'ci/cd', 'api', 'rest'
        ]
        
        resume_lower = resume.lower()
        job_lower = job.lower()
        
        job_skills = [skill for skill in common_skills if skill in job_lower]
        if not job_skills:
            return 70.0  # No specific skills mentioned
        
        matched_skills = [skill for skill in job_skills if skill in resume_lower]
        score = (len(matched_skills) / len(job_skills)) * 100
        return score
    
    def _calculate_semantic_similarity(self, resume: str, job: str) -> float:
        """Calculate semantic similarity using TF-IDF"""
        try:
            vectorizer = TfidfVectorizer(max_features=200, stop_words='english')
            vectors = vectorizer.fit_transform([resume, job])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity * 100
        except:
            return 50.0  # Default if calculation fails
    
    def _calculate_format_score(self, resume: str) -> float:
        """Score resume formatting quality"""
        score = 100.0
        
        # Check for common sections
        sections = ['experience', 'education', 'skills', 'summary']
        missing = sum(1 for s in sections if s not in resume.lower())
        score -= missing * 5
        
        # Check length
        words = len(resume.split())
        if words < 200:
            score -= 20
        elif words > 1000:
            score -= 10
        
        return max(score, 0.0)
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, keyword, skill, semantic, format) -> List[str]:
        """Generate improvement recommendations"""
        recs = []
        
        if keyword < 70:
            recs.append("Add more keywords from the job description")
        if skill < 70:
            recs.append("Highlight technical skills that match the job requirements")
        if semantic < 70:
            recs.append("Align your experience descriptions with job responsibilities")
        if format < 80:
            recs.append("Improve resume structure with clear sections")
        
        return recs


class KeywordExtractorToolEnhanced:
    """
    Enhanced MCP Tool for keyword extraction and analysis
    Uses NLP to extract and rank keywords
    """
    
    def __init__(self):
        self.name = "keyword_extractor_enhanced"
        self.description = "Extracts and ranks keywords from job descriptions"
    
    def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """Extract keywords"""
        text = request.arguments.get("text", "")
        top_n = request.arguments.get("top_n", 20)
        
        try:
            # Extract using TF-IDF
            keywords = self._extract_tfidf_keywords(text, top_n)
            
            # Extract technical terms
            technical_terms = self._extract_technical_terms(text)
            
            # Extract action verbs
            action_verbs = self._extract_action_verbs(text)
            
            result = {
                "keywords": keywords,
                "technical_terms": technical_terms,
                "action_verbs": action_verbs,
                "total_count": len(keywords)
            }
            
            return MCPToolResponse(
                tool_name=self.name,
                status="success",
                result=result,
                metadata={"method": "tfidf_enhanced"}
            )
            
        except Exception as e:
            return MCPToolResponse(
                tool_name=self.name,
                status="error",
                result={"error": str(e)},
                metadata={}
            )
    
    def _extract_tfidf_keywords(self, text: str, top_n: int) -> List[Dict[str, Any]]:
        """Extract keywords using TF-IDF"""
        try:
            vectorizer = TfidfVectorizer(
                max_features=top_n,
                stop_words='english',
                ngram_range=(1, 2)
            )
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            keywords = [
                {"keyword": feature_names[i], "score": float(scores[i])}
                for i in scores.argsort()[-top_n:][::-1]
            ]
            
            return keywords
        except:
            return []
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms"""
        technical_patterns = [
            r'\b(?:Python|Java|JavaScript|C\+\+|SQL|AWS|Azure|Docker|Kubernetes)\b',
            r'\b(?:API|REST|GraphQL|microservices|CI/CD|DevOps)\b',
            r'\b(?:machine learning|data science|AI|NLP|deep learning)\b',
        ]
        
        terms = set()
        for pattern in technical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.update(matches)
        
        return list(terms)[:15]
    
    def _extract_action_verbs(self, text: str) -> List[str]:
        """Extract action verbs commonly used in resumes"""
        action_verbs = [
            'developed', 'designed', 'implemented', 'managed', 'led',
            'created', 'built', 'improved', 'optimized', 'achieved',
            'delivered', 'collaborated', 'coordinated', 'analyzed'
        ]
        
        found_verbs = [verb for verb in action_verbs if verb in text.lower()]
        return found_verbs[:10]


class ResumeParserTool:
    """
    MCP Tool for parsing resume files
    Supports PDF, DOCX, and JSON formats
    """
    
    def __init__(self):
        self.name = "resume_parser_tool"
        self.description = "Parses resume files and extracts structured data"
    
    def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """Parse resume file"""
        file_path = request.arguments.get("file_path", "")
        file_type = request.arguments.get("file_type", "pdf")
        
        try:
            if file_type == "json":
                result = self._parse_json(file_path)
            elif file_type == "pdf":
                result = self._parse_pdf(file_path)
            elif file_type == "docx":
                result = self._parse_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            return MCPToolResponse(
                tool_name=self.name,
                status="success",
                result=result,
                metadata={"file_type": file_type, "file_path": file_path}
            )
            
        except Exception as e:
            return MCPToolResponse(
                tool_name=self.name,
                status="error",
                result={"error": str(e)},
                metadata={"file_path": file_path}
            )
    
    def _parse_json(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON resume"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF resume using PyPDF2"""
        from PyPDF2 import PdfReader
        
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return self._extract_sections(text)
    
    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX resume (placeholder - needs python-docx)"""
        # TODO: Implement DOCX parsing when python-docx is installed
        raise NotImplementedError("DOCX parsing requires python-docx package")
    
    def _extract_sections(self, text: str) -> Dict[str, Any]:
        """Extract resume sections from text"""
        sections = {
            "raw_text": text,
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "summary": "",
            "experience": [],
            "education": [],
            "skills": []
        }
        
        return sections
    
    def _extract_name(self, text: str) -> str:
        """Extract name from resume (simple heuristic)"""
        lines = text.split('\n')
        return lines[0].strip() if lines else "Unknown"
    
    def _extract_email(self, text: str) -> str:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        matches = re.findall(phone_pattern, text)
        return matches[0] if matches else ""


# Aliases for MCP server compatibility
KeywordExtractorTool = KeywordExtractorToolEnhanced
