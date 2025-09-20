"""OpenAI summarization service."""

import logging
from typing import Dict, List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from chat_bot.config import OpenAISettings

logger = logging.getLogger(__name__)
openai_settings = OpenAISettings()


class DocumentStructure(BaseModel):
    """Structured representation of document analysis."""

    title: str = Field(
        ...,
        description="The main title or subject of the document. If no explicit title exists, create a descriptive one based on the content.",
    )

    main_idea: str = Field(
        ...,
        description="The central theme or main idea of the document in 2-3 sentences.",
    )

    key_concepts: List[str] = Field(
        ...,
        description="List of 5-10 key concepts, topics, or themes discussed in the document.",
    )

    terms_and_definitions: Optional[Dict[str, str]] = Field(
        default=None,
        description="Important terms, acronyms, or specialized vocabulary with their definitions or explanations.",
    )

    main_points: List[str] = Field(
        ...,
        description="List of 5-7 main points or arguments presented in the document.",
    )

    conclusion: Optional[str] = Field(
        default=None,
        description="The conclusion or final thoughts from the document, if present.",
    )


class Summarizer:
    """Document summarization service with structured analysis and chunking support."""

    def __init__(self):
        """Initialize the summarizer with structured output capability."""
        try:
            # LLM for structured document analysis
            self.analysis_llm = ChatOpenAI(
                api_key=openai_settings.API_KEY,
                model=openai_settings.MODEL_NAME,
                temperature=0.1,  # Low temperature for consistent structure
            ).with_structured_output(DocumentStructure)

            # Regular LLM for chunk summarization
            self.summary_llm = ChatOpenAI(
                api_key=openai_settings.API_KEY,
                model=openai_settings.MODEL_NAME,
                temperature=0.1,
            )

            # Text splitter for large documents
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=15000,  # ~15k chars = ~3750 tokens (safe for 30k limit)
                chunk_overlap=1000,  # Overlap to maintain context
                length_function=len,
            )

            # Prompt for structured analysis
            self.analysis_prompt = PromptTemplate.from_template(
                """You are an expert document analyst. Analyze the following document and extract its key structural elements.
The response should be in the same language as the input document.
Document Content:
{document_content}

Instructions:
- Identify the main title or create a descriptive one if none exists
- Extract the central theme and main idea
- List key concepts and topics discussed
- Identify important terms, acronyms, or specialized vocabulary with their meanings
- Extract the main points or arguments
- Identify any conclusion or final thoughts

Analyze the document thoroughly and provide a structured breakdown of its content."""
            )

            # Prompt for chunk summarization
            self.chunk_summary_prompt = PromptTemplate.from_template(
                """Summarize the following document chunk while preserving all important information:

{chunk_content}

Provide a comprehensive summary that includes:
- Main topics covered in this section
- Key facts, concepts, or arguments
- Important details or data
- Any conclusions or findings

IMPORTANT: The summary should be in the same language as the input chunk.
Summary:"""
            )

            # Prompt for combining chunk summaries
            self.combine_summaries_prompt = PromptTemplate.from_template(
                """You are combining multiple summaries of chunks from the same document. Create a comprehensive, unified summary.

Document chunk summaries:
{summaries}

Instructions:\
- Combine all chunk summaries into one cohesive summary
- Eliminate redundancy while preserving all important information
- Maintain logical flow and structure
- Keep the same language as the original summaries
- Ensure all key concepts and main points are included

IMPORTANT: The final summary should be in the same language as the input summaries.
Unified Summary:"""
            )

        except Exception as e:
            logger.error(f"Failed to initialize summarizer: {str(e)}")
            raise

    async def analyze_document_structure(self, content: str) -> DocumentStructure:
        """
        Analyze document content and extract structured elements.

        Args:
            content: The document content to analyze

        Returns:
            DocumentStructure object with extracted elements

        Raises:
            Exception: If analysis fails
        """
        try:
            logger.info("Starting structured document analysis")

            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")

            # Format the analysis prompt
            prompt_input = self.analysis_prompt.format(document_content=content)

            # Get structured analysis
            analysis_result = await self.analysis_llm.ainvoke(prompt_input)

            logger.info(
                f"Document analysis completed. Title: '{analysis_result.title}'"
            )
            logger.info(f"Extracted {len(analysis_result.key_concepts)} key concepts")
            logger.info(
                f"Extracted {len(analysis_result.terms_and_definitions or {})} terms"
            )
            logger.info(f"Extracted {len(analysis_result.main_points)} main points")

            return analysis_result

        except Exception as e:
            logger.error(f"Error during document structure analysis: {str(e)}")
            raise

    def combine_analysis_to_summary(self, analysis: DocumentStructure) -> str:
        """
        Combine structured analysis elements into a cohesive summary using Python.

        Args:
            analysis: DocumentStructure object with extracted elements

        Returns:
            Combined summary text
        """
        try:
            logger.info("Combining structured analysis into final summary")

            # Start building the summary
            summary_parts = []

            # Add title as header
            if analysis.title:
                summary_parts.append(f"**{analysis.title}**\n")

            # Add main idea
            if analysis.main_idea:
                summary_parts.append(f"{analysis.main_idea}\n")

            # Add main points
            if analysis.main_points:
                summary_parts.append("**Key Points:**")
                for i, point in enumerate(analysis.main_points, 1):
                    summary_parts.append(f"{i}. {point}")
                summary_parts.append("")  # Empty line for spacing

            # Add key concepts
            if analysis.key_concepts:
                concepts_text = ", ".join(analysis.key_concepts)
                summary_parts.append(f"**Key Concepts:** {concepts_text}\n")

            # Add terms and definitions
            if analysis.terms_and_definitions:
                summary_parts.append("**Important Terms:**")
                for term, definition in analysis.terms_and_definitions.items():
                    summary_parts.append(f"• **{term}**: {definition}")
                summary_parts.append("")  # Empty line for spacing

            # Add conclusion if present
            if analysis.conclusion:
                summary_parts.append(f"**Conclusion:** {analysis.conclusion}")

            # Join all parts with newlines
            final_summary = "\n".join(summary_parts).strip()

            logger.info("Successfully combined analysis into summary")
            return final_summary

        except Exception as e:
            logger.error(f"Error combining analysis to summary: {str(e)}")
            return "Summary could not be generated."

    async def summarize_document(self, content: str) -> str:
        """
        Perform complete document summarization with structured analysis.
        Handles large documents by chunking them if they exceed token limits.

        This method combines structured document analysis with comprehensive
        summary generation to produce high-quality summaries.

        Args:
            content: The document content to summarize

        Returns:
            Comprehensive summary text ready for database storage

        Raises:
            ValueError: If content is empty or invalid
            Exception: If summarization process fails
        """
        try:
            logger.info("Starting enhanced document summarization")

            # Validate input
            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")

            if len(content.strip()) < 50:
                logger.warning(
                    "Document content is very short, proceeding with basic summarization"
                )
                # For very short documents, return the content as-is with minimal formatting
                return f"**Summary:** {content.strip()}"

            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(content) / 4

            # Step 1: Analyze document structure (with chunking if needed)
            if estimated_tokens <= 20000:  # Safe limit considering prompt overhead
                logger.info("Document is small enough for direct processing")
                analysis = await self.analyze_document_structure(content)
            else:
                logger.info("Document is large, using chunking approach")
                analysis = await self._analyze_large_document(content)

            # Step 2: Combine analysis into summary using Python
            final_summary = self.combine_analysis_to_summary(analysis)

            logger.info("Enhanced document summarization completed successfully")
            return final_summary

        except Exception as e:
            logger.error(f"Error during document summarization: {str(e)}")
            # Return a basic fallback summary to prevent complete failure
            return f"**Summary:** Document analysis failed. Content preview: {content[:500]}..."

        except ValueError as ve:
            logger.error(f"Validation error in document summarization: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error in enhanced document summarization: {str(e)}")
            # Fallback to simple text return
            try:
                logger.info("Attempting fallback to basic summary format")
                return (
                    f"**Summary:** {content[:500]}..."
                    if len(content) > 500
                    else f"**Summary:** {content}"
                )
            except Exception as fallback_error:
                logger.error(
                    f"Fallback summarization also failed: {str(fallback_error)}"
                )
                raise Exception(f"Document summarization failed: {str(e)}")

    async def _analyze_large_document(self, content: str) -> DocumentStructure:
        """Analyze large documents by chunking and combining results."""
        try:
            # Split document into chunks
            chunks = self.text_splitter.split_text(content)
            logger.info(f"Split document into {len(chunks)} chunks")

            # Summarize each chunk
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                try:
                    logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                    prompt = self.chunk_summary_prompt.format(chunk_content=chunk)
                    summary = await self.summary_llm.ainvoke(prompt)
                    chunk_summaries.append(summary.content)
                except Exception as e:
                    logger.error(f"Failed to summarize chunk {i+1}: {str(e)}")
                    # Continue with other chunks even if one fails
                    chunk_summaries.append(f"[Summary failed for chunk {i+1}]")

            # Combine all chunk summaries
            combined_summaries = "\n\n".join(chunk_summaries)
            logger.info("Combining chunk summaries into unified summary")

            # Create a comprehensive summary from all chunks
            combine_prompt = self.combine_summaries_prompt.format(summaries=combined_summaries)
            unified_summary = await self.summary_llm.ainvoke(combine_prompt)

            # Now analyze the unified summary for structure
            logger.info("Analyzing unified summary for document structure")
            return await self.analyze_document_structure(unified_summary.content)

        except Exception as e:
            logger.error(f"Failed to analyze large document: {str(e)}")
            raise
