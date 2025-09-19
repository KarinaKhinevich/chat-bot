"""Chat-related Pydantic schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The question to ask about the documents",
    )


class ChatResponse(BaseModel):
    """Schema for chat response."""

    answer: str = Field(..., description="The AI assistant's answer to the question")
    sources: list[str] = Field(
        default_factory=list,
        description="List of document sources used to generate the answer",
    )


class ChatError(BaseModel):
    """Schema for chat error response."""

    detail: str = Field(..., description="Error message")
