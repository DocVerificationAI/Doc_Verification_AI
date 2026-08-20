import re
import os
import json
from datetime import datetime

from rapidfuzz.fuzz import ratio
from google import genai
from dotenv import load_dotenv


# ---------------------------------
# LOAD GEMINI API KEY
# ---------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=GEMINI_API_KEY
)

GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
]


# ---------------------------------
# TEXT NORMALIZATION
# ---------------------------------

def norm_text(value):

    text = str(value or "").lower().strip()

    return re.sub(
        r"[^a-z0-9]",
        "",
        text
    )


# ---------------------------------
# NAME NORMALIZATION
# ---------------------------------

def norm_name(value):

    text = str(value or "").strip()

    # Remove common titles
    titles = [
        "mr.",
        "mr",
        "mrs.",
        "mrs",
        "ms.",
        "ms",
        "dr.",
        "dr",
        "prof.",
        "prof"
    ]

    text_lower = text.lower().strip()

    for title in titles:

        if text_lower.startswith(title + " "):

            text = text[len(title):].strip()

            break

    return norm_text(text)


# ---------------------------------
# DATE & YEAR HELPER FUNCTIONS
# ---------------------------------

DATE_FIELDS = {
    "dob",
    "date_of_birth",
    "start_date",
    "end_date",
    "issue_date",
    "date",
}

YEAR_FIELDS = {
    "year",
    "passing_year",
    "year_of_passing",
    "graduating_year",
    "graduation_year",
    "admission_year",
}


def clean_date_str(value):
    text = str(value or "").strip()
    text = text.replace(".", "/").replace("-", "/")
    # Remove redundant whitespace around slashes
    text = re.sub(r"\s*/\s*", "/", text)
    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text)
    return text


