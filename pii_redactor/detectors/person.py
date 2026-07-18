"""Person name detector using spaCy NER + heuristics."""

import re

import spacy

from pii_redactor.detectors.detection import Detection

# ---------------------------------------------------------------------------
# Lazy-load spaCy model
# ---------------------------------------------------------------------------

_nlp = None


def get_nlp():
    """Lazy-load spaCy model."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ---------------------------------------------------------------------------
# Heuristic constants
# ---------------------------------------------------------------------------

PERSON_TITLES = {"mr", "mrs", "ms", "shri", "smt", "dr", "prof"}

ROLE_KEYWORDS = {
    "director", "manager", "officer", "secretary", "compliance",
    "executive", "chairman", "promoter", "founder", "ceo", "cfo",
}

PERSON_FALSE_POSITIVES = {
    "pre-offer", "post-offer", "promoters", "promoter",
    "shareholders", "shareholder", "company", "board",
    "committee", "meeting", "resolution", "section",
}

LABEL_WORDS = {
    "email", "phone", "gstin", "pan", "cfo", "ceo",
    "report", "medical", "invoice", "date", "address",
    "salary", "phone", "age", "dob", "name", "title",
}

ORG_INDICATORS = {
    "group", "trust", "limited", "ltd", "company", "foundation",
    "association", "society", "corporation", "inc", "llc", "bank",
}

PLACE_CONTEXTS = {
    "village", "taluka", "district", "post", "pincode",
    "tehsil", "subdivision", "ward", "block", "mandal",
}


# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------

def _has_title_context(text: str, start: int) -> bool:
    """Check if a title prefix (Mr., Shri, etc.) appears before the detection."""
    word_before = text[max(0, start - 15) : start].lower()
    return any(title in word_before for title in PERSON_TITLES)


def _has_role_context(text: str, start: int, end: int) -> bool:
    """Check if a role keyword appears near the detection."""
    window_before = text[max(0, start - 40) : start].lower()
    window_after = text[end : min(len(text), end + 40)].lower()
    return any(kw in window_before or kw in window_after for kw in ROLE_KEYWORDS)


def _has_place_context(text: str, start: int, end: int) -> bool:
    """Check if a geographic keyword appears near a single-word detection."""
    window_before = text[max(0, start - 30) : start].lower()
    window_after = text[end : min(len(text), end + 30)].lower()

    if any(kw in window_before or kw in window_after for kw in PLACE_CONTEXTS):
        return True

    # Word followed by comma (common in addresses)
    if text[end : end + 2] == ", ":
        return True

    # Preceded by comma
    if window_before.rstrip().endswith(","):
        return True

    return False


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

# Regex fallback pattern
TITLE_NAME_PATTERN = re.compile(
    r"(?:contact\s+person|director|officer|manager|secretary|name|partner\s*\d*)[:\s]+"
    r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    re.IGNORECASE,
)


def detect_persons_in_text(text: str) -> list[Detection]:
    """Detect person names using spaCy NER + heuristic promotion.

    Detection strategy (candidate promotion):
        spaCy PERSON  -> accept
        spaCy ORG     -> context rules -> accept/reject
        Title prefix  -> additional candidates
    """
    nlp = get_nlp()
    doc = nlp(text)

    detections: list[Detection] = []

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            if ent.text.lower() in PERSON_FALSE_POSITIVES:
                continue
            if "\n" in ent.text:
                continue
            if len(ent.text.split()) == 1 and ent.text.lower() in LABEL_WORDS:
                continue
            if len(ent.text.split()) == 1 and _has_place_context(
                text, ent.start_char, ent.end_char
            ):
                continue
            if " - " in ent.text:
                continue

            conf = 0.85 if _has_title_context(text, ent.start_char) else 0.70
            detections.append(
                Detection(
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    pii_type="person",
                    confidence=conf,
                )
            )

        elif ent.label_ == "ORG":
            ent_words = set(ent.text.lower().split())
            if ent_words & ORG_INDICATORS:
                continue

            if "\n" in ent.text:
                continue

            has_title = _has_title_context(text, ent.start_char)
            has_role = _has_role_context(text, ent.start_char, ent.end_char)

            if has_title or has_role:
                if len(ent.text.split()) == 1 and _has_place_context(
                    text, ent.start_char, ent.end_char
                ):
                    continue
                if " - " in ent.text:
                    continue

                detections.append(
                    Detection(
                        text=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        pii_type="person",
                        confidence=0.65 if has_role else 0.75,
                    )
                )

    # Deduplicate: keep longest detection for overlapping regions
    detections.sort(key=lambda d: (d.start, -(d.end - d.start)))
    deduplicated: list[Detection] = []
    last_end = -1
    for d in detections:
        if d.start >= last_end:
            deduplicated.append(d)
            last_end = d.end

    # Regex fallback: detect "Contact Person: Firstname Lastname" patterns
    for match in TITLE_NAME_PATTERN.finditer(text):
        name = match.group(1)
        name_start = match.start(1)
        name_end = match.end(1)
        if any(name_start >= d.start and name_end <= d.end for d in deduplicated):
            continue
        deduplicated.append(
            Detection(
                text=name,
                start=name_start,
                end=name_end,
                pii_type="person",
                confidence=0.80,
            )
        )

    return deduplicated
