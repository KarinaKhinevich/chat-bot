"""
Document chunking module for text processing and indexing.
"""

import logging
from typing import Dict, List, Union, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings

from chat_bot.config import OpenAISettings, ChunkingSettings
from chat_bot.core.enums import BREAKPOINT_THRESHOLD_TYPE

# Initialize settings
openai_settings = OpenAISettings()
chunking_settings = ChunkingSettings()

# Configure logger for this module
logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Document chunking service for splitting text into manageable chunks.
    Strategy selection based on configuration settings: 
    - Semantic chunking using embeddings for coherent topic boundaries
    - General chunking with configurable overlap and context windows
    """

    def __init__(self) -> None:
        """
        Initialize the document chunker with OpenAI embeddings.
        
        Raises:
            ValueError: If OpenAI API key is invalid or missing
            ConnectionError: If unable to connect to OpenAI API
        """
        try:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=openai_settings.API_KEY,
                model=chunking_settings.MODEL_NAME
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {str(e)}")
            raise

    def _semantic_split(
        self,
        page_content: str,
        metadata: Dict[str, Union[str, int]],
        breakpoint_threshold_type: str = BREAKPOINT_THRESHOLD_TYPE.PERCENTILE.value,
    ) -> List[Document]:
        """
        Split page content semantically using embedding-based chunk boundaries.
        
        This method uses semantic analysis to identify natural breakpoints in text
        where topics or concepts change, resulting in more coherent chunks compared
        to simple character-based splitting.
        
        Args:
            page_content (str): The input text to split into semantic chunks
            metadata (Dict[str, Union[str, int]]): Metadata to attach to each chunk
            breakpoint_threshold_type (str): Method for determining chunk boundaries:
                - "percentile": General-purpose, uses fixed upper threshold (simple)
                - "standard_deviation": Best for normally distributed data
                - "interquartile": Ignores normal fluctuations, focuses on outliers
                - "gradient": Captures dynamic shifts like topic changes
        
        Returns:
            List[Document]: List of semantically coherent document chunks with metadata
        
        Raises:
            ValueError: If breakpoint_threshold_type is invalid
            RuntimeError: If semantic splitting fails due to API issues

        Follow this link [https://python.langchain.com/docs/how_to/semantic-chunker/] for more information.
        """
        try:
            logger.debug(
                f"Starting semantic split with threshold type: {breakpoint_threshold_type}"
            )
            
            # Initialize semantic chunker
            text_splitter = SemanticChunker(
                self._embeddings, 
                breakpoint_threshold_type=breakpoint_threshold_type
            )
            
            # Create semantic chunks with metadata
            semantic_chunks = text_splitter.create_documents([page_content], [metadata])

            return semantic_chunks
            
        except Exception as e:
            logger.error(f"Semantic splitting failed: {str(e)}")
            raise RuntimeError(f"Failed to perform semantic split: {str(e)}") from e

    def _general_split(
        self,
        page_content: str,
        metadata: Dict[str, Union[str, int]],
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        context_window: int = 1,
    ) -> List[Document]:
        """
        Split text into overlapping chunks with contextual augmentation.
        
        This method splits text using character-based boundaries and enhances each
        chunk with surrounding context from neighboring chunks. This approach helps
        maintain continuity and provides better context for each chunk.
        
        Args:
            page_content (str): The input text to split into chunks
            metadata (Dict[str, Union[str, int]]): Metadata to attach to each chunk
            chunk_size (int): Target size of each individual chunk in characters
            chunk_overlap (int): Number of overlapping characters between chunks
            context_window (int): Number of neighboring chunks to include as context
        
        Returns:
            List[Document]: List of contextualized document chunks with metadata
        Raises:
            ValueError: If chunk_size or chunk_overlap are invalid
            RuntimeError: If text splitting fails due to API issues

        Follow this link [https://python.langchain.com/docs/how_to/recursive_text_splitter/] for more information.
        """
        try:
            logger.debug(
                f"Starting general split: chunk_size={chunk_size}, "
                f"overlap={chunk_overlap}, context_window={context_window}"
            )
            
            # Initialize recursive character text splitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap
            )
            
            # Split text into base chunks
            base_chunks = splitter.split_text(page_content)
            
            # Enhance each chunk with contextual information
            contextualized_chunks = []
            for i, current_chunk in enumerate(base_chunks):
                context_parts = []
                
                # Add preceding context chunks
                for j in range(1, context_window + 1):
                    if i - j >= 0:
                        context_parts.append(base_chunks[i - j])
                
                # Add current chunk
                context_parts.append(current_chunk)
                
                # Add following context chunks
                for j in range(1, context_window + 1):
                    if i + j < len(base_chunks):
                        context_parts.append(base_chunks[i + j])
                
                # Combine context into full chunk content
                full_chunk_content = "\n".join(context_parts)
                
                # Create enhanced metadata with chunk information
                enhanced_metadata = {
                    **metadata,
                    "chunk_index": i
                }
                
                # Create document with enhanced content and metadata
                contextualized_chunks.append(
                    Document(page_content=full_chunk_content, metadata=enhanced_metadata)
                )
            
            return contextualized_chunks
            
        except Exception as e:
            logger.error(f"General splitting failed: {str(e)}")
            raise RuntimeError(f"Failed to perform general split: {str(e)}") from e

    def index_document(
        self, 
        page_content: str, 
        metadata: Dict[str, Union[str, int, Any]]
    ) -> List[Document]:
        """
        Process and index a document using the configured chunking strategy.
        
        This is the main entry point for document chunking. It analyzes the
        configuration settings and applies the appropriate chunking strategy
        (semantic or general).
        
        Args:
            page_content (str): Raw content of the document to be chunked
            metadata (Dict[str, Union[str, int, Any]]): Document metadata to
                                                         attach to each chunk

        Returns:
            List[Document]: List of Document objects containing chunk content and
                          enhanced metadata including chunking information
        
        Raises:
            ValueError: If page_content is empty or invalid
            RuntimeError: If chunking process fails
        """
        # Validate input parameters
        if not page_content or not page_content.strip():
            raise ValueError("Raw text cannot be empty or whitespace only")
        
        if not isinstance(metadata, dict):
            raise ValueError("File metadata must be a dictionary")
        
        try:
            # Select chunking strategy based on configuration
            if chunking_settings.STRATEGY == "semantic":
                logger.info("Using semantic chunking strategy")
                chunks = self._semantic_split(page_content, metadata)
            else:
                logger.info("Using general chunking strategy")
                chunks = self._general_split(
                    page_content,
                    metadata,
                    chunk_size=chunking_settings.CHUNK_SIZE,
                    chunk_overlap=chunking_settings.OVERLAP_SIZE
                )
            
            logger.info(
                f"{chunking_settings.STRATEGY.capitalize()} chunking completed successfully: {len(chunks)} chunks created"
            )
            
            return chunks
            
        except Exception as e:
            error_message = f"Document indexing failed: {str(e)}"
            logger.error(error_message)
            raise RuntimeError(error_message) from e
