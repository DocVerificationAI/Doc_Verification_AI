VeriDoc AI — SIH1652 Prototype
Zero-cost local prototype for AI-assisted document extraction and verification.
Run
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
# .venv\Scripts\activate.bat
pip install -r requirements.txt
python -m streamlit run app.py
The app supports:
GATE scorecard
Marksheet
Experience certificate
PDF text extraction with PyMuPDF
OCR fallback for scanned PDFs/images with RapidOCR
Field extraction
normalization and fuzzy name matching
deterministic validation for numeric/date fields
confidence scoring
verified / mismatch / human-review outcomes
verifier queue and audit trail
three guaranteed demo cases
No paid API or cloud service is required.