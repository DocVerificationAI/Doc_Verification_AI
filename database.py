import sqlite3
import json
from datetime import datetime


DATABASE_NAME = "veridoc.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # -----------------------------------
    # TABLE 1: Verification cases
    # -----------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_cases (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT UNIQUE NOT NULL,

            document_type TEXT NOT NULL,

            status TEXT NOT NULL,

            overall_confidence REAL,

            extraction_confidence REAL,

            application_data TEXT,

            extracted_data TEXT,

            source TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT
        )
    """)

    # -----------------------------------
    # TABLE 2: Field verification results
    # -----------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT NOT NULL,

            field_name TEXT NOT NULL,

            application_value TEXT,

            document_value TEXT,

            status TEXT,

            confidence REAL,

            reason TEXT,

            FOREIGN KEY(case_id)
                REFERENCES verification_cases(case_id)
        )
    """)

    # -----------------------------------
    # TABLE 3: Human review
    # -----------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS human_reviews (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT NOT NULL,

            action TEXT NOT NULL,

            reviewer_note TEXT,

            reviewed_at TEXT NOT NULL,

            FOREIGN KEY(case_id)
                REFERENCES verification_cases(case_id)
        )
    """)

    # -----------------------------------
    # TABLE 4: Audit log
    # -----------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT,

            action TEXT NOT NULL,

            details TEXT,

            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

    print("Database initialized successfully.")


def save_verification_case(
    result,
    application_data,
    document_type,
    source,
    extraction_confidence
):

    connection = get_connection()
    cursor = connection.cursor()

    case_id = result["case_id"]

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Save main verification case
    cursor.execute("""
        INSERT OR REPLACE INTO verification_cases (

            case_id,
            document_type,
            status,
            overall_confidence,
            extraction_confidence,
            application_data,
            extracted_data,
            source,
            created_at

        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        case_id,

        document_type,

        result["status"],

        result.get("overall_confidence"),

        extraction_confidence,

        json.dumps(
            application_data,
            ensure_ascii=False
        ),

        json.dumps(
            result.get("extracted", {}),
            ensure_ascii=False
        ),

        source,

        created_at
    ))

    # Remove old field results for this case
    cursor.execute("""
        DELETE FROM field_results
        WHERE case_id = ?
    """, (case_id,))

    # Save each field verification result
    for field in result.get("fields", []):

        cursor.execute("""
            INSERT INTO field_results (

                case_id,
                field_name,
                application_value,
                document_value,
                status,
                confidence,
                reason

            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            case_id,

            field.get("field"),

            str(
                field.get(
                    "application",
                    ""
                )
            ),

            str(
                field.get(
                    "document",
                    ""
                )
            ),

            field.get("status"),

            field.get("confidence"),

            field.get("reason")
        ))

    connection.commit()
    connection.close()

    print(
        f"Verification case {case_id} "
        f"saved to database."
    )


def save_human_review(
    case_id,
    action,
    reviewer_note
):

    connection = get_connection()
    cursor = connection.cursor()

    reviewed_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Save review history
    cursor.execute("""
        INSERT INTO human_reviews (

            case_id,
            action,
            reviewer_note,
            reviewed_at

        ) VALUES (?, ?, ?, ?)
    """, (

        case_id,
        action,
        reviewer_note,
        reviewed_at
    ))

    # Update main case status
    if action == "APPROVED":
        new_status = "APPROVED"
    elif action == "REJECTED":
        new_status = "REJECTED"
    else:
        new_status = "REVIEW"

    cursor.execute("""
        UPDATE verification_cases

        SET
            status = ?,
            updated_at = ?

        WHERE case_id = ?
    """, (
        new_status,
        reviewed_at,
        case_id
    ))

    connection.commit()
    connection.close()

    print(
        f"Human review saved for {case_id} (status: {new_status})."
    )


def save_audit_log(
    case_id,
    action,
    details=""
):

    connection = get_connection()
    cursor = connection.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO audit_log (

            case_id,
            action,
            details,
            created_at

        ) VALUES (?, ?, ?, ?)
    """, (

        case_id,
        action,
        details,
        created_at
    ))

    connection.commit()
    connection.close()


def get_all_cases():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *

        FROM verification_cases

        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_review_cases():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *

        FROM verification_cases

        WHERE status IN ('REVIEW', 'MISMATCH')

        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_case_field_results(case_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *

        FROM field_results

        WHERE case_id = ?
    """, (case_id,))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def load_all_cases():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM verification_cases
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()

    cases = []
    for row in rows:
        case_dict = dict(row)
        case_id = case_dict["case_id"]

        # Load field results
        cursor.execute("""
            SELECT * FROM field_results WHERE case_id = ?
        """, (case_id,))
        field_rows = cursor.fetchall()
        fields = [
            {
                "field": f["field_name"],
                "application": f["application_value"],
                "document": f["document_value"],
                "status": f["status"],
                "confidence": f["confidence"],
                "reason": f["reason"]
            }
            for f in field_rows
        ]

        # Load latest human review
        cursor.execute("""
            SELECT * FROM human_reviews WHERE case_id = ? ORDER BY id DESC LIMIT 1
        """, (case_id,))
        review_row = cursor.fetchone()
        human_review = None
        if review_row:
            human_review = {
                "action": review_row["action"],
                "note": review_row["reviewer_note"],
                "reviewed_at": review_row["reviewed_at"]
            }

        app_data = {}
        try:
            if case_dict.get("application_data"):
                app_data = json.loads(case_dict["application_data"])
        except Exception:
            pass

        result = {
            "case_id": case_id,
            "status": case_dict["status"],
            "overall_confidence": case_dict.get("overall_confidence", 0),
            "fields": fields,
            "reason": (
                "Review decision: " + human_review["action"]
                if human_review
                else ("All required fields matched." if case_dict["status"] in ("VERIFIED", "APPROVED") else "Verification flagged issues.")
            ),
            "human_review": human_review
        }

        cases.append({
            "case_id": case_id,
            "applicant": app_data.get("name", "Unknown"),
            "document_type": case_dict["document_type"],
            "status": case_dict["status"],
            "confidence": case_dict.get("overall_confidence", 0),
            "source": case_dict.get("source", "Live upload"),
            "result": result,
            "application": app_data,
            "human_review": human_review,
            "extraction_confidence": case_dict.get("extraction_confidence", 0.0),
            "created": case_dict.get("created_at", ""),
        })

    connection.close()
    return cases


if __name__ == "__main__":

    initialize_database()