"""
Document Processing for Local RAG
Handles PDF parsing, text extraction, and chunking
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import hashlib
import PyPDF2
from io import BytesIO


class DocumentProcessor:
    """Process documents (PDFs) for vector storage"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_file: File object or path to PDF
            
        Returns:
            Extracted text
        """
        try:
            # Handle both file paths and file objects
            if isinstance(pdf_file, (str, Path)):
                with open(pdf_file, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            else:
                # File object (e.g., from Streamlit upload)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            return ""
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > self.chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        
        return [c for c in chunks if c]  # Filter empty chunks
    
    def process_pdf(
        self, 
        pdf_file, 
        filename: str,
        additional_metadata: Dict[str, Any] = None
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Process a PDF file into chunks with metadata
        
        Args:
            pdf_file: PDF file object or path
            filename: Name of the file
            additional_metadata: Extra metadata to attach
            
        Returns:
            Tuple of (chunks, metadata_list)
        """
        # Extract text
        text = self.extract_text_from_pdf(pdf_file)
        
        if not text:
            print(f"⚠️ No text extracted from {filename}")
            return [], []
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        # Create metadata for each chunk
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadata = {
                'filename': filename,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'source': 'pdf',
                'text_length': len(chunk)
            }
            
            # Add additional metadata
            if additional_metadata:
                metadata.update(additional_metadata)
            
            metadatas.append(metadata)
        
        print(f"✅ Processed {filename}: {len(chunks)} chunks from {len(text)} characters")
        return chunks, metadatas
    
    def process_multiple_pdfs(
        self,
        pdf_files: List,
        filenames: List[str]
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Process multiple PDF files
        
        Args:
            pdf_files: List of PDF file objects
            filenames: List of filenames
            
        Returns:
            Tuple of (all_chunks, all_metadata)
        """
        all_chunks = []
        all_metadata = []
        
        for pdf_file, filename in zip(pdf_files, filenames):
            chunks, metadata = self.process_pdf(pdf_file, filename)
            all_chunks.extend(chunks)
            all_metadata.extend(metadata)
        
        return all_chunks, all_metadata


def save_uploaded_file(uploaded_file, upload_dir: str = "./data/uploads") -> str:
    """
    Save an uploaded file to local storage
    
    Args:
        uploaded_file: Streamlit uploaded file object
        upload_dir: Directory to save files
        
    Returns:
        Path to saved file
    """
    try:
        # Create upload directory if it doesn't exist
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_filename = "".join(c if c.isalnum() or c in ['.', '_', '-', ' '] else '_' for c in uploaded_file.name)
        
        # Generate unique filename if file already exists
        file_path = Path(upload_dir) / safe_filename
        counter = 1
        while file_path.exists():
            name, ext = os.path.splitext(safe_filename)
            file_path = Path(upload_dir) / f"{name}_{counter}{ext}"
            counter += 1
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        print(f"✅ Saved {safe_filename} to {file_path}")
        return str(file_path)
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        raise
