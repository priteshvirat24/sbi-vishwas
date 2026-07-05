"""
SBI Vishwas — Knowledge Ingestion Pipeline

Chunks, embeds, and stores policy documents into the Qdrant vector store.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http import models as rest

from src.agents.providers.provider_factory import ProviderFactory
from src.database.engine import get_transactional_session
from src.database.models.domain import KnowledgeEntry
from src.database.vector_store import POLICIES_COLLECTION, vector_store

logger = structlog.get_logger(__name__)


class KnowledgeIngestionPipeline:
    """Pipeline for processing and embedding policy documents."""

    def __init__(self):
        # RBI policies need specific chunking to not break mid-clause
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""],
        )

    async def process_entry(self, entry: KnowledgeEntry) -> bool:
        """Process a single knowledge entry: chunk, embed, and store."""
        try:
            logger.info("Processing knowledge entry", entry_id=str(entry.id), title=entry.title)

            # 1. Chunk document
            text_chunks = self.text_splitter.split_text(entry.content)
            
            if not text_chunks:
                logger.warning("No chunks generated for entry", entry_id=str(entry.id))
                return False

            # 2. Embed chunks
            embeddings_model = ProviderFactory.get_embedding_model()
            embeddings = await embeddings_model.aembed_documents(text_chunks)

            if len(embeddings) != len(text_chunks):
                raise ValueError("Mismatch between chunks and embeddings count")

            # 3. Prepare Qdrant points
            points = []
            embedding_ids = []
            
            for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
                point_id = str(uuid.uuid4())
                embedding_ids.append(point_id)
                
                payload = {
                    "entry_id": str(entry.id),
                    "title": entry.title,
                    "category": entry.category,
                    "source_type": entry.source_type,
                    "chunk_index": i,
                    "text": chunk,
                    "tags": entry.tags or [],
                }
                
                points.append(
                    rest.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                )

            # 4. Store in Qdrant
            success = await vector_store.upsert_vectors(POLICIES_COLLECTION, points)
            
            if not success:
                raise Exception("Failed to upsert to Qdrant")

            # 5. Update database record
            async with get_transactional_session() as session:
                db_entry = await session.get(KnowledgeEntry, entry.id)
                if db_entry:
                    db_entry.is_embedded = True
                    db_entry.embedding_ids = embedding_ids
                    db_entry.chunk_count = len(text_chunks)
                    from datetime import datetime, timezone
                    db_entry.last_embedded_at = datetime.now(timezone.utc)
                    
            logger.info("Successfully ingested knowledge entry", entry_id=str(entry.id), chunks=len(text_chunks))
            return True

        except Exception as e:
            logger.error("Knowledge ingestion failed", entry_id=str(entry.id), error=str(e))
            return False

    async def process_unembedded_entries(self) -> int:
        """Find and process all knowledge entries that haven't been embedded yet."""
        from sqlalchemy import select
        
        processed_count = 0
        async with get_transactional_session() as session:
            result = await session.execute(
                select(KnowledgeEntry).where(KnowledgeEntry.is_embedded == False)
            )
            entries = result.scalars().all()
            
        for entry in entries:
            success = await self.process_entry(entry)
            if success:
                processed_count += 1
                
        return processed_count
