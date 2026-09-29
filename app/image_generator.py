"""
Step 3 of the pipeline: one illustration per panel.

generate_image() is the ONLY function the rest of the app calls. Behind it there are
three interchangeable backends, chosen by config (IMAGE_BACKEND in .env):
  - "mock"   : Pillow placeholder, clearly labelled DEMO (no AI, no key needed)
  - "local"  : Stable Diffusion through Hugging Face Diffusers on your own PC
  - "hf_api" : Hugging Face hosted inference using IMAGE_API_KEY (no big download)

CHANGE FROM THE SPEC: `runwayml/stable-diffusion-v1-5` was removed from Hugging Face;
the same model now lives at `stable-diffusion-v1-5/stable-diffusion-v1-5` (see IMAGE_MODEL).
"""
import logging
import re
import textwrap

from PIL import Image, ImageDraw, ImageFont

from . import config
from .errors import ImageError

logger = logging.getLogger("comiccraft.image")

IMAGE_SIZE = (768, 512)

# Words added to the prompt so the chosen art style is actually visible.
STYLE_HINTS = {
    "Anime": "anime style, cel shading, vibrant colors, clean line art",
    "Comic Book": "classic comic book style, bold ink outlines, halftone dots, dynamic colors",
    "Pixel Art": "pixel art, 16-bit retro game style, limited color palette",
    "Cartoon": "cartoon style, bright flat colors, friendly rounded shapes",
    "Realistic": "realistic digital painting, detailed, cinematic lighting",
}
NEGATIVE_PROMPT = "text, letters, words, watermark, signature, speech bubble, blurry, deformed, extra limbs"

_pipeline_cache = {}  # loading Stable Diffusion is slow, so load it only once


def build_character_sheet(character_name: str, story_prompt: str) -> dict:
    """Small dict reused for all 5 panels to help the hero look the same each time."""
    return {
        "name": character_name,
        "description": f"{character_name}, the main character of the story '{story_prompt}'",
    }


def _full_prompt(image_prompt: str, character_info: dict, art_style: str) -> str:
    style = STYLE_HINTS.get(art_style, art_style)
    return (f"{character_info['description']}. {image_prompt}. "
            f"{style}. consistent character design, single comic panel illustration, no text")


def _seed_for(character_info: dict) -> int:
    """Same character name -> same seed for all panels (helps visual consistency)."""
    return sum(ord(c) * (i + 1) for i, c in enumerate(character_info["name"])) % (2**31)


def _output_path(panel_number: int):
    config.PANELS_DIR.mkdir(parents=True, exist_ok=True)
    safe_number = int(panel_number)  # int() guarantees a safe filename like panel_3.png
    return config.PANELS_DIR / f"panel_{safe_number}.png"


# ---------------------------------------------------------------- mock backend
def _mock_image(prompt_text: str, panel_number: int, art_style: str, path) -> None:
    w, h = IMAGE_SIZE
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):  # simple vertical gradient
        shade = int(230 - 90 * y / h)
        draw.line([(0, y), (w, y)], fill=(shade, min(255, shade + 15), 255 - (shade // 3)))
    draw.rectangle([6, 6, w - 7, h - 7], outline=(20, 20, 20), width=6)
    try:
        big, small = ImageFont.load_default(size=44), ImageFont.load_default(size=20)
    except TypeError:  # very old Pillow
        big = small = ImageFont.load_default()
    draw.text((30, 28), f"PANEL {panel_number}", fill=(20, 20, 20), font=big)
    draw.text((30, 90), "DEMO PLACEHOLDER - NOT AI GENERATED", fill=(180, 0, 0), font=small)
    draw.text((30, 125), f"Art style requested: {art_style}", fill=(20, 20, 20), font=small)
    y = 175
    for line in textwrap.wrap(prompt_text, 55)[:8]:
        draw.text((30, y), line, fill=(40, 40, 40), font=small)
        y += 28
    img.save(path, "PNG")


# --------------------------------------------------------------- local backend
def _local_image(full_prompt: str, seed: int, path) -> None:
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError as exc:
        raise ImageError("Install requirements-ai.txt to use IMAGE_BACKEND=local") from exc

    if "pipe" not in _pipeline_cache:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        logger.info("Loading %s on %s (first run downloads several GB)...", config.IMAGE_MODEL, device)
        pipe = StableDiffusionPipeline.from_pretrained(config.IMAGE_MODEL, torch_dtype=dtype)
        _pipeline_cache["pipe"] = pipe.to(device)
        _pipeline_cache["device"] = device
    pipe, device = _pipeline_cache["pipe"], _pipeline_cache["device"]
    generator = torch.Generator(device=device).manual_seed(seed)
    result = pipe(full_prompt, negative_prompt=NEGATIVE_PROMPT, num_inference_steps=25,
                  width=IMAGE_SIZE[0], height=IMAGE_SIZE[1], generator=generator)
    result.images[0].save(path, "PNG")


# ------------------------------------------------------------ hf_api backend
def _hf_api_image(full_prompt: str, seed: int, path) -> None:
    if not config.IMAGE_API_KEY:
        raise ImageError("IMAGE_API_KEY is missing")
    try:
        from huggingface_hub import InferenceClient
    except ImportError as exc:
        raise ImageError("huggingface_hub is not installed") from exc
    client = InferenceClient(api_key=config.IMAGE_API_KEY, timeout=120)
    image = client.text_to_image(full_prompt, model=config.IMAGE_MODEL,
                                 negative_prompt=NEGATIVE_PROMPT, seed=seed)
    image.save(path, "PNG")


# ------------------------------------------------------------------ public API
def generate_image(image_prompt: str, panel_number: int, character_info: dict, art_style: str) -> str:
    """
    Create one panel image and save it to static/panels/panel_<n>.png.
    Returns the path relative to the project root, e.g. 'static/panels/panel_1.png'.
    """
    backend = config.resolved_image_backend()
    path = _output_path(panel_number)
    full_prompt = _full_prompt(image_prompt, character_info, art_style)
    try:
        if backend == "mock":
            logger.warning("DEMO MODE: drawing placeholder for panel %s (no AI image).", panel_number)
            _mock_image(image_prompt, panel_number, art_style, path)
        elif backend == "local":
            _local_image(full_prompt, _seed_for(character_info), path)
        else:
            _hf_api_image(full_prompt, _seed_for(character_info), path)
    except ImageError:
        raise
    except Exception as exc:
        logger.exception("Image generation failed (backend=%s, panel=%s)", backend, panel_number)
        raise ImageError(str(exc)) from exc
    if not path.exists():
        raise ImageError(f"Image file was not created: {path}")
    return path.relative_to(config.BASE_DIR).as_posix()
