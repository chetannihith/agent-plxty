"""
Stage 2: Profile RAG Agent (Parallel Agent 1)
Retrieves relevant profile data from vector database
"""
from google.adk.agents import BaseAgent
from typing import Any, Dict
from local_rag import get_vector_store


class ProfileRAGAgent(BaseAgent):
    """
    Agent 2: RAG-based profile retrieval
    Runs in parallel with SkillsMatcherAgent and ExperienceRelevanceAgent
    """
    
    def __init__(self, name: str = "profile_rag_agent"):
        super().__init__(name=name)
    
    async def _run_async_impl(self, ctx):
        """
        Google ADK BaseAgent execution method
        
        Retrieves relevant profile sections based on job requirements
        """
        
        # Get vector store (singleton pattern)
        vector_store = get_vector_store()
        
        # Get job data from session state
        job_data = ctx.session.state.get("job_data", {})
        profile_id = ctx.session.state.get("profile_id", "")
        
        # Extract job requirements for query
        required_skills = job_data.get("required_skills", [])
        keywords = job_data.get("keywords", [])
        job_title = job_data.get("job_title", "")
        
        # Build search query
        query = f"{job_title} {' '.join(required_skills[:10])} {' '.join(keywords[:10])}"
        
        print(f"🔍 [{self.name}] Querying vector store for relevant profile data...")
        
        # Query vector database
        try:
            # Use the collection name from session state or default to "user_profile"
            collection_name = ctx.session.state.get("profile_id", "user_profile")
            results = vector_store.query(
                query_text=query,
                n_results=15,
                collection_name=collection_name,
                min_similarity=0.3
            )
            
            # Organize retrieved data
            profile_data = {
                "relevant_sections": [],
                "similarity_scores": [],
                "metadata": []
            }
            
            if results.get('documents'):
                for doc, metadata, distance in zip(
                    results.get('documents', []),
                    results.get('metadatas', []),
                    results.get('distances', [])
                ):
                    profile_data["relevant_sections"].append(doc)
                    profile_data["similarity_scores"].append(1 / (1 + distance))
                    profile_data["metadata"].append(metadata)
            
            # Store in session state
            ctx.session.state["profile_data"] = profile_data
            
            print(f"✅ [{self.name}] Retrieved {len(profile_data['relevant_sections'])} relevant sections")
            
            # Debug: Show sample of retrieved content
            if profile_data['relevant_sections']:
                print(f"📄 Sample section 1: {profile_data['relevant_sections'][0][:150]}...")
                if len(profile_data['relevant_sections']) > 1:
                    print(f"📄 Sample section 2: {profile_data['relevant_sections'][1][:150]}...")
            
            # Yield a completion event
            from google.adk.events import Event
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                content=None
            )
            
        except Exception as e:
            print(f"❌ [{self.name}] Error: {e}")
            ctx.session.state["profile_data"] = {
                "relevant_sections": [],
                "error": str(e)
            }
            
            # Yield error event
            from google.adk.events import Event
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                content=None
            )
