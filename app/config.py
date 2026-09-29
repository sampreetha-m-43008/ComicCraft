"""
Central configuration.

All secrets and switches come from environment variables (loaded from a .env file).
Nothing secret is ever written in the source code.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# pathlib keeps paths correct on Windows (backslashes) and Linux/macOS (slashes).
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", "").strip()

# Model names live in .env so they can be changed when Google retires a model.
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "90"))

# IMAGE_BACKEND: "auto" | "mock" | "local" | "hf_api"
IMAGE_BACKEND = os.getenv("IMAGE_BACKEND", "auto").lower()
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "stable-diffusion-v1-5/stable-diffusion-v1-5")

# COMICCRAFT_MODE: "auto" | "demo" | "live"
_MODE = os.getenv("COMICCRAFT_MODE", "auto").lower()


def is_demo_text() -> bool:
    """Story text runs in DEMO mode when forced, or when no Gemini key exists."""
    if _MODE == "demo":
        return True
    if _MODE == "live":
        return False
    return not GEMINI_API_KEY


def resolved_image_backend() -> str:
    """Decide which image backend to use ('mock', 'local' or 'hf_api')."""
    if _MODE == "demo":
        return "mock"
    if IMAGE_BACKEND in ("mock", "local", "hf_api"):
        return IMAGE_BACKEND
    # auto: use the Hugging Face API if a key exists, otherwise placeholders.
    return "hf_api" if IMAGE_API_KEY else "mock"


def is_demo() -> bool:
    """True if ANY part of the pipeline is a placeholder (drives the DEMO banner)."""
    return is_demo_text() or resolved_image_backend() == "mock"


def ensure_directories() -> None:
    for d in (TEMPLATES_DIR, STATIC_DIR, PANELS_DIR, EXPORTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
