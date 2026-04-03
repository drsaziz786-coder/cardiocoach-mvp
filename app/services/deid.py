"""
CardioCoach — PDF De-identification Module
app/services/deid.py

Reads a North Bristol NHS Trust discharge letter PDF, extracts text
page by page, strips patient identifiers, and returns clean text
ready for the CardioCoach extraction pipeline.

Identifier locations in the NBT four-page template:
  1. Header block (page 1) — name, DOB, NHS number, address. In fully
     redacted letters these are blacked out; this function defends against
     partially redacted or unredacted copies.
  2. Footer line (final page) — full name, NHS number (XXX XXX XXXX),
     hospital number, home address. Stripped by NHS-number line detection.
  3. Free-text narrative — Mr/Mrs/Ms [Surname] references. Replaced with
     "the patient".

After scrubbing, a verification scan checks for residual NHS numbers,
UK postcodes, and labelled DOB patterns. Processing halts and raises
DeidentificationError if any are detected — no patient data is logged.

Version: 1.0-pre-lock | March 2026
"""

import logging
import re
from datetime import datetime
from io import BytesIO
from typing import List

import pdfplumber

logger = logging.getLogger(__name__)


# ── PHI detection patterns ────────────────────────────────────────────────────

# NHS number: three groups of digits separated by spaces — 3 3 4
_NHS_RE = re.compile(r"\b\d{3}\s\d{3}\s\d{4}\b")

# UK postcode: standard format, with or without space
_POSTCODE_RE = re.compile(r"\b[A-Z]{1,2}\d[A-Z0-9]?\s*\d[A-Z]{2}\b")

# DOB — only matches when labelled (avoids false positives on clinical dates)
_DOB_LABEL_RE = re.compile(
    r"\b(?:DOB|D\.O\.B|Date\s+of\s+Birth)\b.{0,30}\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}",
    re.IGNORECASE,
)

# Header block labelled fields — replace entire line including any leading
# whitespace pdfplumber inserts for layout positioning.
# No capture groups: replacement strings are hardcoded to avoid backreference
# failures when the group doesn't match.
_NAME_LINE_RE = re.compile(
    r"(?im)^[^\S\r\n]*Name\s*:[^\S\r\n]*.+$"
)
_HOSPITAL_NO_RE = re.compile(
    r"(?im)^[^\S\r\n]*Hospital\s*(?:No|Number|Num)?\s*:[^\S\r\n]*.+$"
)
_ADDRESS_LINE_RE = re.compile(
    r"(?im)^[^\S\r\n]*Address\s*:[^\S\r\n]*.+$"
)

# Street address pattern in running text (number + street word + optional city)
_STREET_RE = re.compile(
    r"\b\d{1,4}\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4}"
    r"(?:,\s*[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})*\b"
)

# Salutation + surname in free-text narrative
_SALUTATION_RE = re.compile(r"\b(Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z][a-zA-Z\-']+\b")


# ── Public exception ──────────────────────────────────────────────────────────

class DeidentificationError(Exception):
    """
    Raised when residual PHI is detected in the de-identified output.
    The exception message describes the type of match only — it never
    contains the matched content.
    """


# ── Main function ─────────────────────────────────────────────────────────────

