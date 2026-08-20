from pathlib import Path
from io import BytesIO
import re
import numpy as np
from PIL import Image
import pymupdf
from rapidocr import RapidOCR
 
_OCR = None
 
def get_ocr():
    global _OCR
    if _OCR is None:
        _OCR = RapidOCR()
    return _OCR
 
def extract_pdf_text(data: bytes):
    """Try native PDF text first. Returns text and average text confidence placeholder."""
    doc = pymupdf.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        txt = page.get_text("text")
        if txt and txt.strip():
            pages.append(txt.strip())
    doc.close()
    text = "\n".join(pages).strip()
    return text
 
def pdf_pages_as_images(data: bytes, max_pages=3):
    doc = pymupdf.open(stream=data, filetype="pdf")
    images = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1.8, 1.8), alpha=False)
        images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    doc.close()
    return images
 
def ocr_image(image: Image.Image):
    engine = get_ocr()
    arr = np.array(image.convert("RGB"))
    result = engine(arr)
    txts = list(result.txts or [])
    scores = [float(x) for x in (result.scores or [])]
    text = "\n".join(txts)
    avg = sum(scores) / len(scores) if scores else 0.0
    return text, avg, list(zip(txts, scores))
 
def extract_document(data: bytes, filename: str):
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        text = extract_pdf_text(data)
        # If it is a digital/text PDF, no OCR is necessary.
        if len(re.sub(r"\s+", "", text)) >= 30:
            return {
                "text": text,
                "ocr_confidence": 0.98,
                "method": "Native PDF text extraction",
                "details": []
            }
        images = pdf_pages_as_images(data)
        chunks, scores, details = [], [], []
        for image in images:
            t, s, d = ocr_image(image)
            chunks.append(t)
            scores.append(s)
            details.extend(d)
        avg = sum(scores) / len(scores) if scores else 0.0
        return {
            "text": "\n".join(chunks),
            "ocr_confidence": avg,
            "method": "RapidOCR on scanned PDF",
            "details": details
        }
 
    image = Image.open(BytesIO(data)).convert("RGB")
    text, avg, details = ocr_image(image)
    return {
        "text": text,
        "ocr_confidence": avg,
        "method": "RapidOCR on image",
        "details": details
    }