"""
API schemas package.

This package contains all Pydantic models used for request/response validation
and serialization in the FastAPI application.
"""

from .health import HealthCheck
from .common import BaseResponse, ErrorResponse

__all__ = ["HealthCheck", "BaseResponse", "ErrorResponse"]