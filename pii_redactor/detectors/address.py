"""Physical address detector using structured entity extraction.

Strategy:
    1. Extract semantic components (house number, building, street, city, etc.)
    2. Validate that components form a valid address structure
    3. Expand to sentence boundaries
    4. Return Detection objects

The detector works on any document type by relying on address structure
rather than document-specific context headers or arbitrary scoring.
"""

import re
from typing import NamedTuple

from pii_redactor.detectors.detection import Detection


# ---------------------------------------------------------------------------
# Address components
# ---------------------------------------------------------------------------


class AddressComponents(NamedTuple):
    """Structured address components."""

    house_number: str | None = None
    building: str | None = None
    street: str | None = None
    locality: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None

    def is_valid(self) -> bool:
        """Check if components form a valid address.

        Valid address criteria:
        - Must contain a postal code (strongest signal for complete address)
        - Must contain at least one location component (street, building, etc.)
        - Must contain at least 3 components total
        """
        present = sum(1 for c in self if c is not None)
        has_postal_code = self.postal_code is not None
        has_location_component = any([
            self.street,
            self.building,
            self.house_number,
            self.locality,
        ])
        return has_postal_code and has_location_component and present >= 3

    def component_count(self) -> int:
        """Return number of present components."""
        return sum(1 for c in self if c is not None)


# ---------------------------------------------------------------------------
# Component extraction patterns
# ---------------------------------------------------------------------------

HOUSE_NUMBER_PATTERN = re.compile(
    r"\b(Flat|Plot|No|Number|Unit|Apt|Apartment|S\.?\s*no\.?)\s*[-–]?\s*\d+[\w\s/-]*",
    re.IGNORECASE,
)

BUILDING_PATTERN = re.compile(
    r"\b\w+\s+(Tower|Building|Floor|Block|Wing|House|Complex|Park|Residency|Apartment|Chambers|Bunglow|Centre|Center)\b",
    re.IGNORECASE,
)

TOWER_NUMBER_PATTERN = re.compile(
    r"\b(Tower|Building|Block|Wing)\s*[-–]?\s*\d+\b",
    re.IGNORECASE,
)

STREET_PATTERN = re.compile(
    r"\b\w+\s+(Road|Street|Lane|Marg|Path|Boulevard|Avenue|Main Road)\b",
    re.IGNORECASE,
)

POSTAL_CODE_PATTERN = re.compile(r"(?<!\d)\d{6}(?!\d)")

CITY_PATTERN = re.compile(
    r"\b(Pune|Mumbai|Delhi|Bangalore|Bengaluru|Chennai|Hyderabad|Kolkata|Ahmednagar|"
    r"Bhopal|Noida|Gurgaon|Gurugram|Jaipur|Lucknow|Kochi|"
    r"London|New York|Springfield|Aurangabad)\b",
    re.IGNORECASE,
)

STATE_PATTERN = re.compile(
    r"\b(Maharashtra|Madhya Pradesh|Gujarat|Karnataka|Tamil Nadu|"
    r"Uttar Pradesh|Haryana|Delhi|California|New York|Texas|"
    r"IL|UP|MP|MH|KA|TN|GJ|RJ|PB|WB|OR|AP|TS|KL|GA|HR|PB|JK|"
    r"Chhattisgarh|Jharkhand|Bihar|Uttarakhand|Himachal Pradesh)\b",
    re.IGNORECASE,
)

COUNTRY_PATTERN = re.compile(
    r"\b(India|USA|UK|United Kingdom|United States|Bharat)\b",
    re.IGNORECASE,
)

