"""Enumeration definitions."""
import enum


class DocumentTypeEnum(enum.Enum):
    """Document type enumeration."""

    PDF = "pdf"
    TXT = "txt"


class BREAKPOINT_THRESHOLD_TYPE(enum.Enum):
    """Breakpoint threshold types enumeration."""

    PERCENTILE = "percentile"
    STANDARD_DEVIATION = "standard_deviation"
    INTERQUARTILE = "interquartile"
    GRADIENT = "gradient"
