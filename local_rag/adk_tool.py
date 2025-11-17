"""
Local RAG Retrieval Tool for Google ADK
Replaces VertexAiRagRetrieval with local ChromaDB implementation
"""
from typing import Any, Dict, List
from local_rag import get_vector_store


# Global vector store instance
_vector_store = None


def get_local_rag_tool(
    collection_name: str = "resumes",
    similarity_top_k: int = 10,
    vector_distance_threshold: float = 0.5
):
    """
    Create a local RAG retrieval tool function for Google ADK
    
    Args:
        collection_name: ChromaDB collection name
        similarity_top_k: Number of results to return
        vector_distance_threshold: Minimum similarity threshold (0-1)
        
    Returns:
        A callable tool function compatible with Google ADK
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    
    def local_rag_retrieval(query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information from local vector database using semantic search.
        Use this tool to find resume information, candidate profiles, or job-related content.
        
        Args:
            query: The search query to find relevant documents
            
        Returns:
            List of relevant documents with content, metadata, and similarity scores
        """
        try:
            # Query the vector store
            results = _vector_store.query(
                query_text=query,
                n_results=similarity_top_k,
                collection_name=collection_name,
                min_similarity=vector_distance_threshold
            )
            
            # Format results for ADK agents
            formatted_results = []
            for doc, metadata, distance in zip(
                results.get('documents', []),
                results.get('metadatas', []),
                results.get('distances', [])
            ):
                formatted_results.append({
                    'content': doc,
                    'metadata': metadata,
                    'distance': distance,
                    'similarity': 1 / (1 + distance)  # Convert distance to similarity score
                })
            
            print(f"🔍 Retrieved {len(formatted_results)} documents for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error in retrieval: {e}")
            return []
    
    return local_rag_retrieval


# For backward compatibility, create a class wrapper
class LocalRagRetrieval:
    """
    Wrapper class for local RAG retrieval tool
    Compatible with Google ADK agent framework
    """
    
    def __init__(
        self,
        name: str = "local_rag_retrieval",
        description: str = "Retrieve relevant information from local vector database",
        collection_name: str = "resumes",
        similarity_top_k: int = 10,
        vector_distance_threshold: float = 0.5
    ):
        """
        Initialize local RAG retrieval tool
        
        Args:
            name: Tool name (for reference)
            description: Tool description (for reference)
            collection_name: ChromaDB collection name
            similarity_top_k: Number of results to return
            vector_distance_threshold: Minimum similarity threshold (0-1)
        """
        self.name = name
        self.description = description
        self.collection_name = collection_name
        self.similarity_top_k = similarity_top_k
        self.vector_distance_threshold = vector_distance_threshold
        self.tool_function = get_local_rag_tool(
            collection_name=collection_name,
            similarity_top_k=similarity_top_k,
            vector_distance_threshold=vector_distance_threshold
        )
    
    def __call__(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Execute retrieval query"""
        return self.tool_function(query)
    
    def get_tool_function(self):
        """Get the actual tool function for use with ADK agents"""
        return self.tool_function
