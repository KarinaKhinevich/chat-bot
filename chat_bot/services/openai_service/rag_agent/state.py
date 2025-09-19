"""State definition for RAG agent."""
from typing import List, Optional, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


class State(TypedDict):
    """
    Represents the state structure for a RAG agent.

    This state tracks the complete flow from moderation through document
    retrieval, relevance checking, and answer generation.
    """

    # Input and output
    input: str  # User's original query
    answer: str  # Final generated answer

    # Messages for conversation tracking
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Document-related fields
    documents: List[str]  # Retrieved document contents
    sources: List[str]  # Source filenames/identifiers

    # Relevance and scoring
    is_relevant: bool  # Boolean flag for relevance decision

    # Flow control
    moderated: bool  # Whether content passed moderation
    is_last_step: bool  # Whether this is the final step in the flow

    # Optional metadata
    retrieval_k: Optional[int]  # Number of documents to retrieve
    error_message: Optional[str]  # Error information if something fails
