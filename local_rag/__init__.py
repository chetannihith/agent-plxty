"""
Local RAG Implementation
Replaces Google Cloud VertexAI RAG with local ChromaDB

This module provides:
- LocalVectorStore: ChromaDB wrapper for vector storage
- DocumentProcessor: PDF text extraction and chunking
- LocalRagRetrieval: Google ADK tool for retrieval
- save_uploaded_file: File upload handler
"""

from .vector_store import LocalVectorStore, get_vector_store
from .document_processor import DocumentProcessor, save_uploaded_file
from .adk_tool import LocalRagRetrieval, get_local_rag_tool

__all__ = [
    'LocalVectorStore',
    'get_vector_store',
    'DocumentProcessor',
    'save_uploaded_file',
    'LocalRagRetrieval',
    'get_local_rag_tool'
]
