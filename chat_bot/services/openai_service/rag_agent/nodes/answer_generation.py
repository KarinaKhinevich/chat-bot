"""Answer generation node for RAG agent."""

import logging
from typing import Any, Dict

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langdetect import detect

from chat_bot.config import OpenAISettings

from ..state import State

logger = logging.getLogger(__name__)

openai_settings = OpenAISettings()


class AnswerGenerator:
    """Node for generating answers based on retrieved documents."""

    def __init__(self):
        """Initialize the answer generator."""
        self.llm = ChatOpenAI(
            api_key=openai_settings.API_KEY,
            model=openai_settings.MODEL_NAME,
            temperature=openai_settings.TEMPERATURE,
        )

        self.answer_prompt = PromptTemplate.from_template(
            """You are a helpful AI assistant that answers questions based on the provided document content.

Context from documents:
{context}

User Question: {question}

Instructions:
- You must always answer in the same language as the user's question, regardless of the language of the context.
- User's question is in {language} language
- Answer the question based only on the provided context
- If the answer cannot be found in the context, say "I don't have enough information in the documents to answer that question."
- Be concise but comprehensive in your response
- If referencing specific information, try to mention which document it came from if that information is available
- Maintain a helpful and professional tone
- Use the document content to provide accurate and detailed answers

Answer:"""
        )

    async def generate_answer(self, state: State) -> Dict[str, Any]:
        """
        Generate an answer based on the retrieved documents.

        Args:
            state: Current state containing query and documents

        Returns:
            Updated state with generated answer
        """
        try:
            query = state.get("input", "")
            documents = state.get("documents", [])
            language = detect(query) if query else "en"

            if not documents:
                logger.warning("No documents available for answer generation")
                return {
                    "answer": "I don't have any documents to base my answer on.",
                    "is_last_step": True,
                }

            # Format context from documents
            context = "\n\n".join([doc for doc in documents])

            # Generate answer using LLM
            prompt = self.answer_prompt.format(context=context, question=query, language=language)
            response = await self.llm.ainvoke(prompt)
            answer_text = response.content

            logger.info(f"Generated answer for query: {query[:50]}...")

            return {"answer": answer_text, "is_last_step": True}

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                "answer": f"I encountered an error while generating the answer: {str(e)}",
                "is_last_step": True,
            }
