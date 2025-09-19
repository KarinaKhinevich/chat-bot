"""Chat service for question answering using RAG agent."""

import logging
from typing import List, Tuple

from .openai_service import RAGAgent

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat questions using RAG agent."""

    def __init__(self):
        """Initialize the chat service with RAG agent."""
        self.rag_agent = RAGAgent(streaming_mode=False)

    async def ask_question(self, question: str, k: int = 5) -> Tuple[str, List[str]]:
        """
        Answer a question using the RAG agent pipeline.

        This method uses a complete RAG pipeline that includes:
        1. Content moderation
        2. Document retrieval from vector store
        3. Relevance checking
        4. Answer generation

        Args:
            question: The user's question
            k: Number of documents to retrieve (default: 5)

        Returns:
            tuple: (answer, list of source document filenames)

        Raises:
            Exception: If there's an error during the process
        """
        try:
            # Process the question through the RAG agent
            result = await self.rag_agent.invoke_agent(question, retrieval_k=k)

            # Extract answer and sources from the result
            answer = result.get(
                "answer", "I'm sorry, I couldn't generate an answer to your question."
            )
            sources = result.get("sources", [])

            # Log the interaction
            moderated = result.get("moderated", False)
            is_relevant = result.get("is_relevant", False)
            relevance_score = result.get("relevance_score", 0.0)

            logger.info(
                f"RAG pipeline completed: moderated={moderated}, relevant={is_relevant}, score={relevance_score}"
            )

            # Filter out duplicate sources
            unique_sources = list(set(sources)) if sources else []

            return answer, unique_sources

        except Exception as e:
            logger.error(f"Error in RAG chat service: {str(e)}")
            raise Exception(f"Failed to process question: {str(e)}")
