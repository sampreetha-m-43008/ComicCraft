"""Step 1 of the pipeline: create the 5-panel outline (fast model: Gemini Flash)."""
import logging

from . import config
from .errors import OutlineError
from .gemini_client import call_gemini_json
from .json_utils import parse_json_list, validate_panels
from .schemas import PanelOutline

logger = logging.getLogger("comiccraft.outline")
REQUIRED = ["panel_number", "title", "scene_description", "image_prompt"]


def _demo_outline(story_prompt, character_name, setting, tone, art_style) -> list:
    """DEMO MODE: fixed template. NOT produced by AI."""
    beats = [
        ("The Beginning", f"{character_name} stands at the edge of the {setting}, ready for the story: {story_prompt}."),
        ("The Journey", f"{character_name} moves deeper into the {setting}, and the mood turns {tone.lower()}."),
        ("The Challenge", f"A big obstacle blocks {character_name}'s path in the {setting}."),
        ("The Turning Point", f"{character_name} finds a clever way to face the obstacle."),
        ("The Ending", f"{character_name} looks back on the adventure, changed by it."),
    ]
    return [
        {
            "panel_number": i,
            "title": title,
            "scene_description": scene,
            "image_prompt": f"{scene} {tone} mood.",
        }
        for i, (title, scene) in enumerate(beats, start=1)
    ]


def generate_outline(story_prompt: str, character_name: str, setting: str,
                     tone: str, art_style: str) -> list:
    """Return a validated list of 5 dicts: panel_number, title, scene_description, image_prompt."""
    if config.is_demo_text():
        logger.warning("DEMO MODE: using template outline (no AI call).")
        return _demo_outline(story_prompt, character_name, setting, tone, art_style)

    prompt = f"""You are a comic book writer. Create a 5-panel comic outline.
Story idea: {story_prompt}
Main character: {character_name}
Setting: {setting}
Tone: {tone}
Art style: {art_style}

Rules:
- Exactly 5 panels: beginning, rising action, challenge, turning point, ending.
- Each panel follows logically from the previous one.
- "image_prompt" is a visual description only (subject, action, background, lighting).
  Do not ask for any text, speech bubbles or letters inside the image.
- Always describe {character_name} the same way in every image_prompt.
Return a JSON list with objects having: panel_number, title, scene_description, image_prompt."""
    try:
        raw = call_gemini_json(config.GEMINI_FLASH_MODEL, prompt, list[PanelOutline], 0.8)
        return validate_panels(parse_json_list(raw), REQUIRED)
    except Exception as exc:  # network, quota, bad JSON, invalid structure ...
        logger.exception("Outline generation failed")
        raise OutlineError(str(exc)) from exc
