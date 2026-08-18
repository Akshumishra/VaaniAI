import logging
import numpy as np
from typing import List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.backend.core.setting import Settings
from src.backend.database.models import Base, DocumentChunk
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        # SQLAlchemy handles postgresql:// just fine using psycopg2 by default.
        self.engine = create_engine(Settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._init_db()

    def _init_db(self):
        """Initializes the database schema and extensions using SQLAlchemy."""
        try:
            # We must create the vector extension before Base.metadata.create_all
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                
            Base.metadata.create_all(bind=self.engine)
            logger.info("PostgreSQL, pgvector, and SQLAlchemy initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def save_chunks(self, metadata_list: List[dict], chunks: List[str], embeddings: np.ndarray):
        """Truncates old chunks and saves the new chunks and their embeddings using ORM."""
        with self.SessionLocal() as session:
            try:
                # Clear existing chunks for this simple implementation
                session.query(DocumentChunk).delete()
                
                # Bulk insert new chunks
                db_chunks = [
                    DocumentChunk(
                        document_name=meta.get("document_name"),
                        page_number=meta.get("page_number"),
                        chunk_text=chunk, 
                        embedding=emb
                    )
                    for meta, chunk, emb in zip(metadata_list, chunks, embeddings)
                ]
                session.add_all(db_chunks)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to save chunks: {e}")
                raise

    def search_chunks(self, query_embedding: np.ndarray, top_k: int) -> List[dict]:
        """Searches the database for chunks closest to the query embedding using ORM."""
        with self.SessionLocal() as session:
            try:
                # Use pgvector's cosine_distance operator via SQLAlchemy
                results = session.query(DocumentChunk).order_by(
                    DocumentChunk.embedding.cosine_distance(query_embedding)
                ).limit(top_k).all()
                
                return [
                    {
                        "text": row.chunk_text,
                        "source": row.document_name,
                        "page": row.page_number
                    } 
                    for row in results
                ]
            except Exception as e:
                logger.error(f"Failed to search chunks: {e}")
                return []

db_manager = DatabaseManager()