def parse_date(value):
    if not value:
        return None

    text = clean_date_str(value)

    formats = [
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%d %B, %Y",
        "%d %b, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    return None


def extract_year(value):
    if not value:
        return None

    # Try full date parsing first
    dt = parse_date(value)
    if dt:
        return dt.year

    text = str(value or "").strip()

    # Look for 4-digit year (1900-2099)
    match_4digit = re.search(r"\b(19\d\d|20\d\d)\b", text)
    if match_4digit:
        return int(match_4digit.group(1))

    # Check standalone digits
    digits_only = re.sub(r"\D", "", text)
    if len(digits_only) == 4 and (
        digits_only.startswith("19") or digits_only.startswith("20")
    ):
        return int(digits_only)
    elif len(digits_only) == 2:
        yr = int(digits_only)
        return 2000 + yr if yr < 50 else 1900 + yr

    return None


def norm_date(value):
    dt = parse_date(value)
    if dt:
        return dt.isoformat()
    return norm_text(clean_date_str(value))


# ---------------------------------
# STRICT FIELD TYPES
# ---------------------------------

STRICT_NUMERIC_FIELDS = {
    "gate_score",
    "total_marks",
    "score",
    "marks",
    "roll_number",
    "registration_number",
}


# ---------------------------------
# SEMANTIC AI VALIDATION
# ---------------------------------

def ai_compare_text_fields(
    fields_to_check
):

    if not fields_to_check:

        return {}

    prompt = f"""
You are an AI validation assistant in a
document verification system.

Compare application values with values
extracted from an uploaded document.

Your task is to determine whether each pair
reasonably refers to the same real-world value.

Be conservative.

IMPORTANT RULES:

1. Ignore capitalization differences.

2. Ignore harmless punctuation differences.

3. For person names, honorifics such as
Mr, Mrs, Ms, Dr and Prof should be ignored.

Example:

"Ismail Ibrahim Nassar"
and
"Mr. Ismail Ibrahim Nassar"

should be MATCH.

4. For organization names, determine whether
a short common organization name and a longer
official/legal name reasonably refer to the
same organization.

Example:

"Kirby"
and
"KIRBY BUILDING SYSTEMS KUWAIT K.S.C."

can be MATCH if the shorter name clearly
identifies the organization.

Do NOT match unrelated organizations merely
because one word is similar.

5. For job designations, compare semantic
meaning conservatively.

6. If you are not confident, return REVIEW.

7. Do not automatically match names that are
meaningfully different.

Return ONLY valid JSON.

Use this format:

{{
    "field_name": {{
        "status": "MATCH or REVIEW or MISMATCH",
        "confidence": 0-100,
        "reason": "short explanation"
    }}
}}

FIELDS TO COMPARE:

{json.dumps(fields_to_check, ensure_ascii=False)}
"""

    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            raw_text = response.text.strip()

            # Extract JSON object substring
            json_match = re.search(r"\{[\s\S]*\}", raw_text)
            if json_match:
                raw_text = json_match.group(0)
            else:
                raw_text = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
                raw_text = re.sub(r"^```\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            return json.loads(raw_text)

        except Exception as error:
            print(f"AI validation notice ({model_name}):", error)
            continue

    return {}


# ---------------------------------
# COMPARE STRICT FIELD
# ---------------------------------

def compare_strict_field(
    field,
    app_value,
    doc_value,
    ocr_confidence
):

    app = str(app_value or "").strip()

    doc = str(doc_value or "").strip()


    # -----------------------------
    # DATE COMPARISON
    # -----------------------------

    if field in DATE_FIELDS:

        app_dt = parse_date(app)
        doc_dt = parse_date(doc)

        if app_dt and doc_dt:
            if app_dt == doc_dt:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "MATCH",
                    "confidence": 99,
                    "reason": "Dates match after format normalization.",
                }

            year_diff = abs(app_dt.year - doc_dt.year)
            if year_diff >= 2:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "MISMATCH",
                    "confidence": 95,
                    "reason": f"Significant year difference in date ({app_dt.year} vs {doc_dt.year}).",
                }
            elif year_diff == 1:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "REVIEW",
                    "confidence": 70,
                    "reason": f"Minor year difference in date ({app_dt.year} vs {doc_dt.year}). Human review recommended.",
                }
            else:
                # Same year, but day and/or month differ
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "REVIEW",
                    "confidence": 75,
                    "reason": f"Date values differ in day/month with matching year ({app} vs {doc}). Human review recommended.",
                }

        # Fallback if full date parsing was partial
        app_year = extract_year(app)
        doc_year = extract_year(doc)

        if app_year and doc_year:
            year_diff = abs(app_year - doc_year)
            if year_diff >= 2:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "MISMATCH",
                    "confidence": 95,
                    "reason": f"Significant year difference in date ({app_year} vs {doc_year}).",
                }
            elif year_diff == 1:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "REVIEW",
                    "confidence": 70,
                    "reason": f"Minor year difference in date ({app_year} vs {doc_year}). Human review recommended.",
                }
            else:
                if norm_text(app) == norm_text(doc):
                    return {
                        "field": field,
                        "application": app,
                        "document": doc,
                        "status": "MATCH",
                        "confidence": 99,
                        "reason": "Dates match after format normalization.",
                    }
                else:
                    return {
                        "field": field,
                        "application": app,
                        "document": doc,
                        "status": "REVIEW",
                        "confidence": 75,
                        "reason": f"Minor date difference ({app} vs {doc}). Human review recommended.",
                    }

        # If neither date nor year could be extracted
        match = norm_text(app) == norm_text(doc)
        return {
            "field": field,
            "application": app,
            "document": doc,
            "status": (
                "MATCH"
                if match
                else ("REVIEW" if ocr_confidence < 0.95 else "MISMATCH")
            ),
            "confidence": 99 if match else 90,
            "reason": (
                "Dates match after format normalization."
                if match
                else "Date values are different."
            ),
        }

    # -----------------------------
    # YEAR COMPARISON
    # -----------------------------

    if field in YEAR_FIELDS:

        app_year = extract_year(app)
        doc_year = extract_year(doc)

        if app_year and doc_year:
            if app_year == doc_year:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "MATCH",
                    "confidence": 99,
                    "reason": "Years match.",
                }

            year_diff = abs(app_year - doc_year)
            if year_diff >= 2:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "MISMATCH",
                    "confidence": 95,
                    "reason": f"Significant year difference detected ({app_year} vs {doc_year}).",
                }
            else:
                return {
                    "field": field,
                    "application": app,
                    "document": doc,
                    "status": "REVIEW",
                    "confidence": 70,
                    "reason": f"Minor year difference ({app_year} vs {doc_year}). Human review recommended.",
                }

        # Fallback if cannot extract 4-digit years
        match = norm_text(app) == norm_text(doc)
        return {
            "field": field,
            "application": app,
            "document": doc,
            "status": "MATCH" if match else "MISMATCH",
            "confidence": 99 if match else 95,
            "reason": "Years match." if match else "Year values are different.",
        }


    # -----------------------------
    # PERCENTAGE
    # -----------------------------

    if field == "percentage":

        try:

            app_number = float(
                app.replace("%", "")
            )

            doc_number = float(
                doc.replace("%", "")
            )

            match = (
                abs(
                    app_number -
                    doc_number
                ) < 0.01
            )

        except Exception:

            match = (
                norm_text(app) ==
                norm_text(doc)
            )

        return {

            "field": field,

            "application": app,

            "document": doc,

            "status":
                "MATCH"
                if match
                else (
                    "REVIEW"
                    if ocr_confidence < 0.95
                    else "MISMATCH"
                ),

            "confidence":
                99
                if match
                else 95,

            "reason":
                "Numeric values match."
                if match
                else "Numeric values are different."
        }


    # -----------------------------
    # STRICT NUMERIC FIELDS
    # -----------------------------

    if field == "gate_score":

        match = re.sub(r"\D", "", app) == re.sub(r"\D", "", doc)
        conf = min(99, round(80 + 19 * ocr_confidence))

        return {

            "field": field,

            "application": app,

            "document": doc,

            "status":
                "MATCH"
                if match
                else (
                    "REVIEW"
                    if ocr_confidence < 0.95
                    else "MISMATCH"
                ),

            "confidence": conf,

            "reason":
                "Numeric values match."
                if match
                else "Numeric values are different."
        }


    if field == "total_marks":

        # Extract the first number from each value.
        # Examples:
        # "468" -> 468
        # "468/600" -> 468
        # "468 out of 600" -> 468
        # "Marks Obtained: 468" -> 468

        app_numbers = re.findall(r"\d+(?:\.\d+)?", app)
        doc_numbers = re.findall(r"\d+(?:\.\d+)?", doc)

        if app_numbers and doc_numbers:

            app_marks = float(app_numbers[0])
            doc_marks = float(doc_numbers[0])

            match = abs(app_marks - doc_marks) < 0.01

        else:
            match = False

        conf = (
            min(99, round(80 + 19 * ocr_confidence))
            if match
            else min(99, round(85 + 14 * ocr_confidence))
        )

        return {

            "field": field,

            "application": app,

            "document": doc,

            "status":
                "MATCH"
                if match
                else (
                    "REVIEW"
                    if ocr_confidence < 0.95
                    else "MISMATCH"
                ),

            "confidence": conf,

            "reason":
                "Numeric values match."
                if match
                else "Numeric values are different."
        }

    if field in STRICT_NUMERIC_FIELDS:

        app_number = re.sub(
            r"\D",
            "",
            app
        )

        doc_number = re.sub(
            r"\D",
            "",
            doc
        )

        match = (
            app_number ==
            doc_number
        )

        return {

            "field": field,

            "application": app,

            "document": doc,

            "status":
                "MATCH"
                if match
                else (
                    "REVIEW"
                    if ocr_confidence < 0.95
                    else "MISMATCH"
                ),

            "confidence":
                99
                if match
                else 95,

            "reason":
                "Exact numeric values match."
                if match
                else "Numeric values are different."
        }


    return None


