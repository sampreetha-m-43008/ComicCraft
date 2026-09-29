"""
Pydantic models.

Pydantic checks data types and rules automatically. FastAPI uses PromptRequest to
validate JSON sent to /generate-comic/json and to build the /docs page.
"""
from pydantic import BaseModel, Field, field_validator

ALLOWED_TONES = ["Funny", "Dramatic", "Adventure", "Light-hearted", "Mysterious", "Poetic"]
ALLOWED_STYLES = ["Anime", "Comic Book", "Pixel Art", "Cartoon", "Realistic"]


class PromptRequest(BaseModel):
    story_prompt: str = Field(..., min_length=5, max_length=500)
    character_name: str = Field(..., min_length=1, max_length=40)
    setting: str = Field(..., min_length=2, max_length=80)
    tone: str = Field(..., min_length=2, max_length=30)
    art_style: str = Field(..., min_length=2, max_length=30)

    @field_validator("story_prompt", "character_name", "setting", "tone", "art_style")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        v = " ".join(v.split())  # collapse whitespace/newlines
        if not v:
            raise ValueError("must not be empty")
        return v

    @field_validator("tone")
    @classmethod
    def valid_tone(cls, v: str) -> str:
        match = next((t for t in ALLOWED_TONES if t.lower() == v.lower()), None)
        if not match:
            raise ValueError(f"tone must be one of {ALLOWED_TONES}")
        return match

    @field_validator("art_style")
    @classmethod
    def valid_style(cls, v: str) -> str:
        match = next((s for s in ALLOWED_STYLES if s.lower() == v.lower()), None)
        if not match:
            raise ValueError(f"art_style must be one of {ALLOWED_STYLES}")
        return match


class PanelOutline(BaseModel):
    """Shape Gemini must follow for each outline panel."""
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str


class PanelStory(BaseModel):
    """Shape Gemini must follow for each story panel."""
    panel_number: int
    narration: str
    dialogue: str
    caption: str
