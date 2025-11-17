"""
Resume Optimization Workflow Orchestrator

6-stage pipeline with sequential and parallel execution:
- Stage 1: Job Description Extraction (Sequential)
- Stage 2: Profile Analysis (3 Parallel Agents)
- Stage 3: Content Alignment (Sequential)
- Stage 4: ATS Optimization (2 Parallel Agents)
- Stage 5: LaTeX Generation (Sequential)
- Stage 6: Quality Assurance (2 Parallel Agents)
"""
from google.adk.agents import SequentialAgent, ParallelAgent
from typing import Dict, Any

from ..agents.job_description_extractor import JobDescriptionExtractorCrew
from ..agents.profile_rag_agent import ProfileRAGAgent
from ..agents.skills_matcher_agent import create_skills_matcher_agent
from ..agents.experience_relevance_agent import create_experience_relevance_agent
from ..agents.content_alignment_agent import create_content_alignment_agent
from ..agents.ats_optimizer_agent import create_ats_optimizer_agent
from ..agents.keyword_enhancer_agent import create_keyword_enhancer_agent
from ..agents.markdown_formatter_agent import create_markdown_formatter_agent
from ..agents.quality_validator_agent import create_quality_validator_agent
from ..agents.formatting_checker_agent import FormattingCheckerAgent


