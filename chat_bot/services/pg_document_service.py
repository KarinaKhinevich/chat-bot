"""
Document service for async database operations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from chat_bot.core import DocumentTypeEnum
from chat_bot.models import Document
from chat_bot.schemas import DocumentUploadResponse
from langchain_postgres import PGEngine, PGVectorStore
from langchain_core.documents import Document
from chat_bot.document_processing import DocumentChunker
from chat_bot.config import OpenAISettings, ChunkingSettings, DBSettings
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings

# Initialize settings
openai_settings = OpenAISettings()
chunking_settings = ChunkingSettings()
db_settings = DBSettings()

logger = logging.getLogger(__name__)


class PGDocumentService:
    """Service class for async vector document operations."""

    def __init__(self, db: AsyncSession, pg_engine: PGEngine):
        try:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=openai_settings.API_KEY,
                model=chunking_settings.MODEL_NAME
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {str(e)}")
            raise

        self.chunker = DocumentChunker(self._embeddings)
        self.pg_engine = pg_engine
        self.db = db

    async def init_pgvector(self) -> PGVectorStore:
        return await PGVectorStore.create(
            engine=self.pg_engine,
            table_name=db_settings.VECTOR_TABLE_NAME,
            embedding_service=self._embeddings,
        )
    async def create_document(
        self, page_content: str,  metadata: Dict[str, Union[str, int, Any]]
    ):
        """
        Create a new document in the vector table in the database.

        Args:
            page_content: The content of the document
            metadata: Metadata to attach to the document

        Raises:
            HTTPException: If document creation fails
        """
        documents = self.chunker.index_document(page_content, metadata)
        try:
            vectorstore = await self.init_pgvector()
            await vectorstore.aadd_documents(documents=documents)
            logger.info(f"Document added to vector store with {len(documents)} chunks.")

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to save document to database: {str(e)}"
            )

    
