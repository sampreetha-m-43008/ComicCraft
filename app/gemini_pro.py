"""Step 2 of the pipeline: narration, dialogue and captions (creative model: Gemini Pro)."""
import json
import logging

from . import config
from .errors import StoryError
from .gemini_client import call_gemini_json
from .json_utils import parse_json_list, validate_panels
from .schemas import PanelStory

logger = logging.getLogger("comiccraft.story")
REQUIRED = ["panel_number", "narration", "dialogue", "caption"]


def _demo_story(outline: list, character_name: str) -> list:
    """DEMO MODE: fixed template text. NOT produced by AI."""
    lines = [
        ("Our story begins.", "This looks like the start of something big.", "Chapter one"),
        ("The path grows stranger with every step.", "I can't turn back now.", "Onward"),
        ("Danger appears without warning!", "Stay calm... think!", "Trouble"),
        ("An idea sparks at the perfect moment.", "That's it! I know what to do!", "The plan"),
        ("Peace returns, and something has changed.", "I'll never forget today.", "The end"),
    ]
    return [
        {"panel_number": p["panel_number"], "narration": n, "dialogue": f"{character_name}: \"{d}\"", "caption": c}
        for p, (n, d, c) in zip(outline, lines)
    ]


def generate_story(outline: list, story_prompt: str, character_name: str,
                   setting: str, tone: str, art_style: str) -> list:
    """Return a validated list of 5 dicts: panel_number, narration, dialogue, caption."""
    if config.is_demo_text():
        logger.warning("DEMO MODE: using template story text (no AI call).")
        return _demo_story(outline, character_name)

    prompt = f"""You are a comic book scriptwriter. Write text for every panel of this comic.
Story idea: {story_prompt}
Main character: {character_name}
Setting: {setting}
Tone: {tone}
Art style: {art_style}

Panel outline (JSON):
{json.dumps(outline, indent=2)}

Rules:
- Write for all 5 panels, in order, as one coherent story.
- {character_name} keeps the same personality and voice throughout.
- No panel may contradict the previous one unless the story explains why.
- narration: 1-2 sentences. dialogue: 1-3 short spoken lines, prefixed with the speaker's name.
  caption: a very short (2-6 words) label.
Return a JSON list with objects having: panel_number, narration, dialogue, caption."""
    try:
        raw = call_gemini_json(config.GEMINI_PRO_MODEL, prompt, list[PanelStory], 0.9)
        return validate_panels(parse_json_list(raw), REQUIRED)
    except Exception as exc:
        logger.exception("Story generation failed")
        raise StoryError(str(exc)) from exc
