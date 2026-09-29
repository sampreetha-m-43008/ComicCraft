"""The 5-step comic pipeline, shared by the HTML route and the JSON route."""
import logging

from . import config
from .exporters import save_pdf
from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import build_character_sheet, generate_image
from .layout_builder import build_comic_layout

logger = logging.getLogger("comiccraft.pipeline")


def create_comic(story_prompt: str, character_name: str, setting: str,
                 tone: str, art_style: str) -> dict:
    """Run outline -> story -> images -> layout -> PDF and return everything the UI needs."""
    logger.info("Starting comic: character=%s style=%s tone=%s", character_name, art_style, tone)
    outline = generate_outline(story_prompt, character_name, setting, tone, art_style)
    story = generate_story(outline, story_prompt, character_name, setting, tone, art_style)

    character_info = build_character_sheet(character_name, story_prompt)
    images = [
        generate_image(p["image_prompt"], p["panel_number"], character_info, art_style)
        for p in outline
    ]

    layout = build_comic_layout(outline, story, images)
    title = f"The Adventure of {character_name}"
    demo = config.is_demo()
    pdf_path = save_pdf(layout, title, demo=demo)
    logger.info("Comic finished: %s", pdf_path)
    return {"title": title, "layout": layout, "pdf_path": pdf_path, "demo_mode": demo}
