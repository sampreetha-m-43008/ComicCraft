"""All web routes. Each route receives a request, calls the pipeline, and returns a page or JSON."""
import logging
import re
import time

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from . import config
from .errors import ComicCraftError
from .image_generator import build_character_sheet, generate_image
from .pipeline import create_comic
from .schemas import ALLOWED_STYLES, ALLOWED_TONES, PromptRequest

logger = logging.getLogger("comiccraft.routes")
router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

SETTINGS = ["Forest", "School", "City", "Space", "Village", "Custom"]
FRIENDLY_ERROR = "Sorry, ComicCraft couldn't generate your comic right now. Please try again."
PDF_NAME = re.compile(r"^comic_\d{8}_\d{6}\.pdf$")  # blocks path tricks like ../../secret


def _form_page(request: Request, values=None, errors=None, status_code=200):
    return templates.TemplateResponse(request, "index.html", {
        "settings": SETTINGS, "tones": ALLOWED_TONES, "styles": ALLOWED_STYLES,
        "values": values or {}, "errors": errors or [], "demo_mode": config.is_demo(),
    }, status_code=status_code)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Show the input form."""
    return _form_page(request)


@router.post("/generate", response_class=HTMLResponse)
def generate(request: Request,
             story_prompt: str = Form(""), character_name: str = Form(""),
             setting: str = Form(""), custom_setting: str = Form(""),
             tone: str = Form(""), art_style: str = Form("")):
    """Handle the HTML form: validate, run the pipeline, show the preview."""
    values = {"story_prompt": story_prompt, "character_name": character_name, "setting": setting,
              "custom_setting": custom_setting, "tone": tone, "art_style": art_style}
    final_setting = custom_setting if setting == "Custom" else setting
    try:
        data = PromptRequest(story_prompt=story_prompt, character_name=character_name,
                             setting=final_setting, tone=tone, art_style=art_style)
    except ValidationError as exc:
        messages = [f"{'/'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        return _form_page(request, values, messages, status_code=422)

    try:
        result = create_comic(**data.model_dump())
    except ComicCraftError as exc:
        logger.error("Comic generation failed: %s (%s)", type(exc).__name__, exc)
        return _form_page(request, values, [exc.user_message], status_code=500)
    except Exception:
        logger.exception("Unexpected error during /generate")
        return _form_page(request, values, [FRIENDLY_ERROR], status_code=500)

    return templates.TemplateResponse(request, "comic_preview.html", {
        **result, "pdf_name": result["pdf_path"].rsplit("/", 1)[-1], "cache_bust": int(time.time()),
    })


@router.post("/generate-comic/json")
def generate_json(payload: PromptRequest):
    """JSON API: same pipeline, JSON answer. Pydantic already validated `payload`."""
    try:
        return create_comic(**payload.model_dump())
    except ComicCraftError as exc:
        logger.error("JSON generation failed: %s (%s)", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail=exc.user_message)
    except Exception:
        logger.exception("Unexpected error during /generate-comic/json")
        raise HTTPException(status_code=500, detail=FRIENDLY_ERROR)


@router.get("/test-image")
def test_image(prompt: str = "A brave fox in an enchanted forest", art_style: str = "Anime"):
    """Developer test: generate a single image and return it directly."""
    if art_style not in ALLOWED_STYLES or not (3 <= len(prompt) <= 300):
        raise HTTPException(status_code=422, detail="Invalid prompt or art_style")
    try:
        info = build_character_sheet("Test Hero", prompt)
        rel_path = generate_image(prompt, 0, info, art_style)
    except ComicCraftError as exc:
        logger.error("Test image failed: %s (%s)", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail=exc.user_message)
    return FileResponse(config.BASE_DIR / rel_path, media_type="image/png")


@router.get("/export-success", response_class=HTMLResponse)
def export_success(request: Request, file: str = ""):
    """Confirmation page with the PDF download link."""
    if not PDF_NAME.match(file) or not (config.EXPORTS_DIR / file).exists():
        raise HTTPException(status_code=404, detail="That comic PDF was not found.")
    return templates.TemplateResponse(request, "export_success.html", {"pdf_name": file})
