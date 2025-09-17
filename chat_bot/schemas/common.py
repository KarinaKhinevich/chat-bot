"""
Common base schemas that can be reused across the application.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = datetime.now()


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = datetime.now()
