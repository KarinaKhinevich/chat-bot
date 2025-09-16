"""
Common base schemas that can be reused across the application.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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