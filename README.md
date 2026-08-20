# Doc Verification AI

A Streamlit-powered demo and toolkit for extracting fields from identity or credential documents and running verification checks (OCR, model-assisted extraction, heuristic and model-based verification). Designed for developers experimenting with document extraction/verification flows or building prototype proof-of-concepts.

[Repository](/DocVerificationAI/Doc_Verification_AI)

---

## Highlights

- Single-file Streamlit app (app.py) that orchestrates upload, extraction, verification, and result display.
- Modular processing in `modules/`:
  - `modules/extractor.py` — model + rule-based field extraction and JSON matching
  - `modules/ocr.py` — OCR and image/PDF helpers
  - `modules/verifier.py` — verification logic, scoring, and case handling
- Includes sample/demo cases in `data/demo_cases.json` and basic tests (test_*.py).
- No mandatory paid cloud services — optional integrations with Google GenAI or other OCR backends can be enabled with credentials.

---

## Quick start

1. Clone and install:

```bash
git clone https://github.com/DocVerificationAI/Doc_Verification_AI.git
cd Doc_Verification_AI
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Run the app locally:

```bash
python -m streamlit run app.py
```

3. Open the URL Streamlit prints (usually http://localhost:8501) and upload a PDF/image to try the demo cases.

Notes:
- Put any API keys or credentials in a `.env` file (app loads dotenv). If you don't provide keys the app will still run using local OCR and heuristics where available.
- For best PDF extraction install PyMuPDF (already listed in requirements) and ensure the system can open/parse the files.

---

## What the app does

1. Accepts uploaded documents (PDF / images).
2. Runs OCR and/or model extraction to locate fields of interest (name, DOB, IDs, scores, marks, organization, etc.).
3. Normalizes and validates fields (date formats, numeric normalization, basic checks).
4. Produces a verification result with a score, reasons, and per-field diagnostics.
5. Saves the case (optional) and displays a human-friendly review UI.

---

## Architecture (short)

```
app.py            # Streamlit UI + orchestration
modules/          # Core processing
  extractor.py    # Extraction logic (multi-model fallback + JSON matching)
  ocr.py          # Image/PDF handling & OCR helpers
  verifier.py     # Verification pipeline and scoring
data/             # Example demo cases
database.py       # Lightweight persistence helpers
```

app.py ties the pieces together: it loads demo cases, captures file uploads, calls extractor/ocr and verifier, and renders the results in Streamlit pages.

---

## Configuration

- .env: Place API keys for optional services (e.g. Google GenAI) here. The code checks for these and will fall back to local methods if not available.
- requirements.txt: primary Python dependencies

Recommended env vars (example):
```
GOOGLE_API_KEY=your_key_here
OTHER_OCR_KEY=...
```

---

## Development

- Run tests: `pytest`
- Add a new extraction model: update `modules/extractor.py` list of models and add dispatch logic (search for the GEMINI / model list in that file).
- Add or tune verification rules in `modules/verifier.py` (case-handling live in verifier and saved demo cases in `data/demo_cases.json`).

---

## Examples / CLI snippets

Extract text from a PDF using app's internals (example, not a provided CLI):

```py
# (pseudo) use modules.extractor and modules.ocr to parse a PDF
from modules import extractor, ocr
text = ocr.extract_pdf_text(open('example.pdf','rb').read())
fields = extractor.extract_fields(text)
```

---

## Troubleshooting

- If Streamlit fails to open files, check that `pymupdf` (PyMuPDF) is installed and your Python environment has permissions to read the file.
- If extracted values look garbled on scanned documents, try higher-resolution scans or enable model extraction backends in `.env`.

---

## Contributing

Contributions are welcome. Suggestions:
- Add unit tests for new rules under `test_*.py`.
- Add more demo cases to `data/demo_cases.json`.
- Make extraction/verification configurable via a YAML/JSON config file.

---

## License

Add a license file if you intend to open-source formally. (No license file is included in this repo.)

---

If you'd like, I can open a PR that replaces README.md with this improved content or tweak any section further (more examples, badges, or a short GIF for the UI).