def deidentify_pdf(pdf_bytes: bytes) -> str:
    """
    De-identify a North Bristol discharge letter PDF.

    Parameters
    ----------
    pdf_bytes : bytes
        Raw bytes of the uploaded PDF file.

    Returns
    -------
    str
        De-identified plain text, safe to pass to the CardioCoach
        extraction pipeline.

    Raises
    ------
    ValueError
        If the PDF contains no extractable text (scanned / image-only).
    DeidentificationError
        If residual PHI patterns are detected after scrubbing.
    """
    # ── Step 1: Extract text page by page ────────────────────────────────────
    pages_text: List[str] = _extract_pages(pdf_bytes)

    if not any(p.strip() for p in pages_text):
        raise ValueError(
            "No readable text found in PDF. "
            "The file may be scanned or image-only — text extraction is not possible."
        )

    # ── Step 2: Strip footer identifier line from last page ───────────────────
    # The NBT template footer line contains the NHS number in XXX XXX XXXX
    # format. Strip any line from the last page that contains this pattern.
    pages_text[-1] = _strip_nhs_footer_lines(pages_text[-1])

    # ── Step 3: Join pages ────────────────────────────────────────────────────
    full_text = "\n\n".join(pages_text)

    # ── Step 4: Scrub salutations in free-text narrative ─────────────────────
    full_text = _SALUTATION_RE.sub("the patient", full_text)

    # ── Step 5: Belt-and-braces scrub of any remaining structured PHI ─────────
    # Labelled header fields — replace entire line with clean placeholder
    full_text = _NAME_LINE_RE.sub("Name: <<PATIENT_NAME>>", full_text)
    full_text = _HOSPITAL_NO_RE.sub("Hospital No: <<HOSPITAL_NUMBER>>", full_text)
    full_text = _ADDRESS_LINE_RE.sub("Address: <<ADDRESS>>", full_text)
    # NHS numbers, DOB labels, postcodes
    full_text = _NHS_RE.sub("<<NHS_NUMBER>>", full_text)
    full_text = _DOB_LABEL_RE.sub("<<DATE_OF_BIRTH>>", full_text)
    full_text = _POSTCODE_RE.sub("<<POSTCODE>>", full_text)

    # ── Step 6: Audit log — no patient data written ───────────────────────────
    logger.info(
        "deid | ts=%s | pages=%d | chars_before=%d | chars_after=%d",
        datetime.utcnow().isoformat(timespec="seconds"),
        len(pages_text),
        sum(len(p) for p in pages_text),
        len(full_text),
    )

    # ── Step 7: Verification scan ─────────────────────────────────────────────
    _verify_clean(full_text)

    return full_text.strip()


# ── Private helpers ───────────────────────────────────────────────────────────

def _extract_pages(pdf_bytes: bytes) -> List[str]:
    """Open PDF with pdfplumber and return one string per page."""
    pages: List[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages


def _strip_nhs_footer_lines(page_text: str) -> str:
    """
    Remove any line from the last-page text that contains an NHS number
    in XXX XXX XXXX format. These lines are the patient identity footer
    of the NBT discharge template.
    """
    lines = page_text.splitlines()
    cleaned = [line for line in lines if not _NHS_RE.search(line)]
    return "\n".join(cleaned)


def _verify_clean(text: str) -> None:
    """
    Scan de-identified output for residual PHI patterns.
    Raises DeidentificationError describing the type of match only —
    the matched text is never included in the exception or logs.
    """
    checks = [
        (_NHS_RE,         "NHS number pattern (XXX XXX XXXX)"),
        (_POSTCODE_RE,    "UK postcode pattern"),
        (_DOB_LABEL_RE,   "labelled date-of-birth pattern"),
        # Name: / Hospital No: / Address: lines whose value was not replaced
        (re.compile(r"(?im)^[^\S\r\n]*Name\s*:[^\S\r\n]*(?!<<PATIENT_NAME>>).+$"),
         "unlabelled Name: line"),
        (re.compile(r"(?im)^[^\S\r\n]*Hospital\s*(?:No|Number|Num)?\s*:[^\S\r\n]*(?!<<HOSPITAL_NUMBER>>).+$"),
         "unlabelled Hospital No: line"),
        (re.compile(r"(?im)^[^\S\r\n]*Address\s*:[^\S\r\n]*(?!<<ADDRESS>>).+$"),
         "unlabelled Address: line"),
    ]
    for pattern, label in checks:
        if pattern.search(text):
            raise DeidentificationError(
                f"Verification failed: {label} detected in de-identified output. "
                "Manual review required before processing."
            )
