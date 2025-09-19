"""
Relevance checking node for RAG agent.
This node uses LLM-as-a-judge approach to determine if retrieved documents are relevant to the user query.
"""

import logging
from typing import Dict, Any

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field   
from chat_bot.config import OpenAISettings
from ..state import State

logger = logging.getLogger(__name__)

openai_settings = OpenAISettings()

class RelevanceQuery(BaseModel):
    """Determines if retrieved documents are relevant to the user query"""

    relevance: bool = Field(
        ...,
        description="Indicates whether the retrieved documents are relevant to the user query. False is not relevant, True is relevant.",
    )

class RelevanceChecker:
    """Node for checking document relevance to user query."""
    
    def __init__(self):
        """Initialize the relevance checker."""
        self.llm = ChatOpenAI(
            api_key=openai_settings.API_KEY,
            model=openai_settings.MODEL_NAME,
            temperature=0.1,  # Low temperature for consistent evaluation
        ).with_structured_output(RelevanceQuery)
        
        self.relevance_prompt = PromptTemplate.from_template(
            """You are an expert at evaluating document relevance.

Given a user query and retrieved documents, determine if the documents contain information relevant to answering the query.

User Query: {query}

Retrieved Documents:
{documents}

Evaluation Criteria:
- Do the documents contain information that can help answer the user's question?
- Is there any meaningful connection between the query and document content?
- Consider partial relevance as still relevant

Respond with ONLY:
- "True" if the documents can help answer the query
- "False" if the documents cannot help answer the query

Response:"""
        )
        
    async def check_relevance(self, state: State) -> bool:
        """
        Check if retrieved documents are relevant to the user query.
        
        Args:
            state: Current state containing query and documents
            
        Returns:
            Boolean indicating if documents are relevant
        """
        try:
            query = state.get("input", "")
            
            # Get documents from state - they should be populated by the retriever tool
            documents = state.get("documents", [])
            
            if not documents:
                logger.info("No documents found for relevance check")
                return False
            
            # Format documents for evaluation
            formatted_docs = "\n\n".join([str(doc) for doc in documents])
            
            # Check relevance using LLM with proper prompt formatting
            prompt_input = self.relevance_prompt.format(
                query=query,
                documents=formatted_docs
            )
            
            response = await self.llm.ainvoke(prompt_input)
            is_relevant = response.relevance
            logger.info(f"Relevance check result: {is_relevant}")
            
            return is_relevant
            
        except Exception as e:
            logger.error(f"Error in relevance checking: {str(e)}")
            return False
    
    def relevance_passed_handler(self, state: State) -> Dict[str, Any]:
        """Handle case where documents are relevant."""
        logger.info("Documents are relevant to the query")
        return {"is_last_step": False}
    
    def relevance_failed_handler(self, state: State) -> Dict[str, Any]:
        """Handle case where documents are not relevant."""
        logger.info("Documents are not relevant to the query")
        return {
            "answer": "I couldn't find information in the uploaded documents that's relevant to your question. Please try asking about topics that are covered in your documents.",
            "is_last_step": True
        }