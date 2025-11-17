"""
Stage 6: Formatting Checker Agent (Parallel Agent 2)
Validates Markdown/HTML formatting and structure
"""
from google.adk.agents import BaseAgent
from typing import Dict, Any
import re


class FormattingCheckerAgent(BaseAgent):
    """
    Agent 10: Formatting validation for Markdown/HTML resume
    Runs in parallel with QualityValidatorAgent
    """
    
    def __init__(self, name: str = "formatting_checker_agent"):
        super().__init__(name=name)
    
    async def _run_async_impl(self, ctx):
        """
        Google ADK BaseAgent execution method
        
        Validates Markdown/HTML formatting and structure
        Must yield events, not return values
        """
        from google.adk.events import Event
        
        # Get resume content from state
        resume_data = ctx.session.state.get("resume_content", {})
        
        if isinstance(resume_data, dict):
            resume_content = resume_data.get("markdown_content", "")
        else:
            resume_content = str(resume_data)
        
        print(f"📋 [{self.name}] Validating Markdown/HTML formatting...")
        
        # Perform formatting checks
        report = {
            "validation_status": "PASSED",
            "html_check": self._check_html(resume_content),
            "structure_check": self._check_structure(resume_content),
            "content_check": self._check_content(resume_content),
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Determine overall status
        if report["html_check"]["errors"] or report["structure_check"]["errors"]:
            report["validation_status"] = "FAILED"
        elif report["html_check"]["warnings"] or report["content_check"]["issues"]:
            report["validation_status"] = "PASSED_WITH_WARNINGS"
        
        # Store in session state
        ctx.session.state["formatting_report"] = report
        
        status_symbol = "✅" if report["validation_status"] == "PASSED" else "⚠️" if "WARNING" in report["validation_status"] else "❌"
        print(f"{status_symbol} [{self.name}] Formatting check: {report['validation_status']}")
        
        # Yield a completion event
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=None
        )
    
    def _check_html(self, content: str) -> Dict[str, Any]:
        """Check HTML/CSS syntax"""
        errors = []
        warnings = []
        
        # Check for style tag
        if '<style>' not in content:
            warnings.append("Missing <style> tag for CSS styling")
        
        # Check for resume container
        if 'resume-container' not in content:
            warnings.append("Missing main resume-container div")
        
        # Check for matching div tags
        open_divs = content.count('<div')
        close_divs = content.count('</div>')
        if open_divs != close_divs:
            errors.append(f"Unmatched div tags: {open_divs} open, {close_divs} close")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _check_structure(self, content: str) -> Dict[str, Any]:
        """Check document structure"""
        errors = []
        warnings = []
        sections_found = []
        
        # Check for key resume sections
        if 'Professional Summary' not in content and 'Summary' not in content:
            warnings.append("Missing Professional Summary section")
        else:
            sections_found.append("Summary")
        
        if 'Work Experience' not in content and 'Experience' not in content:
            warnings.append("Missing Work Experience section")
        else:
            sections_found.append("Experience")
        
        if 'Skills' not in content and 'Technical Skills' not in content:
            warnings.append("Missing Skills section")
        else:
            sections_found.append("Skills")
        
        if 'Education' not in content:
            warnings.append("Missing Education section")
        else:
            sections_found.append("Education")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sections_found": sections_found
        }
    
    def _check_content(self, content: str) -> Dict[str, Any]:
        """Check content quality"""
        issues = []
        suggestions = []
        
        # Check for placeholder text
        placeholders = ['FIRST NAME', 'LAST NAME', 'email@example.com', 'Company Name']
        for placeholder in placeholders:
            if placeholder in content:
                issues.append(f"Placeholder text found: {placeholder}")
        
        # Check word count
        word_count = len(content.split())
        if word_count < 200:
            suggestions.append("Resume content seems short - consider adding more details")
        elif word_count > 1000:
            suggestions.append("Resume content is long - consider condensing")
        
        return {
            "issues": issues,
            "suggestions": suggestions
        }
