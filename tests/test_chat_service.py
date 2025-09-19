"""Tests for chat service functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from chat_bot.services.chat_service import ChatService


class TestChatService:
    """Test cases for the ChatService class."""

    @pytest.mark.unit
    def test_chat_service_initialization(self):
        """Test ChatService initialization."""
        with patch('chat_bot.services.chat_service.RAGAgent'):
            service = ChatService()
            assert service.rag_agent is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ask_question_success(self):
        """Test successful question asking."""
        # Mock the RAGAgent
        mock_rag_agent = AsyncMock()
        mock_result = {
            "answer": "This is a test answer",
            "sources": ["document1.pdf", "document2.txt"],
            "moderated": False,
            "is_relevant": True,
            "relevance_score": 0.85
        }
        mock_rag_agent.invoke_agent.return_value = mock_result

        with patch('chat_bot.services.chat_service.RAGAgent', return_value=mock_rag_agent):
            service = ChatService()
            
            answer, sources = await service.ask_question("What is this about?")
            
            assert answer == "This is a test answer"
            assert sources == ["document1.pdf", "document2.txt"]
            mock_rag_agent.invoke_agent.assert_called_once_with("What is this about?", retrieval_k=5)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ask_question_with_custom_k(self):
        """Test question asking with custom retrieval k parameter."""
        mock_rag_agent = AsyncMock()
        mock_result = {
            "answer": "Test answer",
            "sources": ["doc1.pdf"]
        }
        mock_rag_agent.invoke_agent.return_value = mock_result

        with patch('chat_bot.services.chat_service.RAGAgent', return_value=mock_rag_agent):
            service = ChatService()
            
            await service.ask_question("Test question", k=3)
            
            mock_rag_agent.invoke_agent.assert_called_once_with("Test question", retrieval_k=3)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ask_question_no_answer_fallback(self):
        """Test fallback when no answer is provided."""
        mock_rag_agent = AsyncMock()
        mock_result = {
            "sources": ["document1.pdf"]
            # No "answer" key
        }
        mock_rag_agent.invoke_agent.return_value = mock_result

        with patch('chat_bot.services.chat_service.RAGAgent', return_value=mock_rag_agent):
            service = ChatService()
            
            answer, sources = await service.ask_question("What is this?")
            
            assert answer == "I'm sorry, I couldn't generate an answer to your question."
            assert sources == ["document1.pdf"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ask_question_no_sources(self):
        """Test question asking when no sources are returned."""
        mock_rag_agent = AsyncMock()
        mock_result = {
            "answer": "Test answer"
            # No "sources" key
        }
        mock_rag_agent.invoke_agent.return_value = mock_result

        with patch('chat_bot.services.chat_service.RAGAgent', return_value=mock_rag_agent):
            service = ChatService()
            
            answer, sources = await service.ask_question("Test question")
            
            assert answer == "Test answer"
            assert sources == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ask_question_duplicate_sources(self):
        """Test that duplicate sources are filtered out."""
        mock_rag_agent = AsyncMock()
        mock_result = {
            "answer": "Test answer",
            "sources": ["doc1.pdf", "doc2.txt", "doc1.pdf", "doc2.txt"]  # Duplicates
        }
        mock_rag_agent.invoke_agent.return_value = mock_result

        with patch('chat_bot.services.chat_service.RAGAgent', return_value=mock_rag_agent):
            service = ChatService()
            
            answer, sources = await service.ask_question("Test question")
            
            assert answer == "Test answer"
            assert len(sources) == 2  # Duplicates removed
            assert "doc1.pdf" in sources
            assert "doc2.txt" in sources

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ask_question_rag_agent_error(self):
        """Test error handling when RAG agent fails."""
        mock_rag_agent = AsyncMock()
        mock_rag_agent.invoke_agent.side_effect = Exception("RAG agent failed")

        with patch('chat_bot.services.chat_service.RAGAgent', return_value=mock_rag_agent):
            service = ChatService()
            
            with pytest.raises(Exception) as exc_info:
                await service.ask_question("Test question")
            
            assert "Failed to process question" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ask_question_empty_question(self):
        """Test asking an empty question."""
        mock_rag_agent = AsyncMock()
        mock_result = {
            "answer": "Please provide a valid question",
            "sources": []
        }
        mock_rag_agent.invoke_agent.return_value = mock_result

        with patch('chat_bot.services.chat_service.RAGAgent', return_value=mock_rag_agent):
            service = ChatService()
            
            answer, sources = await service.ask_question("")
            
            # The service should still work, letting validation happen at API level
            mock_rag_agent.invoke_agent.assert_called_once_with("", retrieval_k=5)