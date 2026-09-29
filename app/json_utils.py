"""Helpers to safely turn model output into Python data."""
import json
import re


def strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers that models sometimes add."""
    text = (text or "").strip()
    match = re.match(r"^```[a-zA-Z0-9]*\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1).strip() if match else text


def parse_json_list(text: str) -> list:
    """Parse model output into a list. Accepts a bare list or {'panels': [...]}."""
    cleaned = strip_code_fences(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: grab the first [...] block inside surrounding chatter.
        start, end = cleaned.find("["), cleaned.rfind("]")
        if start == -1 or end <= start:
            raise
        data = json.loads(cleaned[start:end + 1])
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                data = value
                break
    if not isinstance(data, list):
        raise ValueError("Expected a JSON list of panels")
    return data


def validate_panels(items: list, required_keys: list, count: int = 5) -> list:
    """Check we got exactly `count` panels, numbered 1..count, with non-empty text keys."""
    if len(items) != count:
        raise ValueError(f"Expected {count} panels, got {len(items)}")
    clean = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Panel {index} is not an object")
        entry = {}
        for key in required_keys:
            if key == "panel_number":
                continue
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Panel {index} is missing '{key}'")
            entry[key] = value.strip()
        entry["panel_number"] = index  # we trust order, not the model's numbering
        clean.append(entry)
    return clean
