"""Route tests using FastAPI's TestClient (needs fastapi + httpx installed)."""
import os
import unittest

os.environ["COMICCRAFT_MODE"] = "demo"

try:
    from fastapi.testclient import TestClient
    from app.main import app
except ImportError:  # pragma: no cover
    TestClient = None

FORM = {"story_prompt": "A brave fox exploring an enchanted forest", "character_name": "Leo",
        "setting": "Forest", "custom_setting": "", "tone": "Dramatic", "art_style": "Anime"}


@unittest.skipIf(TestClient is None, "fastapi/httpx not installed")
class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_homepage(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Generate Comic", r.text)
        self.assertIn("DEMO MODE", r.text)

    def test_docs(self):
        self.assertEqual(self.client.get("/docs").status_code, 200)

    def test_generate_form_and_export_success(self):
        r = self.client.post("/generate", data=FORM)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Download Your Comic as PDF", r.text)
        self.assertIn("Create Another Comic", r.text)
        link = [p for p in r.text.split('"') if p.startswith("/export-success?file=")][0]
        ok = self.client.get(link)
        self.assertEqual(ok.status_code, 200)
        self.assertIn("Your Comic Has Been Successfully Created!", ok.text)

    def test_generate_form_validation(self):
        r = self.client.post("/generate", data={**FORM, "story_prompt": "hi", "character_name": ""})
        self.assertEqual(r.status_code, 422)
        self.assertIn("banner error", r.text)

    def test_generate_json(self):
        payload = {"story_prompt": FORM["story_prompt"], "character_name": "Leo", "setting": "Forest",
                   "tone": "Funny", "art_style": "Comic Book"}
        r = self.client.post("/generate-comic/json", json=payload)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(len(body["layout"]), 5)
        self.assertTrue(body["pdf_path"].endswith(".pdf"))
        self.assertTrue(body["demo_mode"])

    def test_generate_json_invalid(self):
        r = self.client.post("/generate-comic/json", json={"story_prompt": "x"})
        self.assertEqual(r.status_code, 422)

    def test_test_image(self):
        r = self.client.get("/test-image")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "image/png")

    def test_export_success_rejects_bad_names(self):
        self.assertEqual(self.client.get("/export-success?file=../../.env").status_code, 404)
        self.assertEqual(self.client.get("/export-success").status_code, 404)


if __name__ == "__main__":
    unittest.main()
