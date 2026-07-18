"""Company / organization name detector using spaCy NER + suffix heuristics + context."""

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

# Layer 2: Suffix heuristics
COMPANY_SUFFIXES = {
    "ltd", "limited", "llp", "inc", "corporation", "corp",
    "company", "co", "bank", "trust", "foundation", "association",
    "society", "pvt", "private",
}

# Layer 3: Context promotion keywords
ORG_CONTEXT_KEYWORDS = {
    "registrar", "auditor", "legal", "counsel", "banker",
    "lead", "manager", "issuer", "exchange", "depository",
    "merchant", "broker", "underwriter", "advisor",
    "book", "running", "sub-broker",
}

# Layer 4: False-positive filters
ORG_FALSE_POSITIVES = {
    "board", "committee", "promoter", "director",
    "company act", "companies act", "sebi", "rbi",
    "section", "clause", "regulation", "notification",
    "the company", "our company", "my company",
    "company", "companies",
    "registered office", "corporate office", "business centre",
    "business center", "head office", "branch office",
}

GEOGRAPHIC_WORDS = {
    "village", "taluka", "district", "tehsil", "subdivision",
    "ward", "block", "mandal", "post", "pincode",
}

# Regex fallback for suffix patterns not caught by spaCy
SUFFIX_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z&.-]{1,30}(?:\s+[A-Za-z&.-]{1,30}){0,2})\s+"
    r"(?:Pvt\.?\s*Ltd\.?|Limited|LLP|Inc\.?|Corporation|Corp\.?|"
    r"Bank|Trust|Foundation|Association|Society)\b"
)

STRIP_WORDS = {"company", "the", "our", "my", "a", "of", "and", "for"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_company_suffix(text: str) -> bool:
    """Check if text contains a company suffix."""
    words = set(text.lower().replace(".", "").replace(",", "").split())
    return bool(words & COMPANY_SUFFIXES)


def _has_org_context(text: str, start: int, end: int) -> bool:
    """Check if a context promotion keyword appears near the detection."""
    window_before = text[max(0, start - 50) : start].lower()
    window_after = text[end : min(len(text), end + 50)].lower()
    return any(kw in window_before or kw in window_after for kw in ORG_CONTEXT_KEYWORDS)


def _is_org_false_positive(text: str) -> bool:
    """Check if text is a common false positive for organization detection."""
    lower = text.lower().strip()
    if lower in ORG_FALSE_POSITIVES:
        return True
    words = set(lower.replace(",", "").replace(".", "").split())
    if words & ORG_FALSE_POSITIVES:
        return True
    if words & GEOGRAPHIC_WORDS:
        return True
    address_substrings = {
        "registered office", "corporate office", "business centre",
        "business center", "head office", "branch office",
        "tower", "building", "floor", "suite",
    }
    if any(sub in lower for sub in address_substrings):
        return True
    return False


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

def detect_companies_in_text(text: str) -> list[Detection]:
    """Detect company/organization names using layered approach.

    Layer 1: spaCy ORG entities (primary signal)
    Layer 2: Suffix heuristics (words ending with Ltd, Bank, etc.)
    Layer 3: Context promotion (near Registrar, Auditor, etc.)
    Layer 4: False-positive filtering
    """
    nlp = get_nlp()
    doc = nlp(text)

    detections: list[Detection] = []

    for ent in doc.ents:
        if ent.label_ != "ORG":
            continue

        if "\n" in ent.text:
            continue

        if _is_org_false_positive(ent.text):
            continue

        if _has_company_suffix(ent.text):
            detections.append(
                Detection(
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    pii_type="company",
                    confidence=0.90,
                )
            )
            continue

        if _has_org_context(text, ent.start_char, ent.end_char):
            detections.append(
                Detection(
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    pii_type="company",
                    confidence=0.75,
                )
            )
            continue

        if len(ent.text.split()) >= 2:
            detections.append(
                Detection(
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    pii_type="company",
                    confidence=0.70,
                )
            )

    # Layer 2: Regex fallback for suffix patterns not caught by spaCy
    for match in SUFFIX_PATTERN.finditer(text):
        raw_name = match.group(0).strip()
        name_start = match.start()
        name_end = match.end()

        if any(name_start < d.end and name_end > d.start for d in detections):
            continue

        raw_lower = raw_name.lower()
        if any(w in raw_lower for w in ["office", "tower", "building", "floor", "suite"]):
            continue

        words = raw_name.split()
        stripped = 0
        while words and words[0].lower().rstrip(",.") in STRIP_WORDS:
            stripped += len(words[0]) + 1
            words = words[1:]
        name_start += stripped
        name = " ".join(words)
        if not name:
            continue

        if _is_org_false_positive(name):
            continue

        detections.append(
            Detection(
                text=name,
                start=name_start,
                end=name_end,
                pii_type="company",
                confidence=0.85,
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

    return deduplicated