VILLAGE_PATTERN = re.compile(r"\bVillage\s+[\w\s]+", re.IGNORECASE)
TALUKA_PATTERN = re.compile(r"\bTaluka\s+[\w\s-]+", re.IGNORECASE)
DISTRICT_PATTERN = re.compile(r"\b(Dist|District)\s*[-–]?\s*\w+", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Component extraction
# ---------------------------------------------------------------------------


def extract_components(text: str) -> AddressComponents:
    """Extract address components from text."""
    house_number = None
    building = None
    street = None
    locality = None
    city = None
    state = None
    postal_code = None
    country = None

    match = HOUSE_NUMBER_PATTERN.search(text)
    if match:
        house_number = match.group()

    match = BUILDING_PATTERN.search(text)
    if match:
        building = match.group()
    else:
        match = TOWER_NUMBER_PATTERN.search(text)
        if match:
            building = match.group()

    match = STREET_PATTERN.search(text)
    if match:
        street = match.group()

    match = POSTAL_CODE_PATTERN.search(text)
    if match:
        postal_code = match.group()

    match = CITY_PATTERN.search(text)
    if match:
        city = match.group()

    match = STATE_PATTERN.search(text)
    if match:
        state = match.group()

    match = COUNTRY_PATTERN.search(text)
    if match:
        country = match.group()

    match = VILLAGE_PATTERN.search(text)
    if match:
        locality = match.group()
    else:
        match = TALUKA_PATTERN.search(text)
        if match:
            locality = match.group()
        else:
            match = DISTRICT_PATTERN.search(text)
            if match:
                locality = match.group()

    return AddressComponents(
        house_number=house_number,
        building=building,
        street=street,
        locality=locality,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
    )


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------


def generate_comma_separated_candidates(text: str) -> list[tuple[int, int]]:
    """Generate candidate spans from comma-separated segments."""
    candidates: list[tuple[int, int]] = []
    pattern = re.compile(r"[^,]+(?:,\s*[^,]+){1,5}")
    for match in pattern.finditer(text):
        candidates.append((match.start(), match.end()))
    return candidates


def generate_newline_separated_candidates(text: str) -> list[tuple[int, int]]:
    """Generate candidate spans from newline-separated lines."""
    candidates: list[tuple[int, int]] = []
    lines = text.split("\n")
    max_lines = 5

    for i, line in enumerate(lines):
        if POSTAL_CODE_PATTERN.search(line):
            start_line = i
            while start_line > 0 and not lines[start_line - 1].endswith(".") and (i - start_line) < max_lines:
                start_line -= 1

            end_line = i
            while end_line < len(lines) - 1 and not lines[end_line].endswith(".") and (end_line - i) < max_lines:
                end_line += 1

            combined = "\n".join(lines[start_line : end_line + 1])
            pos = text.find(combined)
            if pos >= 0:
                candidates.append((pos, pos + len(combined)))

    return candidates


def generate_all_candidates(text: str) -> list[tuple[int, int]]:
    """Generate all candidate spans using multiple strategies."""
    candidates: list[tuple[int, int]] = []
    candidates.extend(generate_comma_separated_candidates(text))
    candidates.extend(generate_newline_separated_candidates(text))

    candidates = list(set(candidates))
    candidates.sort(key=lambda c: (c[0], -(c[1] - c[0])))
    return candidates


# ---------------------------------------------------------------------------
# Expansion
# ---------------------------------------------------------------------------


def expand_to_sentence_boundary(text: str, start: int, end: int) -> tuple[int, int]:
    """Expand span to sentence boundaries, capped at 200 chars each direction."""
    original_start = start
    original_end = end
    max_expand = 200
    while start > 0 and text[start - 1] not in ".!?\n" and (original_start - start) < max_expand:
        start -= 1
    while end < len(text) and text[end] not in ".!?\n" and (end - original_end) < max_expand:
        end += 1
    return start, end


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------


def detect_addresses_in_text(text: str) -> list[Detection]:
    """Detect physical addresses in text using structured entity extraction."""
    detections: list[Detection] = []

    candidates = generate_all_candidates(text)

    for start, end in candidates:
        candidate_text = text[start:end]
        components = extract_components(candidate_text)

        if not components.is_valid():
            continue

        confidence = min(components.component_count() / 5.0, 1.0)
        expanded_start, expanded_end = expand_to_sentence_boundary(text, start, end)

        # Reject expanded detections spanning more than 10 lines
        line_count = text[expanded_start:expanded_end].count("\n")
        if line_count > 10:
            continue

        detections.append(
            Detection(
                text=text[expanded_start:expanded_end],
                start=expanded_start,
                end=expanded_end,
                pii_type="address",
                confidence=confidence,
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