class ResumeOptimizerWorkflow:
    """
    Main workflow orchestrator using Google ADK SequentialAgent + ParallelAgent
    
    Implements 6-stage pipeline with 10 agents:
    - 1 CrewAI agent (Stage 1)
    - 9 Google ADK agents (Stages 2-6)
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        vector_store_path: str = "./data/vector_db"
    ):
        """
        Initialize workflow with all agents
        
        Args:
            model: LLM model to use for agents
            vector_store_path: Path to ChromaDB vector store
        """
        self.model = model
        self.vector_store_path = vector_store_path
        
        # Initialize all agents
        self._init_agents()
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _init_agents(self):
        """Initialize all 10 agents"""
        
        # Stage 1: Job Description Extraction (CrewAI)
        self.job_extractor = JobDescriptionExtractorCrew()
        
        # Stage 2: Profile Analysis (3 Parallel Google ADK Agents)
        self.profile_rag = ProfileRAGAgent(
            name="profile_rag_agent"
        )
        self.skills_matcher = create_skills_matcher_agent(model=self.model)
        self.experience_relevance = create_experience_relevance_agent(model=self.model)
        
        # Stage 3: Content Alignment (Sequential)
        self.content_alignment = create_content_alignment_agent(model=self.model)
        
        # Stage 4: ATS Optimization (2 Parallel)
        self.ats_optimizer = create_ats_optimizer_agent(model=self.model)
        self.keyword_enhancer = create_keyword_enhancer_agent(model=self.model)
        
        # Stage 5: LaTeX Generation (Sequential)
        self.markdown_formatter = create_markdown_formatter_agent(model=self.model)
        
        # Stage 6: Quality Assurance (2 Parallel)
        self.quality_validator = create_quality_validator_agent(model=self.model)
        self.formatting_checker = FormattingCheckerAgent()
    
    def _build_workflow(self) -> SequentialAgent:
        """
        Build 6-stage sequential workflow with parallel stages
        
        Workflow structure:
        1. [Sequential] Job Description Extraction
        2. [Parallel]   Profile RAG + Skills Matcher + Experience Relevance
        3. [Sequential] Content Alignment
        4. [Parallel]   ATS Optimizer + Keyword Enhancer
        5. [Sequential] LaTeX Formatter
        6. [Parallel]   Quality Validator + Formatting Checker
        """
        
        # Stage 2: Parallel profile analysis
        stage2_parallel = ParallelAgent(
            name="profile_analysis_stage",
            sub_agents=[
                self.profile_rag,
                self.skills_matcher,
                self.experience_relevance
            ]
        )
        
        # Stage 4: Parallel ATS optimization
        stage4_parallel = ParallelAgent(
            name="ats_optimization_stage",
            sub_agents=[
                self.ats_optimizer,
                self.keyword_enhancer
            ]
        )
        
        # Stage 6: Parallel quality assurance
        stage6_parallel = ParallelAgent(
            name="quality_assurance_stage",
            sub_agents=[
                self.quality_validator,
                self.formatting_checker
            ]
        )
        
        # Main sequential workflow
        workflow = SequentialAgent(
            name="resume_optimizer_workflow",
            sub_agents=[
                # Note: CrewAI agent needs A2A wrapper (see a2a_bridge.py)
                # For now, we'll call it separately in run_workflow()
                
                stage2_parallel,        # Stage 2
                self.content_alignment,  # Stage 3
                stage4_parallel,        # Stage 4
                self.markdown_formatter,   # Stage 5
                stage6_parallel         # Stage 6
            ]
        )
        
        return workflow
    
    async def run_workflow(
        self,
        ctx,
        job_url: str,
        resume_path: str
    ) -> Dict[str, Any]:
        """
        Execute the complete 6-stage workflow
        
        Args:
            ctx: Google ADK context object
            job_url: URL of job posting to scrape
            resume_path: Path to user's resume file
        
        Returns:
            Dict with workflow results including:
            - latex_content: Generated LaTeX resume
            - ats_analysis: ATS score and recommendations
            - quality_report: Quality validation report
            - formatting_report: Formatting validation report
        """
        
        print("🚀 Starting Resume Optimization Workflow")
        print("=" * 60)
        
        # Stage 1: Job Description Extraction (CrewAI - called separately)
        print("\n📥 Stage 1: Job Description Extraction")
        job_data = self.job_extractor.extract_job_description(job_url)
        ctx.session.state["job_description"] = job_data
        print(f"✅ Extracted job: {job_data.get('title', 'N/A')}")
        
        # Initialize resume data in state
        ctx.session.state["resume_path"] = resume_path
        
        # Stages 2-6: Execute Google ADK workflow
        print("\n🔄 Executing Stages 2-6...")
        result = await self.workflow.run_async(ctx)
        
        # Collect final results
        final_results = {
            "job_description": ctx.session.state.get("job_description", {}),
            "profile_data": ctx.session.state.get("profile_data", {}),
            "skills_analysis": ctx.session.state.get("skills_analysis", {}),
            "experience_scores": ctx.session.state.get("experience_scores", {}),
            "aligned_data": ctx.session.state.get("aligned_data", {}),
            "ats_analysis": ctx.session.state.get("ats_analysis", {}),
            "keyword_enhancements": ctx.session.state.get("keyword_enhancements", {}),
            "latex_content": ctx.session.state.get("latex_content", {}),
            "quality_report": ctx.session.state.get("quality_report", {}),
            "formatting_report": ctx.session.state.get("formatting_report", {})
        }
        
        print("\n" + "=" * 60)
        print("✅ Workflow Complete!")
        
        # Print summary
        ats_score = final_results["ats_analysis"].get("ats_score", {}).get("total_score", 0)
        quality_score = final_results["quality_report"].get("overall_quality_score", 0)
        
        print(f"\n📊 Final Scores:")
        print(f"   ATS Score: {ats_score}/100")
        print(f"   Quality Score: {quality_score}/100")
        
        validation_status = final_results["quality_report"].get("validation_status", "UNKNOWN")
        print(f"   Status: {validation_status}")
        
        return final_results
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of workflow configuration"""
        return {
            "total_agents": 10,
            "stages": 6,
            "parallel_stages": 3,
            "sequential_stages": 3,
            "agent_breakdown": {
                "crewai_agents": 1,
                "google_adk_agents": 9
            },
            "stage_details": [
                {
                    "stage": 1,
                    "type": "sequential",
                    "agents": ["JobDescriptionExtractor (CrewAI)"]
                },
                {
                    "stage": 2,
                    "type": "parallel",
                    "agents": ["ProfileRAG", "SkillsMatcher", "ExperienceRelevance"]
                },
                {
                    "stage": 3,
                    "type": "sequential",
                    "agents": ["ContentAlignment"]
                },
                {
                    "stage": 4,
                    "type": "parallel",
                    "agents": ["ATSOptimizer", "KeywordEnhancer"]
                },
                {
                    "stage": 5,
                    "type": "sequential",
                    "agents": ["LaTeXFormatter"]
                },
                {
                    "stage": 6,
                    "type": "parallel",
                    "agents": ["QualityValidator", "FormattingChecker"]
                }
            ]
        }
