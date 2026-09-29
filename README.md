# ComicCraft - AI Comic Story Creator using Gemini Models

## 1. Project description
ComicCraft turns a short idea (for example *"A brave fox exploring an enchanted forest"*) into a
**5-panel comic**: a structured outline, narration and dialogue, one illustration per panel, an
on-screen comic preview and a downloadable **PDF**.

## 2. Features
- Form with story prompt, character name, setting (incl. custom), tone and art style
- Gemini Flash writes the 5-panel outline; Gemini Pro writes narration, dialogue and captions
- One image per panel (Stable Diffusion locally, or via the Hugging Face API)
- Comic-style preview page, PDF export, export-success page
- JSON API (`/generate-comic/json`) with automatic docs at `/docs`
- **Clearly labelled DEMO mode** that works with no API keys (placeholders, *not* AI output)
- Friendly error messages for users, detailed logs in the terminal

## 3. Technology stack
Python, FastAPI, Uvicorn, Jinja2, Pydantic, python-multipart, python-dotenv, Pillow,
fpdf2, `google-genai` (Gemini), Hugging Face Diffusers / `huggingface_hub` (images).

### Changes from the original specification
| Specification | Used here | Why |
|---|---|---|
| `google-generativeai` package | `google-genai` | Old SDK is deprecated; new one is the supported SDK |
| `gemini-1.5-flash` / `gemini-1.5-pro` | `gemini-2.5-flash` / `gemini-2.5-pro` (set in `.env`) | 1.5 models are retired. If Google renames again, only edit `.env` |
| `fpdf` | `fpdf2` | `fpdf` is unmaintained; `fpdf2` uses the same `from fpdf import FPDF` |
| `runwayml/stable-diffusion-v1-5` | `stable-diffusion-v1-5/stable-diffusion-v1-5` (set in `.env`) | The original repository was taken down; same model, new home |
| Only local Stable Diffusion | 3 image backends behind one `generate_image()` | Local SD needs a big download/GPU; the API or demo backend works on any laptop |

## 4. Architecture
```
Browser --form/JSON--> FastAPI routes --> pipeline:
   generate_outline (Gemini Flash) -> generate_story (Gemini Pro)
   -> generate_image x5 (Stable Diffusion) -> build_comic_layout -> save_pdf
--> Jinja2 template (comic_preview.html) --> Browser
```

## 5. Folder structure
```
ComicCraft/
  app/  __init__.py  main.py  routes.py  pipeline.py  config.py  schemas.py  errors.py
        json_utils.py  gemini_client.py  gemini_flash.py  gemini_pro.py
        image_generator.py  layout_builder.py  exporters.py
  templates/  index.html  comic_preview.html  export_success.html
  static/  css/style.css   panels/   exports/
  tests/  test_core.py  test_routes.py
  .env.example  .gitignore  requirements.txt  requirements-ai.txt  README.md  run.py
```

## 6. Prerequisites
Windows 10/11, Python 3.10+ (3.11/3.12 recommended), internet for installing packages.

## 7. Install Python
Download from https://www.python.org/downloads/ and tick **"Add python.exe to PATH"** in the installer.
Check with `python --version`.

## 8. Virtual environment (PowerShell or Command Prompt, inside the ComicCraft folder)
```
python -m venv comiccraft-env
comiccraft-env\Scripts\activate
```
(If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.)

## 9. Install dependencies
```
pip install -r requirements.txt
```
Optional, only for running Stable Diffusion on your own PC (several GB): `pip install -r requirements-ai.txt`

## 10. API keys
```
copy .env.example .env
```
Open `.env` and set:
- `GEMINI_API_KEY` - free key from https://aistudio.google.com/apikey
- `IMAGE_API_KEY` - Hugging Face token from https://huggingface.co/settings/tokens (for `IMAGE_BACKEND=auto/hf_api`)
- Or set `IMAGE_BACKEND=local` to use Diffusers on your PC (no image key needed).

Leave the keys as `your_key_here` / empty to stay in **DEMO mode**. Never commit `.env`.

## 11. Run
```
uvicorn app.main:app --reload
```
(or `python run.py`). Open http://127.0.0.1:8000 - API docs at http://127.0.0.1:8000/docs

## 12. Test
```
python -m unittest discover -s tests -v
```
Manual checks: open `/`, submit the example, click *Download Your Comic as PDF*, open
`/test-image`, and try the JSON API in `/docs`.

## 13. API endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Home page / form |
| POST | `/generate` | Form submit -> comic preview page |
| POST | `/generate-comic/json` | JSON in -> layout + PDF path out |
| GET | `/test-image?prompt=...&art_style=Anime` | Developer image test (returns a PNG) |
| GET | `/export-success?file=comic_....pdf` | Success page with PDF link |

## 14. Example input
Prompt: *A brave fox exploring an enchanted forest* | Character: *Leo* | Setting: *Forest* | Tone: *Dramatic* | Style: *Anime*

## 15. Expected output
A page with 5 numbered panels (title, image, caption, narration, speech bubble), a PDF in
`static/exports/comic_YYYYMMDD_HHMMSS.pdf` (title page + 5 panel pages), and the success page.
In DEMO mode a yellow banner says the content is placeholder, and each image says
"DEMO PLACEHOLDER - NOT AI GENERATED".

## 16. Troubleshooting
| Problem | Fix |
|---|---|
| `'uvicorn' is not recognized` | Activate the venv (`comiccraft-env\Scripts\activate`) and re-run `pip install -r requirements.txt` |
| Yellow DEMO banner but I set keys | `.env` must be in the project root, be named exactly `.env`; restart the server |
| "Sorry, ComicCraft couldn't generate your comic" | Read the terminal log: bad key, quota, wrong model name, or timeout |
| Gemini 404 model error | Set `GEMINI_FLASH_MODEL` / `GEMINI_PRO_MODEL` in `.env` to a currently available model |
| Hugging Face image errors (model not available on API) | Set `IMAGE_MODEL` to a text-to-image model your token can use, or use `IMAGE_BACKEND=local` |
| Local Stable Diffusion is very slow | Normal on CPU (minutes per image). Use a GPU, `hf_api`, or demo mode |
| Port 8000 busy | `uvicorn app.main:app --reload --port 8001` |

## 17. Future enhancements
User accounts, comic library, multi-page comics, more than 5 panels, stronger character
consistency (LoRA / reference images), editing and regenerating single panels, multiple
characters, cloud deployment. The modular files (`pipeline.py`, one function per stage) make
these easy to add.
