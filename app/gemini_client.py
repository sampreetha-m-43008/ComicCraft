"""
Shared Gemini helper.

CHANGE FROM THE SPEC: the spec installs `google-generativeai` and uses
`models/gemini-1.5-*`. That SDK is deprecated and the 1.5 models are retired.
We use the current `google-genai` SDK and Gemini 2.5 models (configurable in .env).
"""
import logging

from . import config
from .errors import ConfigError

logger = logging.getLogger("comiccraft.gemini")


def call_gemini_json(model: str, prompt: str, schema, temperature: float) -> str:
    """Send a prompt and return the raw JSON text. `schema` is e.g. list[PanelOutline]."""
    if not config.GEMINI_API_KEY:
        raise ConfigError("GEMINI_API_KEY is missing")
    # Imported here so demo mode works even if the SDK is not installed.
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=config.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_SECONDS * 1000),
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",  # ask for structured JSON
            response_schema=schema,
            temperature=temperature,
        ),
    )
    if not response.text:
        raise ValueError("Gemini returned an empty response")
    return response.text