# ---------------------------------
# MAIN VERIFICATION FUNCTION
# ---------------------------------

def verify(
    application,
    extracted,
    ocr_confidence,
    fields
):

    results = []

    semantic_fields = {}

    # ---------------------------------
    # FIRST PASS:
    # MISSING + STRICT CHECKS
    # ---------------------------------

    for field in fields:

        app_value = str(
            application.get(
                field,
                ""
            )
        ).strip()

        doc_value = str(
            extracted.get(
                field,
                ""
            )
        ).strip()


        # -----------------------------
        # MISSING DATA
        # -----------------------------

        if not app_value or not doc_value:

            results.append({

                "field": field,

                "application": app_value,

                "document": doc_value,

                "status": "REVIEW",

                "confidence": 40,

                "reason":
                    "Required value could not be extracted."
            })

            continue


        # -----------------------------
        # STRICT FIELD VALIDATION
        # -----------------------------

        strict_result = compare_strict_field(

            field,

            app_value,

            doc_value,

            ocr_confidence
        )

        if strict_result:

            results.append(
                strict_result
            )

            continue


        # -----------------------------
        # NAME NORMALIZATION
        # -----------------------------

        if field == "name":

            app_name = norm_name(
                app_value
            )

            doc_name = norm_name(
                doc_value
            )

            if app_name == doc_name:

                results.append({

                    "field": field,

                    "application": app_value,

                    "document": doc_value,

                    "status": "MATCH",

                    "confidence": 99,

                    "reason":
                        "Names match after title and formatting normalization."
                })

                continue


        # -----------------------------
        # EXACT NORMALIZED MATCH
        # -----------------------------

        if norm_text(
            app_value
        ) == norm_text(
            doc_value
        ):

            results.append({

                "field": field,

                "application": app_value,

                "document": doc_value,

                "status": "MATCH",

                "confidence": 99,

                "reason":
                    "Values match after normalization."
            })

            continue


        # ---------------------------------
        # SEND UNCLEAR TEXT FIELD TO AI
        # ---------------------------------

        semantic_fields[field] = {

            "application":

                app_value,

            "document":

                doc_value
        }


    # ---------------------------------
    # SECOND PASS:
    # GEMINI SEMANTIC VALIDATION
    # ---------------------------------

    ai_results = ai_compare_text_fields(
        semantic_fields
    )


    for field, values in semantic_fields.items():

        ai_result = ai_results.get(
            field,
            {}
        )

        status = str(
            ai_result.get(
                "status",
                "REVIEW"
            )
        ).upper()

        confidence = ai_result.get(
            "confidence",
            60
        )

        reason = ai_result.get(
            "reason",
            "AI validation was unable to reach a confident conclusion."
        )


        # Safety check
        if status not in {

            "MATCH",
            "MISMATCH",
            "REVIEW"

        }:

            status = "REVIEW"


        results.append({

            "field": field,

            "application":

                values["application"],

            "document":

                values["document"],

            "status":

                status,

            "confidence":

                confidence,

            "reason":

                reason
        })


    # ---------------------------------
    # SORT RESULTS
    # ---------------------------------

    field_order = {

        field: index

        for index, field in enumerate(
            fields
        )
    }

    results.sort(

        key=lambda result:
        field_order.get(
            result["field"],
            999
        )
    )


    # ---------------------------------
    # FINAL DECISION
    # ---------------------------------

    if not results:

        return {

            "status":

                "REVIEW",

            "overall_confidence":

                0,

            "fields":

                [],

            "reason":

                "No fields available."
        }


    mismatches = [

        result

        for result in results

        if result["status"] == "MISMATCH"
    ]


    reviews = [

        result

        for result in results

        if result["status"] == "REVIEW"
    ]


    average_confidence = round(

        sum(

            float(
                result["confidence"]
            )

            for result in results

        )

        / len(results)

    )


    if mismatches:

        final_status = "MISMATCH"


    elif reviews or ocr_confidence < 0.70:

        final_status = "REVIEW"


    else:

        final_status = "VERIFIED"


    return {

        "status":

            final_status,

        "overall_confidence":

            average_confidence,

        "fields":

            results,

        "reason":

            (
                "One or more high-confidence mismatches were detected."

                if mismatches

                else

                "Human review is recommended because one or more values are uncertain."

                if reviews or ocr_confidence < 0.70

                else

                "All required fields matched with high confidence."
            )
    }