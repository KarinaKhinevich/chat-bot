from chat_bot.core import DocumentTypeEnum

# Document configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf": DocumentTypeEnum.PDF,
    "text/plain": DocumentTypeEnum.TXT,
}
