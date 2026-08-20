import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client()

# Waterfall list of models for high-availability & quota resilience
GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
]

DOC_FIELDS = {
    "GATE Scorecard": [
        "name",
        "gate_score",
        "registration_number",
        "year",
    ],

    "Marksheet": [
        "name",
        "dob",
        "roll_number",
        "total_marks",
        "percentage",
    ],

    "Experience Certificate": [
        "name",
        "organization",
        "designation",
        "start_date",
        "end_date",
    ],
}


def clean_json_response(text):
    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    # Extract JSON object substring if model includes surrounding markdown or notes
    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        text = json_match.group(0)
    else:
        text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def extract_fields(
    ocr_text,
    doc_type,
    file_bytes=None,
    mime_type=None,
):
    """
    Extract document fields using Gemini Vision with multi-model fallback.
    """
    required_fields = DOC_FIELDS.get(doc_type, [])

    prompt = f"""
You are an AI document information extractor for an enterprise document verification system.

The document may be written in English, Hindi (Devanagari), or a mixture of languages.

DOCUMENT TYPE:
{doc_type}

You must extract ONLY these fields:
{required_fields}

IMPORTANT INSTRUCTIONS:
1. The original document is provided as the primary source of truth.
2. OCR text may also be provided below as supporting reference.
3. Read the original document directly and accurately.

OCR TEXT FOR REFERENCE:
----------------
{ocr_text}
----------------

LANGUAGE RULES:
1. ALL extracted text values must be returned in English/Latin script.
2. If a person's name or father's name is written in Hindi/Devanagari, transliterate it to English/Latin letters.
   Examples:
   आरव कुमार -> Aarav Kumar
   राहुल शर्मा -> Rahul Sharma
   सीमा देवी -> Seema Devi
3. If an organization/board is written in Hindi, return its standard English/Latin representation.
4. Dates must be returned in normalized DD/MM/YYYY format whenever day, month, and year are visible.
5. Numbers, scores, marks (e.g. 468/600), percentages (e.g. 78.00%), roll numbers, and registration numbers must remain unchanged.
6. If a field cannot be confidently found, return null.
7. Return ONLY valid JSON with EXACTLY the requested field keys.
"""

    contents = []

    # Add original PDF/image for Gemini Vision
    if file_bytes and mime_type:
        document_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=mime_type,
        )
        contents.append(document_part)
        print(f"Gemini Vision active. Ingesting original document ({mime_type})")
    else:
        print("Original document not available. Using OCR text fallback.")

    contents.append(prompt)

    # Multi-model waterfall with fallback resilience
    last_error = None
    for model_name in GEMINI_MODELS:
        try:
            print(f"Attempting Gemini extraction with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )

            if response and response.text:
                extracted = clean_json_response(response.text)
                print(f"Extraction successful using {model_name}: {extracted}")

                # Ensure every expected field exists
                return {
                    field: extracted.get(field)
                    for field in required_fields
                }

        except Exception as e:
            print(f"Gemini extraction notice ({model_name}): {e}")
            last_error = e
            continue

    print(f"All Gemini models exhausted. Final error: {last_error}")
    return {
        field: None
        for field in required_fields
    }