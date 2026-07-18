"""Credit card number detector with Luhn validation and brand identification.

Supports Visa, MasterCard, Amex, and Discover card patterns.
Uses the Luhn algorithm for checksum validation.
"""

import re

from pii_redactor.detectors.detection import Detection

# ---------------------------------------------------------------------------
# Card patterns (13-19 digits, optionally separated by spaces or dashes)
# ---------------------------------------------------------------------------

BRAND_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Visa", re.compile(r"\b4[0-9]{12}(?:[0-9]{3}){0,2}\b")),
    ("MasterCard", re.compile(r"\b5[1-5][0-9]{14}\b")),
    ("Amex", re.compile(r"\b3[47][0-9]{13}\b")),
    ("Discover", re.compile(r"\b6(?:011|5[0-9]{2})[0-9]{12}\b")),
]

# Generic pattern with optional separators (used as catch-all)
GENERIC_PATTERN = re.compile(r"\b(?:[0-9]{4}[-\s]?){3}[0-9]{4}\b")

# Card brand prefix map
_CARD_BRANDS: dict[str, str] = {
    "4": "Visa",
    "51": "MasterCard", "52": "MasterCard", "53": "MasterCard",
    "54": "MasterCard", "55": "MasterCard",
    "34": "Amex", "37": "Amex",
    "6011": "Discover", "65": "Discover",
}


# ---------------------------------------------------------------------------
# Luhn algorithm
# ---------------------------------------------------------------------------

def _luhn_check(card_number: str) -> bool:
    """Validate a card number using the Luhn algorithm.

    Returns False for:
    - Numbers shorter than 13 or longer than 19 digits
    - All-zero card numbers (not a valid card)
    """
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    # Reject all-zero card numbers
    if all(d == 0 for d in digits):
        return False

    digits.reverse()
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# ---------------------------------------------------------------------------
# Brand detection
# ---------------------------------------------------------------------------

def detect_card_brand(card_number: str) -> str | None:
    """Detect card brand from the numeric prefix.

    Returns brand name (e.g., "Visa", "MasterCard") or None.
    """
    digits = re.sub(r"[-\s]", "", card_number)
    for prefix, brand in sorted(_CARD_BRANDS.items(), key=lambda x: -len(x[0])):
        if digits.startswith(prefix):
            return brand
    return None


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

def detect_credit_cards_in_text(text: str) -> list[Detection]:
    """Detect credit card numbers in a text string.

    Validates using the Luhn algorithm to reduce false positives.
    """
    detections: list[Detection] = []
    seen_spans: set[tuple[int, int]] = set()

    # Try brand-specific patterns first
    for _brand, pattern in BRAND_PATTERNS:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if span in seen_spans:
                continue
            if _luhn_check(match.group()):
                seen_spans.add(span)
                detections.append(
                    Detection(
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        pii_type="credit_card",
                        confidence=0.95,
                    )
                )

    # Catch-all with separators
    for match in GENERIC_PATTERN.finditer(text):
        span = (match.start(), match.end())
        if span in seen_spans:
            continue
        if _luhn_check(match.group()):
            seen_spans.add(span)
            detections.append(
                Detection(
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    pii_type="credit_card",
                    confidence=0.95,
                )
            )

    return sorted(detections, key=lambda d: d.start)
