"""
Core package.
"""

from .constants import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, MAX_FILE_SIZE
from .enums import DocumentTypeEnum

__all__ = [
    "DocumentTypeEnum",
    "MAX_FILE_SIZE",
    "ALLOWED_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
]
