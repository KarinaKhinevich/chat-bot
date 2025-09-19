"""Tools for RAG agent document retrieval."""

import logging
from typing import List

from langchain_core.tools import tool

from chat_bot.database import pg_engine
from chat_bot.services.pg_document_service import PGDocumentService

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Document retriever for vector search."""

    def __init__(self):
        """Initialize the document retriever."""
        self.pg_document_service = PGDocumentService(pg_engine)

    async def get_relevant_documents(self, query: str, k: int = 5) -> List[dict]:
        """
        Retrieve relevant documents from vector store.

        Args:
            query: Search query
            k: Number of documents to retrieve

        Returns:
            List of documents with content and metadata
        """
        try:
            vectorstore = await self.pg_document_service.init_pgvector()
            docs = await vectorstore.asimilarity_search(query, k=k)

            results = []
            for doc in docs:
                results.append({"content": doc.page_content, "metadata": doc.metadata})

            logger.info(f"Retrieved {len(results)} documents for query: {query}...")
            return results

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []


@tool("retrieve_documents")
async def retrieve_documents(query: str, k: int = 5) -> dict:
    """
    Retrieve documents related to a query from the vector store.

    Args:
        query: A query string to search for
        k: Number of documents to retrieve (default: 5)

    Returns:
        Dict with documents list
    """
    retriever = DocumentRetriever()
    documents = await retriever.get_relevant_documents(query, k)

    if not documents:
        return {"documents": []}

    content = [doc["content"] for doc in documents]

    return {
        "documents": content,
    }
