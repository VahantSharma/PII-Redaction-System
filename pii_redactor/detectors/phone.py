"""Indian phone number detector."""

import re

from pii_redactor.detectors.detection import Detection

PHONE_PATTERNS = [
    re.compile(r"\+91[-\s]?\d{10}"),
    re.compile(r"\+91[-\s]+\d{2,4}[-\s]*\d{4}[-\s]*\d{4}"),
    re.compile(r"\+91[-\s]+\d{5}[-\s]*\d{5}"),
    re.compile(r"\+91[-\s]+\d{3}[-\s]+\d{3}[-\s]+\d{4}"),
    re.compile(r"0\d{2,3}[-\s]+\d{3,4}[-\s]+\d{4}"),
    re.compile(r"0\d{2,3}[-\s]?\d{6,8}"),
    re.compile(r"\b\d{5}\s\d{5}\b"),
]


def detect_phones_in_text(text: str) -> list[Detection]:
    """Detect Indian phone numbers in a text string."""
    detections: list[Detection] = []
    seen_spans: set[tuple[int, int]] = set()

    for pattern in PHONE_PATTERNS:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if span in seen_spans:
                continue

            matched_text = match.group().strip()
            digits_only = re.sub(r"\D", "", matched_text)

            # Reject SEBI/CIN registration numbers (8-9 digits starting with 0000)
            if len(digits_only) in (8, 9) and digits_only.startswith("0000"):
                continue

            seen_spans.add(span)
            detections.append(
                Detection(
                    text=matched_text,
                    start=match.start(),
                    end=match.end(),
                    pii_type="phone",
                    confidence=0.90,
                )
            )

    return sorted(detections, key=lambda d: d.start)
