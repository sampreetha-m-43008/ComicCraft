"""Core tests (run in DEMO mode, no API keys needed):  python -m unittest discover -s tests -v"""
import os
import unittest

os.environ["COMICCRAFT_MODE"] = "demo"  # must be set before the app modules are imported

from app import config  # noqa: E402
from app.gemini_flash import generate_outline  # noqa: E402
from app.gemini_pro import generate_story  # noqa: E402
from app.image_generator import build_character_sheet, generate_image  # noqa: E402
from app.json_utils import parse_json_list, strip_code_fences, validate_panels  # noqa: E402
from app.layout_builder import build_comic_layout  # noqa: E402

ARGS = ("A brave fox exploring an enchanted forest", "Leo", "Forest", "Dramatic", "Anime")


class JsonUtilsTests(unittest.TestCase):
    def test_strips_code_fences(self):
        self.assertEqual(strip_code_fences('```json\n[{"a": 1}]\n```'), '[{"a": 1}]')

    def test_parses_fenced_and_wrapped_json(self):
        self.assertEqual(parse_json_list('```json\n[{"a": 1}]\n```'), [{"a": 1}])
        self.assertEqual(parse_json_list('{"panels": [{"a": 1}]}'), [{"a": 1}])
        self.assertEqual(parse_json_list('Sure! [{"a": 1}] Enjoy'), [{"a": 1}])

    def test_validate_rejects_wrong_count_or_missing_key(self):
        with self.assertRaises(ValueError):
            validate_panels([{"title": "x"}], ["panel_number", "title"], count=5)
        with self.assertRaises(ValueError):
            validate_panels([{"title": ""}] * 5, ["panel_number", "title"], count=5)


class PipelineDemoTests(unittest.TestCase):
    def test_outline_story_images_layout(self):
        outline = generate_outline(*ARGS)
        self.assertEqual([p["panel_number"] for p in outline], [1, 2, 3, 4, 5])
        story = generate_story(outline, *ARGS)
        self.assertEqual(len(story), 5)
        info = build_character_sheet("Leo", ARGS[0])
        images = [generate_image(p["image_prompt"], p["panel_number"], info, "Anime") for p in outline]
        for img in images:
            self.assertTrue((config.BASE_DIR / img).exists())
        layout = build_comic_layout(outline, story, images)
        self.assertEqual(layout[0]["image"], "/static/panels/panel_1.png")
        for key in ("panel_number", "title", "image", "scene_description", "caption", "narration", "dialogue"):
            self.assertIn(key, layout[0])

    def test_layout_rejects_mismatch(self):
        with self.assertRaises(ValueError):
            build_comic_layout([{"panel_number": 1}], [], [])


class ExportTests(unittest.TestCase):
    def test_pdf_created(self):
        try:
            from app.exporters import save_pdf
        except ImportError:
            self.skipTest("fpdf2 not installed")
        outline = generate_outline(*ARGS)
        story = generate_story(outline, *ARGS)
        info = build_character_sheet("Leo", ARGS[0])
        images = [generate_image(p["image_prompt"], p["panel_number"], info, "Anime") for p in outline]
        layout = build_comic_layout(outline, story, images)
        pdf_rel = save_pdf(layout, "The Adventure of Leo", demo=True)
        pdf = config.BASE_DIR / pdf_rel
        self.assertTrue(pdf.exists())
        self.assertEqual(pdf.read_bytes()[:4], b"%PDF")


if __name__ == "__main__":
    unittest.main()
