"""
Database models for the chat bot application.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from chat_bot.core import DocumentTypeEnum

Base = declarative_base()


class Document(Base):
    """
    Document model for storing uploaded documents.
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    document_type = Column(SQLEnum(DocumentTypeEnum), nullable=False)
    content = Column(LargeBinary, nullable=False)  # Store file content as binary
    summary = Column(
        Text, nullable=True, default=""
    )  # Store generated document summary
    mime_type = Column(String(100), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"
