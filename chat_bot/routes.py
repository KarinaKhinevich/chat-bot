import logging
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from chat_bot.schemas import (DocumentUploadError, DocumentUploadResponse,
                              HealthCheck)
from chat_bot.utils import (generate_unique_filename, get_file_size,
                            save_uploaded_file, validate_file)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

# Initialize router and dependencies
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """
    Render the home page.

    Args:
        request: The FastAPI request object

    Returns:
        HTMLResponse: Rendered home page template
    """
    return templates.TemplateResponse(request, "home.html")


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
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """
    ## Upload a Document

    Upload a PDF or TXT document to the server.

    **Supported file types:**
    - PDF files (.pdf)
    - Text files (.txt)

    **File size limit:** 10MB

    Args:
        file: The file to upload

    Returns:
        DocumentUploadResponse: Information about the uploaded document

    Raises:
        HTTPException: If file validation or upload fails
    """
    try:
        # Validate the file
        document_type = validate_file(file)

        # Generate unique filename
        unique_filename, document_id = generate_unique_filename(file.filename)

        # Save the file
        file_path = await save_uploaded_file(file, unique_filename)

        # Get file size
        file_size = get_file_size(file_path)

        # Log the upload
        logger.info(f"Document uploaded: {file.filename} -> {unique_filename}")

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            document_type=document_type,
            upload_timestamp=datetime.now(),
            file_path=file_path,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred during file upload"
        )
