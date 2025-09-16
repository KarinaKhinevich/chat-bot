import logging
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import  HTMLResponse


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
    return templates.TemplateResponse("home.html", {"request": request})