"""FastAPI application entry point. Start with:  uvicorn app.main:app --reload"""
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config
from .routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("comiccraft")

config.ensure_directories()  # the static mount below needs these folders to exist

app = FastAPI(title="ComicCraft", description="AI Comic Story Creator using Gemini Models")
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.include_router(router)

logger.info("Story mode: %s | Image backend: %s",
            "DEMO (template text)" if config.is_demo_text() else "LIVE (Gemini)",
            config.resolved_image_backend())
if config.is_demo():
    logger.warning("DEMO MODE is active for at least one step - output is not fully AI generated.")
