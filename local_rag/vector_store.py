"""
Local Vector Store Implementation using ChromaDB
Replaces VertexAI RAG with local storage
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import hashlib
from pathlib import Path


class LocalVectorStore:
    """Local vector database using ChromaDB for resume indexing"""
    
    def __init__(self, persist_directory: str = "./data/vector_db"):
        """
        Initialize ChromaDB client with local persistence
        
        Args:
            persist_directory: Path to store vector database
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
    def get_or_create_collection(self, collection_name: str = "resumes"):
        """
        Get or create a ChromaDB collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection
        """
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Resume documents collection"}
            )
            return collection
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    def add_documents(
        self, 
        documents: List[str], 
        metadatas: List[Dict[str, Any]], 
        collection_name: str = "resumes"
    ) -> bool:
        """
        Add documents to the vector store
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts for each document
            collection_name: Name of collection to add to
            
        Returns:
            Success status
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate unique IDs for documents
            ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]
            
            # Add documents to collection
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added {len(documents)} documents to collection '{collection_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False
    
    def query(
        self, 
        query_text: str, 
        n_results: int = 10, 
        collection_name: str = "resumes",
        min_similarity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Query the vector store
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            collection_name: Name of collection to query
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            Query results with documents and metadata
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Filter by similarity threshold (ChromaDB returns distances, lower is better)
            # Convert distance to similarity (1 - normalized_distance)
            filtered_results = {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'ids': []
            }
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance, doc_id) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0],
                    results['ids'][0]
                )):
                    # ChromaDB uses L2 distance, convert to similarity
                    similarity = 1 / (1 + distance)
                    
                    if similarity >= min_similarity:
                        filtered_results['documents'].append(doc)
                        filtered_results['metadatas'].append(metadata)
                        filtered_results['distances'].append(distance)
                        filtered_results['ids'].append(doc_id)
            
            print(f"✅ Found {len(filtered_results['documents'])} results above similarity threshold {min_similarity}")
            return filtered_results
            
        except Exception as e:
            print(f"❌ Error querying: {e}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
    
    def delete_collection(self, collection_name: str = "resumes") -> bool:
        """
        Delete a collection
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            Success status
        """
        try:
            self.client.delete_collection(name=collection_name)
            print(f"✅ Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all collections
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            print(f"❌ Error listing collections: {e}")
            return []
    
    def get_collection_count(self, collection_name: str = "resumes") -> int:
        """
        Get number of documents in collection
        
        Args:
            collection_name: Name of collection
            
        Returns:
            Document count
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()
        except Exception as e:
            print(f"❌ Error getting count: {e}")
            return 0


# Singleton instance
_vector_store_instance = None

def get_vector_store(persist_directory: str = "./data/vector_db") -> LocalVectorStore:
    """
    Get singleton instance of LocalVectorStore
    
    Args:
        persist_directory: Path to store vector database
        
    Returns:
        LocalVectorStore instance
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = LocalVectorStore(persist_directory)
    return _vector_store_instance
