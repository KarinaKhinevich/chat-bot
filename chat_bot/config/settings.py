"""Project settings module."""
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


load_dotenv()


# Database settings
class DBSettings(BaseSettings):
    """Database configuration settings."""

    PASSWORD: str
    USER: str
    HOST: str
    PORT: int
    DB: str
    VECTOR_TABLE_NAME: str = "documents_vectors"
    VECTOR_SIZE: int = 1536  # OpenAI text-embedding-3-small produces 1536 dimensions

    @property
    def URL(self) -> str:
        """Construct the database URL."""
        return f"postgresql+psycopg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"

    class Config:
        """Pydantic configuration for environment variable prefix."""

        env_prefix = "POSTGRES_"


# OpenAI settings
class OpenAISettings(BaseSettings):
    """OpenAI configuration settings."""

    API_KEY: str
    MODEL_NAME: str = "gpt-4o"
    TEMPERATURE: float = 0

    class Config:
        """Pydantic configuration for environment variable prefix."""

        env_prefix = "OPENAI_"


# Langchain settings
class LangchainSettings(BaseSettings):
    """Langchain configuration settings."""

    API_KEY: str
    TRACING_V2: bool = True
    PROJECT_NAME: str = "chatbot_dev"

    class Config:
        """Pydantic configuration for environment variable prefix."""

        env_prefix = "LANGCHAIN_"


# Chunking settings
class ChunkingSettings(BaseSettings):
    """Settings for document chunking and embedding."""

    STRATEGY: str = "general"  # Options: 'general', 'semantic'
    MODEL_NAME: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 500
    OVERLAP_SIZE: int = 50
    BATCH_SIZE: int = 50  # Number of chunks to process in each embedding batch
    SUB_BATCH_SIZE: int = 10  # Fallback batch size for failed batches

    class Config:
        """Pydantic configuration for environment variable prefix."""

        env_prefix = "CHUNKING_"


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "custom_formatter": {
            "format": "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
        "stream_handler": {
            "formatter": "custom_formatter",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
        "file_handler": {
            "formatter": "custom_formatter",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",
            "maxBytes": 1024 * 1024 * 1,  # = 1MB
            "backupCount": 3,
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default", "file_handler"],
            "level": "TRACE",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["stream_handler", "file_handler"],
            "level": "TRACE",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["stream_handler", "file_handler"],
            "level": "TRACE",
            "propagate": False,
        },
        "uvicorn.asgi": {
            "handlers": ["stream_handler", "file_handler"],
            "level": "TRACE",
            "propagate": False,
        },
    },
}
