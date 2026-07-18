"""Date detector with contextual DOB filtering.

Detects dates in common formats using datetime.strptime for validation.
Dates near DOB-context keywords get higher confidence and pii_type="dob".
"""

import re
from datetime import datetime

from pii_redactor.detectors.detection import Detection

# ---------------------------------------------------------------------------
# Date patterns (order matters — most specific first)
# ---------------------------------------------------------------------------

# Full month names
MONTHS_FULL = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)

# Abbreviated month names
MONTHS_ABBR = (
    "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)

# DD Month YYYY  (e.g., "15 January 1990")
DAY_MONTH_YEAR = re.compile(
    rf"\b\d{{1,2}}\s+(?:{MONTHS_FULL})\s+\d{{4}}\b",
    re.IGNORECASE,
)

# Month DD, YYYY  (e.g., "January 15, 1990")
MONTH_DAY_YEAR = re.compile(
    rf"\b(?:{MONTHS_FULL})\s+\d{{1,2}},?\s+\d{{4}}\b",
    re.IGNORECASE,
)

# DD Mon YYYY  (e.g., "15 Jan 1990")
DAY_MON_YEAR = re.compile(
    rf"\b\d{{1,2}}\s+(?:{MONTHS_ABBR})\s+\d{{4}}\b",
    re.IGNORECASE,
)

# Mon DD, YYYY  (e.g., "Jan 15, 1990")
MON_DAY_YEAR = re.compile(
    rf"\b(?:{MONTHS_ABBR})\s+\d{{1,2}},?\s+\d{{4}}\b",
    re.IGNORECASE,
)

# DD-Month-YYYY  (e.g., "15-january-1990")
DAY_MONTH_YEAR_DASH = re.compile(
    rf"\b\d{{1,2}}-(?:{MONTHS_FULL})-\d{{4}}\b",
    re.IGNORECASE,
)

# YYYY-MM-DD  (ISO) — use lookbehind/lookahead instead of \b around digits
ISO_DATE = re.compile(r"(?<!\d)\d{4}-\d{1,2}-\d{1,2}(?!\d)")

# MM/DD/YYYY or DD/MM/YYYY or MM-DD-YYYY
SLASH_DATE = re.compile(r"(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{4}(?!\d)")

# MM-DD-YYYY with dash separators
DASH_DATE = re.compile(r"(?<!\d)\d{1,2}-\d{1,2}-\d{4}(?!\d)")

DATE_PATTERNS = [
    DAY_MONTH_YEAR, MONTH_DAY_YEAR,
    DAY_MON_YEAR, MON_DAY_YEAR,
    DAY_MONTH_YEAR_DASH,
    ISO_DATE, SLASH_DATE, DASH_DATE,
]

# ---------------------------------------------------------------------------
# Date formats for strptime validation
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    "%d %B %Y",
    "%B %d, %Y",
    "%B %d %Y",
    "%d %b %Y",
    "%b %d, %Y",
    "%b %d %Y",
    "%d-%B-%Y",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%d-%m-%Y",
]

# ---------------------------------------------------------------------------
# DOB context keywords
# ---------------------------------------------------------------------------

DOB_CONTEXT_KEYWORDS = {
    "date of birth", "dob", "born", "birth date", "birthdate",
    "date of birth:", "dob:", "born on", "born:",
}


def _validate_date(date_str: str) -> bool:
    """Validate a date string using datetime.strptime.

    Accepts dates between 1900 and 2099.
    """
    cleaned = date_str.replace(",", "").strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if 1900 <= dt.year <= 2099:
                return True
        except ValueError:
            continue
    return False


def _has_dob_context(text: str, start: int, end: int) -> bool:
    """Check if a date appears near DOB-context keywords (50-char window)."""
    window_before = text[max(0, start - 50) : start].lower()
    window_after = text[end : min(len(text), end + 50)].lower()
    return any(kw in window_before or kw in window_after for kw in DOB_CONTEXT_KEYWORDS)


def detect_dates_in_text(text: str) -> list[Detection]:
    """Detect dates in a text string.

    Returns dates with confidence and pii_type based on context:
    - pii_type="dob", confidence=0.90 when near DOB keywords
    - pii_type="date", confidence=0.70 for generic dates
    """
    detections: list[Detection] = []

    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            if not _validate_date(match.group()):
                continue

            confidence = 0.70
            pii_type = "date"

            if _has_dob_context(text, match.start(), match.end()):
                confidence = 0.90
                pii_type = "dob"

            detections.append(
                Detection(
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    pii_type=pii_type,
                    confidence=confidence,
                )
            )

    # Deduplicate overlapping detections — longest first, then earliest start
    detections.sort(key=lambda d: (d.start, -(d.end - d.start)))
    deduplicated: list[Detection] = []
    last_end = -1
    for d in detections:
        if d.start >= last_end:
            deduplicated.append(d)
            last_end = d.end

    return deduplicated
