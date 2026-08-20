from pathlib import Path
from datetime import datetime
import json

import pandas as pd
import streamlit as st

from modules.ocr import extract_document
from modules.extractor import extract_fields, DOC_FIELDS
from modules.verifier import verify
from database import (
    initialize_database,
    save_verification_case,
    save_human_review,
    load_all_cases,
)

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="VeriDoc AI — Enterprise Verification",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).parent
DATA = BASE / "data"

initialize_database()


# -------------------------------------------------
# ENTERPRISE STYLING: WHITE SIDEBAR + OBSIDIAN CANVAS
# -------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    * {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Streamlit Header (Transparent with pointer events for controls) */
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none;
        z-index: 9999 !important;
    }

    header[data-testid="stHeader"] > * {
        pointer-events: auto;
    }

    /* Floating Expand/Open Sidebar Control when sidebar is collapsed */
    div[data-testid="stSidebarCollapsedControl"],
    button[data-testid="stSidebarCollapsedControl"],
    div[data-testid="collapsedControl"],
    header[data-testid="stHeader"] button[data-testid="stSidebarCollapsedControl"] {
        background: #18181b !important;
        border: 1px solid #3f3f46 !important;
        border-radius: 10px !important;
        padding: 0.45rem 0.55rem !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        margin-left: 0.5rem;
        margin-top: 0.5rem;
    }

    div[data-testid="stSidebarCollapsedControl"]:hover,
    button[data-testid="stSidebarCollapsedControl"]:hover,
    div[data-testid="collapsedControl"]:hover {
        background: #27272a !important;
        border-color: #71717a !important;
        transform: scale(1.05);
    }

    div[data-testid="stSidebarCollapsedControl"] svg,
    button[data-testid="stSidebarCollapsedControl"] svg,
    div[data-testid="collapsedControl"] svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }

    /* Global Dark Canvas */
    .stApp {
        background: #08080a;
        color: #f1f5f9;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }

    /* =========================================
       WHITE ENTERPRISE SIDEBAR
       ========================================= */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.03);
    }

    section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
        padding: 1.2rem 1.15rem 1.5rem 1.15rem !important;
        background: #ffffff !important;
    }

    /* Prominent Sidebar Minimize Button in White Header */
    button[data-testid="stSidebarCollapseButton"],
    div[data-testid="stSidebarCollapseButton"] button,
    div[data-testid="stSidebarHeader"] button,
    section[data-testid="stSidebar"] button[kind="header"] {
        background: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.2s ease !important;
        opacity: 1 !important;
        visibility: visible !important;
        cursor: pointer !important;
    }

    button[data-testid="stSidebarCollapseButton"]:hover,
    div[data-testid="stSidebarCollapseButton"] button:hover,
    div[data-testid="stSidebarHeader"] button:hover,
    section[data-testid="stSidebar"] button[kind="header"]:hover {
        background: #09090b !important;
        border-color: #09090b !important;
        color: #ffffff !important;
    }

    button[data-testid="stSidebarCollapseButton"] svg,
    div[data-testid="stSidebarCollapseButton"] svg,
    div[data-testid="stSidebarHeader"] svg,
    section[data-testid="stSidebar"] button[kind="header"] svg {
        fill: #0f172a !important;
        stroke: #0f172a !important;
        color: #0f172a !important;
    }

    button[data-testid="stSidebarCollapseButton"]:hover svg,
    div[data-testid="stSidebarCollapseButton"] button:hover svg,
    div[data-testid="stSidebarHeader"] button:hover svg,
    section[data-testid="stSidebar"] button[kind="header"]:hover svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }

    /* Sidebar Brand */
    .brand-header {
        padding: 0.2rem 0.2rem 1.3rem 0.2rem;
        border-bottom: 1px solid #f1f5f9;
        margin-bottom: 1.25rem;
    }

    .brand-title-wrap {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.85rem;
    }

    .brand-logo-icon {
        width: 38px;
        height: 38px;
        background: #09090b;
        color: #ffffff;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.25rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }

    .brand-title {
        color: #09090b !important;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.1;
    }

    .brand-subtitle {
        color: #64748b;
        font-size: 0.7rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 700;
    }

    .system-status-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 20px;
        padding: 0.3rem 0.65rem;
    }

    .status-dot-pulse {
        width: 7px;
        height: 7px;
        background: #16a34a;
        border-radius: 50%;
        box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.2);
    }

    .status-chip-text {
        color: #15803d;
        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Sidebar Navigation Label */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        color: #64748b !important;
        font-size: 0.72rem !important;
        font-weight: 750 !important;
        letter-spacing: 0.14em !important;
        text-transform: uppercase !important;
        margin-bottom: 0.5rem !important;
    }

    /* Sidebar Radio Options */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 0.45rem !important;
    }

    section[data-testid="stSidebar"] label[data-baseweb="radio"] {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.2rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
    }

    section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
        background: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
        transform: translateX(2px);
    }

    section[data-testid="stSidebar"] label[data-baseweb="radio"] div,
    section[data-testid="stSidebar"] label[data-baseweb="radio"] p,
    section[data-testid="stSidebar"] label[data-baseweb="radio"] span {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }

    /* Selected State: Contrast Black Pill */
    section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
        background: #09090b !important;
        border-color: #09090b !important;
        box-shadow: 0 4px 14px rgba(9, 9, 11, 0.15) !important;
        transform: translateX(3px);
    }

    section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) div,
    section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) p,
    section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) span {
        color: #ffffff !important;
        font-weight: 750 !important;
    }

    /* =========================================
       MAIN CANVAS & HERO DESIGN
       ========================================= */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 750 !important;
        letter-spacing: -0.025em;
    }

    .hero {
        background: linear-gradient(135deg, #131316 0%, #09090b 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 2.2rem 2.6rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45);
        position: relative;
        overflow: hidden;
    }

    .hero::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    }

    .hero-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #cbd5e1;
        margin-bottom: 0.75rem;
    }

    .hero-title {
        color: #ffffff;
        font-size: clamp(2rem, 3.8vw, 2.75rem);
        line-height: 1.15;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin: 0 0 0.6rem 0;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.96rem;
        line-height: 1.6;
        max-width: 820px;
    }

    /* Metric KPI Cards */
    .metric-card {
        background: linear-gradient(180deg, #111114 0%, #09090b 100%);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 1.35rem 1.45rem;
        min-height: 130px;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: #334155;
    }

    .metric-card.verified::before {
        background: #10b981;
    }

    .metric-card.mismatch::before {
        background: #ef4444;
    }

    .metric-card.review::before {
        background: #f59e0b;
    }

    .metric-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
    }

    .metric-label {
        color: #8899a6;
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.85rem;
    }

    .metric-value {
        color: #ffffff;
        font-size: 2.15rem;
        line-height: 1;
        font-weight: 800;
        letter-spacing: -0.04em;
    }

    /* General Panel / Container */
    .panel {
        background: linear-gradient(180deg, #0e0e11 0%, #08080a 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    /* Result banner */
    .result-banner {
        background: linear-gradient(135deg, #131318 0%, #0a0a0c 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        padding: 1.4rem 1.7rem;
        margin: 1.3rem 0 1.2rem 0;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }

    .result-status {
        color: #ffffff;
        font-size: 1.65rem;
        font-weight: 800;
        margin-top: 0.25rem;
        letter-spacing: -0.02em;
    }

    .result-message {
        color: #94a3b8;
        margin-top: 0.35rem;
        font-size: 0.95rem;
    }

    /* Inputs */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    textarea {
        background: #0d0d10 !important;
        border-color: #27272a !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }

    input, textarea {
        color: #ffffff !important;
    }

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    textarea:focus {
        border-color: #94a3b8 !important;
        box-shadow: 0 0 0 1px #94a3b8 !important;
    }

    /* Primary & Standard Buttons */
    .stButton > button {
        background: #ffffff !important;
        color: #09090b !important;
        border: 1px solid #ffffff !important;
        border-radius: 10px !important;
        min-height: 44px;
        font-weight: 750;
        letter-spacing: 0.02em;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    .stButton > button:hover {
        background: #e2e8f0 !important;
        border-color: #e2e8f0 !important;
        color: #09090b !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(255, 255, 255, 0.2);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* File uploader */
    section[data-testid="stFileUploaderDropzone"] {
        background: #0d0d10 !important;
        border: 1px dashed #3f3f46 !important;
        border-radius: 14px !important;
        transition: border-color 0.2s ease;
    }

    section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #71717a !important;
    }

    /* Dataframe & Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #27272a;
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stExpander"] {
        background: #0d0d10;
        border: 1px solid #27272a;
        border-radius: 14px;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s ease;
    }

    div[data-testid="stExpander"]:hover {
        border-color: #3f3f46;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        color: #71717a !important;
        font-weight: 700 !important;
        font-size: 0.94rem !important;
        padding: 0.65rem 1.1rem !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        border-bottom-color: #ffffff !important;
    }

    /* Status bar */
    .status-line {
        background: #0d0d10;
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 0.85rem 1.1rem;
        color: #94a3b8;
        margin: 0.7rem 0 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------

if "cases" not in st.session_state:
    try:
        st.session_state.cases = load_all_cases()
    except Exception as err:
        print(f"Initial DB load notice: {err}")
        st.session_state.cases = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "review_notification" not in st.session_state:
    st.session_state.review_notification = None


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def status_icon(status):
    return {
        "VERIFIED": "✓",
        "APPROVED": "✓",
        "REJECTED": "✕",
        "MISMATCH": "✕",
        "REVIEW": "!",
    }.get(status, "•")


def next_case_id():
    existing_nums = []
    for case in st.session_state.cases:
        cid = str(case.get("case_id", ""))
        if cid.startswith("CASE-"):
            try:
                num = int(cid.split("-")[1])
                existing_nums.append(num)
            except Exception:
                pass
    next_num = max(existing_nums, default=0) + 1
    return f"CASE-{next_num:03d}"


def save_case_to_database(
    result,
    application_data,
    document_type,
    source,
    extraction_confidence,
):
    try:
        save_verification_case(
            result=result,
            application_data=application_data,
            document_type=document_type,
            source=source,
            extraction_confidence=extraction_confidence,
        )
    except Exception as error:
        print(f"Database save warning: {error}")


def add_case(
    result,
    applicant,
    doc_type,
    source="Live upload",
    extraction_confidence=0.0,
):
    case_id = result.get("case_id") or next_case_id()
    result["case_id"] = case_id

    case = {
        "case_id": case_id,
        "applicant": applicant.get("name", "Unknown"),
        "document_type": doc_type,
        "status": result["status"],
        "confidence": result["overall_confidence"],
        "source": source,
        "result": result,
        "application": applicant,
        "human_review": None,
        "extraction_confidence": extraction_confidence,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    st.session_state.cases.insert(0, case)

    save_case_to_database(
        result=result,
        application_data=applicant,
        document_type=doc_type,
        source=source,
        extraction_confidence=extraction_confidence,
    )

    return case


def render_result(bundle):
    result = bundle["result"]
    status = result["status"]

    message = {
        "VERIFIED": "All required fields matched successfully with high confidence.",
        "APPROVED": "Case verified and manually approved by an analyst.",
        "MISMATCH": "A high-confidence contradiction was detected between application and document.",
        "REJECTED": "Case flagged with significant discrepancy and rejected.",
        "REVIEW": "The AI could not verify one or more values with sufficient certainty.",
    }.get(status, result.get("reason", ""))

    st.markdown(
        f"""
        <div class="result-banner">
            <div class="hero-tag">VERIFICATION VERDICT</div>
            <div class="result-status">{status_icon(status)} {status}</div>
            <div class="result-message">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Overall Confidence",
            f'{result["overall_confidence"]}%',
        )

    with c2:
        extraction_confidence = bundle.get("ocr_confidence", 0) * 100
        st.metric(
            "Extraction OCR Confidence",
            f"{extraction_confidence:.0f}%",
        )

    with c3:
        st.metric(
            "Final Decision",
            status,
        )

    rows = []

    for field_result in result.get("fields", []):
        rows.append(
            {
                "Field": field_result["field"].replace("_", " ").title(),
                "Application": field_result["application"],
                "Document": field_result["document"],
                "Result": (
                    f'{status_icon(field_result["status"])} '
                    f'{field_result["status"]}'
                ),
                "Confidence": f'{field_result["confidence"]}%',
                "Reason": field_result["reason"],
            }
        )

    if rows:
        st.markdown("#### Field-by-Field Validation Details")
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Explainable AI Audit Trace"):
        st.write(result.get("reason", "No explanation was returned."))
        st.caption(
            "Enterprise AI Verification Engine. Critical or uncertain cases remain subject to human oversight."
        )

    with st.expander("Raw Extracted Document OCR Text"):
        st.code(result.get("raw_text", ""), language="text")


def run_verification(uploaded, application, doc_type):
    with st.status(
        "AI verification pipeline running...",
        expanded=True,
    ) as pipeline:
        st.write("Ingesting uploaded document bytes")

        file_bytes = uploaded.getvalue()

        raw = extract_document(
            file_bytes,
            uploaded.name,
        )

        st.write("Optical Character Recognition (OCR) completed")

        mime_type = uploaded.type
        if not mime_type:
            if uploaded.name.lower().endswith(".pdf"):
                mime_type = "application/pdf"
            elif uploaded.name.lower().endswith(".png"):
                mime_type = "image/png"
            else:
                mime_type = "image/jpeg"

        extracted = extract_fields(
            ocr_text=raw["text"],
            doc_type=doc_type,
            file_bytes=file_bytes,
            mime_type=mime_type,
        )

        st.write("Gemini Vision structured extraction completed")

        result = verify(
            application,
            extracted,
            raw["ocr_confidence"],
            DOC_FIELDS[doc_type],
        )

        st.write("Deterministic & AI comparison validation completed")

        result["raw_text"] = raw["text"]
        result["case_id"] = next_case_id()

        bundle = {
            "result": result,
            "applicant": application,
            "doc_type": doc_type,
            "method": raw.get("method", "Document extraction"),
            "ocr_confidence": raw["ocr_confidence"],
        }

        st.session_state.current_result = bundle

        add_case(
            result=result,
            applicant=application,
            doc_type=doc_type,
            source="Live upload",
            extraction_confidence=raw["ocr_confidence"],
        )

        pipeline.update(
            label="Verification pipeline completed",
            state="complete",
            expanded=False,
        )


# -------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------

st.sidebar.markdown(
    """
    <div class="brand-header">
        <div class="brand-title-wrap">
            <div class="brand-logo-icon">V</div>
            <div>
                <div class="brand-title">VERIDOC</div>
                <div class="brand-subtitle">AI Platform</div>
            </div>
        </div>
        <div class="system-status-chip">
            <span class="status-dot-pulse"></span>
            <span class="status-chip-text">System Operational</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigation Menu",
    [
        "Dashboard",
        "Verify Document",
        "Human Review",
    ],
)


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

if page == "Dashboard":
    total = len(st.session_state.cases)

    verified = sum(
        case["status"] in ("VERIFIED", "APPROVED")
        for case in st.session_state.cases
    )

    mismatch = sum(
        case["status"] in ("MISMATCH", "REJECTED")
        for case in st.session_state.cases
    )

    pending_review = sum(
        case.get("status") in ("REVIEW", "MISMATCH") and not case.get("human_review")
        for case in st.session_state.cases
    )

    st.markdown(
        """
        <div class="hero">
            <div class="hero-tag">ENTERPRISE AUDIT READY</div>
            <div class="hero-title">Verify documents with confidence.</div>
            <div class="hero-subtitle">
                Automated document extraction, intelligent cross-field validation, and streamlined human review workflows.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)

    metric_configs = [
        ("DOCUMENTS PROCESSED", total, ""),
        ("VERIFIED & APPROVED", verified, "verified"),
        ("MISMATCHES / REJECTED", mismatch, "mismatch"),
        ("PENDING REVIEW", pending_review, "review"),
    ]

    for column, (label, value, card_class) in zip(
        [m1, m2, m3, m4],
        metric_configs,
    ):
        with column:
            st.markdown(
                f"""
                <div class="metric-card {card_class}">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    st.markdown("#### Recent Verification Cases")

    if st.session_state.cases:
        table = pd.DataFrame(
            [
                {
                    "Case ID": case["case_id"],
                    "Applicant": case["applicant"],
                    "Document Type": case["document_type"],
                    "Status": f'{status_icon(case["status"])} {case["status"]}',
                    "Confidence": f'{case["confidence"]}%',
                    "Timestamp": case.get("created", ""),
                }
                for case in st.session_state.cases
            ]
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.markdown(
            """
            <div class="panel">
                <div style="color:#ffffff;font-weight:700;font-size:1.05rem;">
                    No Verification Cases Ingested
                </div>
                <div style="color:#8d8d8d;margin-top:0.4rem;">
                    Upload and verify documents to populate live verification telemetry.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -------------------------------------------------
# VERIFY DOCUMENT
# -------------------------------------------------

elif page == "Verify Document":
    st.markdown(
        """
        <div class="hero">
            <div class="hero-tag">NEW VERIFICATION PIPELINE</div>
            <div class="hero-title">Verify a document.</div>
            <div class="hero-subtitle">
                Select the certificate type, enter application metadata, upload the document asset, and initiate automated verification.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 1. Select Certificate Type")

    doc_type = st.selectbox(
        "Certificate Type",
        options=["Select certificate type..."] + list(DOC_FIELDS.keys()),
        index=0,
        help="Choose the document type you wish to ingest and cross-verify.",
        key="document_type_selector",
    )

    if doc_type == "Select certificate type...":
        st.markdown(
            '<div class="status-line">Select a certificate type to configure required verification parameters.</div>',
            unsafe_allow_html=True,
        )

    else:
        st.markdown("#### 2. Enter Application Data & Upload Document")

        left, right = st.columns([1.15, 0.85], gap="large")

        with left:
            if doc_type == "GATE Scorecard":
                st.caption("Enter the candidate details provided during application.")

                name = st.text_input(
                    "Applicant Name",
                    key="gate_name",
                )
                gate_score = st.text_input(
                    "GATE Score",
                    key="gate_score",
                )
                registration = st.text_input(
                    "Registration Number",
                    key="gate_registration",
                )
                year = st.text_input(
                    "Year Of Passing",
                    key="gate_year",
                )

                application = {
                    "name": name,
                    "gate_score": gate_score,
                    "registration_number": registration,
                    "year": year,
                }

            elif doc_type == "Marksheet":
                st.caption("Enter the academic result and student credentials.")

                name = st.text_input(
                    "Applicant Name",
                    key="marksheet_name",
                )
                dob_date = st.date_input(
                    "Date of Birth",
                    value=datetime(2005, 1, 1).date(),
                    min_value=datetime(1950, 1, 1).date(),
                    max_value=datetime.today().date(),
                    format="DD/MM/YYYY",
                    key="marksheet_dob",
                )
                dob = dob_date.strftime("%d/%m/%Y") if dob_date else ""
                roll = st.text_input(
                    "Roll Number",
                    key="marksheet_roll",
                )
                total = st.text_input(
                    "Total Marks",
                    key="marksheet_total",
                )
                percentage = st.text_input(
                    "Percentage",
                    key="marksheet_percentage",
                )

                application = {
                    "name": name,
                    "dob": dob,
                    "roll_number": roll,
                    "total_marks": total,
                    "percentage": percentage,
                }

            elif doc_type == "Experience Certificate":
                st.caption("Enter the employment verification credentials.")

                name = st.text_input(
                    "Applicant Name",
                    key="experience_name",
                )
                organization = st.text_input(
                    "Organization Name",
                    key="experience_organization",
                )
                designation = st.text_input(
                    "Designation / Title",
                    key="experience_designation",
                )
                start_date_val = st.date_input(
                    "Start Date",
                    value=datetime(2020, 1, 1).date(),
                    min_value=datetime(1970, 1, 1).date(),
                    max_value=datetime.today().date(),
                    format="DD/MM/YYYY",
                    key="experience_start",
                )
                start_date = start_date_val.strftime("%d/%m/%Y") if start_date_val else ""
                end_date_val = st.date_input(
                    "End Date",
                    value=datetime(2023, 1, 1).date(),
                    min_value=datetime(1970, 1, 1).date(),
                    max_value=datetime.today().date(),
                    format="DD/MM/YYYY",
                    key="experience_end",
                )
                end_date = end_date_val.strftime("%d/%m/%Y") if end_date_val else ""

                application = {
                    "name": name,
                    "organization": organization,
                    "designation": designation,
                    "start_date": start_date,
                    "end_date": end_date,
                }

            else:
                application = {}
                for field in DOC_FIELDS.get(doc_type, []):
                    application[field] = st.text_input(
                        field.replace("_", " ").title(),
                        key=f"{doc_type}_{field}",
                    )

        with right:
            st.caption("Upload source document asset")

            uploaded = st.file_uploader(
                "PDF, JPG, JPEG or PNG Asset",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"upload_{doc_type}",
            )

            if uploaded:
                st.success(f"Asset Loaded: {uploaded.name}")
                st.caption(f"Doc Type: {doc_type}")
                st.caption(
                    "Dual-stage validation: OCR text parsing + Gemini Vision multimodal structure comparison."
                )
            else:
                st.markdown(
                    '<div class="status-line">No document uploaded yet.</div>',
                    unsafe_allow_html=True,
                )

        st.divider()

        if st.button(
            "START AI VERIFICATION PIPELINE",
            type="primary",
            use_container_width=True,
            key=f"verify_{doc_type}",
        ):
            if uploaded is None:
                st.error("Please upload a document before starting verification.")
            else:
                missing_fields = [
                    field.replace("_", " ").title()
                    for field, value in application.items()
                    if not str(value).strip()
                ]

                if missing_fields:
                    st.error(
                        "Please complete all required fields: "
                        + ", ".join(missing_fields)
                    )
                else:
                    try:
                        run_verification(
                            uploaded=uploaded,
                            application=application,
                            doc_type=doc_type,
                        )
                    except Exception as error:
                        st.error("Verification pipeline encountered an issue.")
                        st.exception(error)

        if st.session_state.current_result:
            current = st.session_state.current_result
            if current["doc_type"] == doc_type:
                st.divider()
                render_result(current)


# -------------------------------------------------
# HUMAN REVIEW
# -------------------------------------------------

elif page == "Human Review":
    if st.session_state.review_notification:
        notif = st.session_state.review_notification
        if notif.get("type") == "success":
            st.success(notif.get("message"))
        else:
            st.warning(notif.get("message"))
        st.session_state.review_notification = None

    pending = [
        case
        for case in st.session_state.cases
        if not case.get("human_review") and case.get("status") in ("REVIEW", "MISMATCH")
    ]

    resolved = [
        case
        for case in st.session_state.cases
        if case.get("human_review") or case.get("status") in ("APPROVED", "REJECTED")
    ]

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-tag">HUMAN-IN-THE-LOOP CENTER</div>
            <div class="hero-title">Review queue.</div>
            <div class="hero-subtitle">
                {len(pending)} case(s) currently require an analyst decision. Reviewed cases are saved to decision history.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_pending, tab_history = st.tabs(
        [
            f"Pending Queue ({len(pending)})",
            f"Decision History ({len(resolved)})",
        ]
    )

    with tab_pending:
        if not pending:
            st.markdown(
                """
                <div class="panel">
                    <div style="color:#ffffff;font-weight:700;font-size:1.05rem;">
                        Queue is Clear
                    </div>
                    <div style="color:#8d8d8d;margin-top:0.4rem;">
                        All cases flagged for review or discrepancy have been resolved by reviewers.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for case in pending:
            title = (
                f'{status_icon(case["status"])} '
                f'{case["case_id"]} — '
                f'{case["applicant"]} — '
                f'{case["document_type"]}'
            )

            with st.expander(title, expanded=False):
                a, b = st.columns(2)

                with a:
                    st.metric(
                        "AI Automated Status",
                        case["status"],
                    )

                with b:
                    st.metric(
                        "AI Confidence Score",
                        f'{case["confidence"]}%',
                    )

                flagged_rows = []

                for field_result in case["result"].get("fields", []):
                    if field_result["status"] != "MATCH":
                        flagged_rows.append(
                            {
                                "Field": (
                                    field_result["field"]
                                    .replace("_", " ")
                                    .title()
                                ),
                                "Application": field_result["application"],
                                "Document": field_result["document"],
                                "Result": (
                                    f'{status_icon(field_result["status"])} '
                                    f'{field_result["status"]}'
                                ),
                                "Reason": field_result["reason"],
                            }
                        )

                st.markdown("#### Fields Requiring Attention")

                if flagged_rows:
                    st.dataframe(
                        pd.DataFrame(flagged_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "No single field is in mismatch, but the case was "
                        "routed for human evaluation based on overall uncertainty."
                    )

                review_note = st.text_area(
                    "Reviewer Notes & Decision Rationale",
                    key=f"note_{case['case_id']}",
                    placeholder="Enter decision rationale or audit comments...",
                )

                st.markdown("#### Reviewer Decision")

                col1, col2 = st.columns(2)

                # APPROVE ACTION
                if col1.button(
                    "✓ APPROVE CASE",
                    key=f"approve_{case['case_id']}",
                    use_container_width=True,
                ):
                    case["status"] = "APPROVED"
                    case["result"]["status"] = "APPROVED"

                    human_info = {
                        "action": "APPROVED",
                        "note": review_note if review_note.strip() else "Manually approved by reviewer.",
                        "reviewed_at": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                    case["human_review"] = human_info
                    case["result"]["human_review"] = human_info

                    try:
                        save_human_review(
                            case_id=case["case_id"],
                            action="APPROVED",
                            reviewer_note=human_info["note"],
                        )
                    except Exception as error:
                        print(f"Database review warning: {error}")

                    st.session_state.review_notification = {
                        "type": "success",
                        "message": f"✓ Case {case['case_id']} ({case['applicant']}) has been APPROVED successfully."
                    }
                    st.rerun()

                # REJECT ACTION
                if col2.button(
                    "✕ REJECT CASE",
                    key=f"reject_{case['case_id']}",
                    use_container_width=True,
                ):
                    case["status"] = "REJECTED"
                    case["result"]["status"] = "REJECTED"

                    human_info = {
                        "action": "REJECTED",
                        "note": review_note if review_note.strip() else "Rejected by reviewer due to discrepancies.",
                        "reviewed_at": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                    case["human_review"] = human_info
                    case["result"]["human_review"] = human_info

                    try:
                        save_human_review(
                            case_id=case["case_id"],
                            action="REJECTED",
                            reviewer_note=human_info["note"],
                        )
                    except Exception as error:
                        print(f"Database review warning: {error}")

                    st.session_state.review_notification = {
                        "type": "warning",
                        "message": f"✕ Case {case['case_id']} ({case['applicant']}) has been REJECTED."
                    }
                    st.rerun()

    with tab_history:
        if not resolved:
            st.markdown(
                """
                <div class="panel">
                    <div style="color:#ffffff;font-weight:700;font-size:1.05rem;">
                        No Review History
                    </div>
                    <div style="color:#8d8d8d;margin-top:0.4rem;">
                        Cases you approve or reject will appear here with full audit trails.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for case in resolved:
                rev = case.get("human_review", {})
                action = rev.get("action", case["status"])
                reviewed_at = rev.get("reviewed_at", case.get("created", ""))
                note = rev.get("note", "No reviewer note provided.")

                with st.expander(
                    f"{status_icon(action)} {case['case_id']} — {case['applicant']} — {action}",
                    expanded=False,
                ):
                    h1, h2, h3 = st.columns(3)
                    with h1:
                        st.metric("Decision", action)
                    with h2:
                        st.metric("Confidence", f"{case['confidence']}%")
                    with h3:
                        st.metric("Reviewed At", reviewed_at)

                    st.markdown(f"**Reviewer Note:** {note}")

                    field_rows = [
                        {
                            "Field": f["field"].replace("_", " ").title(),
                            "Application": f["application"],
                            "Document": f["document"],
                            "Result": f'{status_icon(f["status"])} {f["status"]}',
                            "Reason": f["reason"],
                        }
                        for f in case["result"].get("fields", [])
                    ]
                    if field_rows:
                        st.dataframe(
                            pd.DataFrame(field_rows),
                            use_container_width=True,
                            hide_index=True,
                        )
