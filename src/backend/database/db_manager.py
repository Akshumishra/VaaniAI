import logging
import numpy as np
from typing import List
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from src.backend.core.setting import Settings
from src.backend.database.models import Base, DocumentChunk
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(Settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self._init_db()

    def _init_db(self):
        """Initializes the database schema and extensions using SQLAlchemy."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS file_hash TEXT DEFAULT '';"
                        )
                    )
                except Exception:
                    pass
                conn.commit()

            Base.metadata.create_all(bind=self.engine)
            logger.info(
                "PostgreSQL, pgvector, and SQLAlchemy initialized successfully."
            )
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def save_chunks(
        self,
        metadata_list: List[dict],
        chunks: List[str],
        embeddings: np.ndarray,
        file_hash: str,
    ):
        """Saves the new chunks and their embeddings using ORM."""
        with self.SessionLocal() as session:
            try:
                db_chunks = [
                    DocumentChunk(
                        document_name=meta.get("document_name"),
                        file_hash=file_hash,
                        page_number=meta.get("page_number"),
                        chunk_text=chunk,
                        embedding=emb,
                    )
                    for meta, chunk, emb in zip(metadata_list, chunks, embeddings)
                ]
                session.add_all(db_chunks)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to save chunks: {e}")
                raise

    def check_document_exists(self, file_hash: str) -> bool:
        """Checks if a document with the given hash already exists."""
        with self.SessionLocal() as session:
            try:
                return (
                    session.query(DocumentChunk)
                    .filter(DocumentChunk.file_hash == file_hash)
                    .first()
                    is not None
                )
            except Exception as e:
                logger.error(f"Failed to check document existence: {e}")
                return False

    def search_chunks(
        self, query: str, query_embedding: np.ndarray, top_k: int, file_hash: str
    ) -> List[dict]:
        """Searches the database for chunks closest to the query using Hybrid Search (Vector + FTS)."""
        with self.SessionLocal() as session:
            try:
                vector_results = (
                    session.query(DocumentChunk)
                    .filter(DocumentChunk.file_hash == file_hash)
                    .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
                    .limit(10)
                    .all()
                )

                ts_query = func.plainto_tsquery("english", query)
                ts_vector = func.to_tsvector("english", DocumentChunk.chunk_text)

                lexical_results = (
                    session.query(DocumentChunk)
                    .filter(
                        DocumentChunk.file_hash == file_hash,
                        ts_vector.op("@@")(ts_query),
                    )
                    .order_by(func.ts_rank(ts_vector, ts_query).desc())
                    .limit(10)
                    .all()
                )

                k_rrf = 60
                scores = {}
                chunks_map = {}

                for rank, chunk in enumerate(vector_results):
                    scores[chunk.id] = 1.0 / (k_rrf + rank + 1)
                    chunks_map[chunk.id] = chunk

                for rank, chunk in enumerate(lexical_results):
                    if chunk.id in scores:
                        scores[chunk.id] += 1.0 / (k_rrf + rank + 1)
                    else:
                        scores[chunk.id] = 1.0 / (k_rrf + rank + 1)
                        chunks_map[chunk.id] = chunk

                sorted_chunk_ids = sorted(
                    scores.items(), key=lambda item: item[1], reverse=True
                )
                top_results = [
                    chunks_map[chunk_id]
                    for chunk_id, _score in sorted_chunk_ids[:top_k]
                ]

                return [
                    {
                        "text": row.chunk_text,
                        "source": row.document_name,
                        "page": row.page_number,
                    }
                    for row in top_results
                ]
            except Exception as e:
                logger.error(f"Failed to search chunks: {e}")
                return []


db_manager = DatabaseManager()
