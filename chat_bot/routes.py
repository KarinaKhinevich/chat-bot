import logging

from fastapi import (APIRouter, Depends, File, HTTPException, Request,
                     UploadFile, status)
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chat_bot.core import DocumentTypeEnum
from chat_bot.database import create_tables, get_db
from chat_bot.document_processing import DocumentParser, PGVector
from chat_bot.schemas import (DocumentInfo, DocumentListResponse,
                              DocumentUploadError, DocumentUploadResponse,
                              HealthCheck)
from chat_bot.services import DocumentService, summarize_document
from chat_bot.utils import validate_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

# Initialize router and dependencies
router = APIRouter()
templates = Jinja2Templates(directory="templates")

document_parser = DocumentParser()
pg_vector = PGVector()

# Ensure database tables exist on startup
# Note: This will be called during app startup
async def startup_event():
    """Initialize database tables on startup."""
    await create_tables()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    """
    Render the home page.

    Args:
        request: The FastAPI request object
        db: Async database session

    Returns:
        HTMLResponse: Rendered home page template
    """
    try:
        # Get documents from database
        document_service = DocumentService(db)
        documents = await document_service.get_documents()

        # Get document info for template
        document_list = [
            {
                "document_id": str(doc.id),
                "filename": doc.original_filename,
                "file_size": doc.file_size,
                "document_type": doc.document_type.value,
                "upload_timestamp": doc.upload_timestamp,
            }
            for doc in documents
        ]

        return templates.TemplateResponse(
            request, "home.html", {"documents": document_list}
        )
    except Exception as e:
        logger.error(f"Error fetching documents for home page: {str(e)}")
        # Fallback to empty list if there's an error
        return templates.TemplateResponse(request, "home.html", {"documents": []})


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request) -> HTMLResponse:
    """
    Render the document upload page.

    Args:
        request: The FastAPI request object

    Returns:
        HTMLResponse: Rendered upload page template
    """
    return templates.TemplateResponse(request, "upload.html")


@router.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on.
    This endpoint can primarily be used Docker to ensure a robust container orchestration and management is in place. # noqa
    Other services which rely on proper functioning of the API service will not deploy if this endpoint returns any other HTTP status code except 200 (OK). # noqa
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")


@router.post(
    "/document",
    tags=["documents"],
    summary="Upload a document",
    response_description="Document upload response",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentUploadResponse,
    responses={
        400: {
            "model": DocumentUploadError,
            "description": "Bad Request - Invalid file",
        },
        413: {"model": DocumentUploadError, "description": "File too large"},
        500: {"model": DocumentUploadError, "description": "Internal server error"},
    },
)
async def upload_document(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> DocumentUploadResponse:
    """
    ## Upload a Document

    Upload a PDF or TXT document to the database.

    **Supported file types:**
    - PDF files (.pdf)
    - Text files (.txt)

    **File size limit:** 10MB

    Args:
        file: The file to upload
        db: Database session

    Returns:
        DocumentUploadResponse: Information about the uploaded document

    Raises:
        HTTPException: If file validation or upload fails
    """
    try:
        # Validate the file
        document_type = validate_file(file)
        logger.info(f"File type check {file}")
        # Parse the document to extract content and metadata
        page_content, metadata = await document_parser.parse(file, document_type)

        # Generate summary using OpenAI (with fallback)
        try:
            summary = await summarize_document(page_content)
        except Exception as e:
            # If summary generation fails, use empty string
            summary = ""
            logger.warning(f"Failed to generate summary: {str(e)}")

        # pg_vector.add_document_to_vector(page_content, metadata)
        # Create document service and save to database
        document_service = DocumentService(db)
        result = await document_service.create_document(file, document_type, summary)

        # Log the upload
        logger.info(f"Document uploaded to database: {file.filename}")

        return result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred during file upload"
        )


@router.get(
    "/documents",
    tags=["documents"],
    summary="List all documents",
    response_description="List of uploaded documents",
    response_model=DocumentListResponse,
)
async def list_documents(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> DocumentListResponse:
    """
    ## List Documents

    Get a list of all uploaded documents.

    Args:
        skip: Number of documents to skip (for pagination)
        limit: Maximum number of documents to return
        db: Async database session

    Returns:
        DocumentListResponse: List of documents
    """
    document_service = DocumentService(db)
    documents = await document_service.get_documents(skip=skip, limit=limit)

    document_infos = [
        DocumentInfo(
            document_id=str(doc.id),
            summary=doc.summary or "",  # Use empty string if summary is None
            filename=doc.original_filename,
            file_size=doc.file_size,
            document_type=doc.document_type.value,
            upload_timestamp=doc.upload_timestamp,
            file_path=f"database://documents/{doc.id}",
        )
        for doc in documents
    ]

    return DocumentListResponse(documents=document_infos, total=len(document_infos))


@router.get(
    "/documents/{document_id}/summary",
    tags=["documents"],
    summary="Get a document summary",
    response_description="Document summary",
)
async def get_document_summary(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    ## Get Document Summary

    Get a document summary by its ID.

    Args:
        document_id: The document ID
        db: Async database session

    Returns:
        dict: The document summary

    Raises:
        HTTPException: If document not found
    """
    document_service = DocumentService(db)
    document_summary = await document_service.get_document_summary(document_id)

    if not document_summary:
        raise HTTPException(status_code=404, detail="Document summary not found")

    return {"document_id": document_id, "summary": document_summary}


@router.delete(
    "/documents/{document_id}",
    tags=["documents"],
    summary="Delete a document",
    response_description="Deletion confirmation",
)
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    ## Delete Document

    Delete a document by its ID.

    Args:
        document_id: The document ID
        db: Async database session

    Returns:
        dict: Deletion confirmation

    Raises:
        HTTPException: If document not found
    """
    document_service = DocumentService(db)
    success = await document_service.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"success": True, "message": "Document deleted successfully"}
