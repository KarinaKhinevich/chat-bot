"""
Document service for async database operations.
"""

import logging
from typing import Any, Dict, Union

from fastapi import HTTPException
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from chat_bot.config import ChunkingSettings, DBSettings, OpenAISettings
from chat_bot.database import engine
from chat_bot.document_processing import DocumentChunker

# Initialize settings
openai_settings = OpenAISettings()
chunking_settings = ChunkingSettings()
db_settings = DBSettings()

logger = logging.getLogger(__name__)


class PGDocumentService:
    """Service class for async vector document operations."""

    def __init__(self, pg_engine: PGEngine):
        try:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=openai_settings.API_KEY,
                model=chunking_settings.MODEL_NAME,
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {str(e)}")
            raise

        self.chunker = DocumentChunker(self._embeddings)
        self.pg_engine = pg_engine

    async def init_pgvector(self) -> PGVectorStore:
        return await PGVectorStore.create(
            engine=self.pg_engine,
            table_name=db_settings.VECTOR_TABLE_NAME,
            embedding_service=self._embeddings,
        )

    async def create_document(
        self, page_content: str, metadata: Dict[str, Union[str, int, Any]]
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
            logger.error(f"Failed to save document to vector database: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to save document to database: {str(e)}"
            )

    async def delete_document(self, id: str):
        """
        Delete a document from the vector table in the database.

         Args:
             id: The ID of the document to delete

         Raises:
             HTTPException: If document deletion fails
        """
        try:
            vectorstore = await self.init_pgvector()
            await vectorstore.adelete(ids=[id])
            logger.info(f"Document deleted from vector store with ID: {id}")

        except Exception as e:
            logger.error(f"Failed to delete document from vector database: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document from database: {str(e)}",
            )

    async def delete_document_by_metadata(self, document_id: str):
        """
        Delete all document chunks from the vector table by document ID stored in metadata.

         Args:
             document_id: The document ID stored in metadata to filter chunks

         Returns:
             int: Number of deleted chunks

         Raises:
             HTTPException: If document deletion fails
        """
        try:
            table_name = db_settings.VECTOR_TABLE_NAME

            async with engine.begin() as conn:
                delete_query = text(
                    f"""
                    DELETE FROM {table_name} 
                    WHERE langchain_metadata->>'document_id' = :document_id
                """
                )

                result = await conn.execute(delete_query, {"document_id": document_id})
                deleted_count = result.rowcount

                logger.info(
                    f"Deleted {deleted_count} vector chunks for document ID: {document_id}"
                )
                return deleted_count

        except Exception as e:
            logger.error(
                f"Failed to delete document chunks from vector store: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document chunks from vector store: {str(e)}",
            )
