"""Step 4: merge outline + story + image paths into one clean list for the page and PDF."""


def build_comic_layout(outline: list, story: list, image_paths: list) -> list:
    """Return a list of 5 panel dicts. Raises ValueError if the parts do not line up."""
    if not (len(outline) == len(story) == len(image_paths)):
        raise ValueError("outline, story and images must have the same number of panels")
    story_by_number = {s["panel_number"]: s for s in story}
    layout = []
    for panel, image in zip(outline, image_paths):
        text = story_by_number.get(panel["panel_number"])
        if text is None:
            raise ValueError(f"No story text for panel {panel['panel_number']}")
        layout.append({
            "panel_number": panel["panel_number"],
            "title": panel["title"],
            "image": "/" + image.lstrip("/"),  # web URL, e.g. /static/panels/panel_1.png
            "scene_description": panel["scene_description"],
            "caption": text["caption"],
            "narration": text["narration"],
            "dialogue": text["dialogue"],
        })
    return layout
