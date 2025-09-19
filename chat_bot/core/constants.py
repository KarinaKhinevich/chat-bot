"""Core constants and configurations."""
from .enums import DocumentTypeEnum

# Document configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf": DocumentTypeEnum.PDF,
    "text/plain": DocumentTypeEnum.TXT,
}

# Moderation message for inappropriate content
MODERATION_MESSAGE = "I'm sorry, but I can't assist with that kind of request. Moderation has flagged the content as inappropriate."

# Retrieval configuration
RETRIEVAL_FAILED_MESSAGE = "I couldn't find information in the uploaded documents that's relevant to your question. Please try asking about topics that are covered in your documents."

RETRIEVAL_TOP_K = 3  # Number of top documents to retrieve for context
