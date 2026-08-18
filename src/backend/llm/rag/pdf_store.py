import os
import logging
from typing import List, Generator
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from src.backend.database.db_manager import db_manager

logger = logging.getLogger(__name__)

class PDFStore:
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        self.model_name = model_name
        logger.info(f"Loading SentenceTransformer model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        logger.info("SentenceTransformer model loaded successfully.")

    def add_pdf_generator(self, file_path: str) -> Generator[str, None, None]:
        yield "Extracting text from PDF...\n"
        filename = os.path.basename(file_path)
        
        all_chunks = []
        all_metadata = []
        
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if not page_text:
                    continue
                    
                # Chunk per page
                page_chunks = [c.strip() for c in page_text.split('\n\n') if c.strip()]
                
                # If page is dense, fallback to character chunking
                if len(page_chunks) < 2 and len(page_text) > 1000:
                    page_chunks = []
                    chunk_size = 500
                    for i in range(0, len(page_text), chunk_size):
                        page_chunks.append(page_text[i:i+chunk_size])
                
                for chunk in page_chunks:
                    all_chunks.append(chunk)
                    all_metadata.append({
                        "document_name": filename,
                        "page_number": page_num
                    })
                    
        except Exception as e:
            logger.exception("Failed to extract text from PDF")
            yield f"Error: Failed to extract text - {str(e)}\n"
            return

        if not all_chunks:
            yield "Error: No text found in PDF.\n"
            return

        yield "Generating embeddings and saving to Database (this might take a moment)...\n"
        
        try:
            # Generate embeddings (768 dimensions)
            chunk_embeddings = self.model.encode(all_chunks, convert_to_numpy=True)
            
            # Save to PostgreSQL via DB layer
            db_manager.save_chunks(all_metadata, all_chunks, chunk_embeddings)
            
            yield "Ready\n"
        except Exception as e:
            logger.exception("Failed to generate or save embeddings")
            yield f"Error: Failed to generate/save embeddings - {str(e)}\n"

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """
        Searches the PostgreSQL vector store for chunks most similar to the query.
        """
        
        try:
            # Embed the query
            query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
            
            # Search via DB layer
            results = db_manager.search_chunks(query_embedding, top_k)
            
            if not results:
                return ["No highly relevant information found in the document."]
                
            return results
        except Exception as e:
            logger.exception("Failed to search database")
            return [f"Database search error: {str(e)}"]

pdf_store = PDFStore()
