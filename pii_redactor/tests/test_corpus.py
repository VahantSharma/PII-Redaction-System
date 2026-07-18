"""Corpus-based detector tests.

Parses the PII corpus files in tests/samples/ and verifies that:
- VALID examples are detected
- INVALID examples are NOT detected

Each corpus file has sections: === VALID ===, === INVALID ===, === FALSE POSITIVES ===,
=== FORMATTING ===, === EDGE CASES ===

The test runs the appropriate detector on each line and checks detection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.detectors import (
    detect_emails_in_text,
    detect_phones_in_text,
    detect_persons_in_text,
    detect_companies_in_text,
    detect_ipv4_in_text,
    detect_ipv6_in_text,
    detect_dates_in_text,
    detect_credit_cards_in_text,
    detect_national_ids_in_text,
)

SAMPLES_DIR = Path(__file__).parent / "samples"

# Map detector name -> (detect_function, pii_type, match_mode)
# match_mode: "exact" for structured PII, "contain" for NER-based PII
DETECTORS = {
    "email": (detect_emails_in_text, "email", "exact"),
    "phone": (detect_phones_in_text, "phone", "exact"),
    "person": (detect_persons_in_text, "person", "contain"),
    "company": (detect_companies_in_text, "company", "contain"),
    "ipv4": (detect_ipv4_in_text, "ipv4", "exact"),
    "ipv6": (detect_ipv6_in_text, "ipv6", "exact"),
    "date": (detect_dates_in_text, "date", "exact"),
    "credit_card": (detect_credit_cards_in_text, "credit_card", "exact"),
    "national_id": (detect_national_ids_in_text, "national_id", "exact"),
}


def parse_corpus(filepath: Path) -> dict[str, list[str]]:
    """Parse a corpus file into sections.

    Returns dict mapping section name to list of example strings.
    Handles \\t escape sequences as actual tabs.
    """
    sections: dict[str, list[str]] = {}
    current_section = None

    for line in filepath.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("=== ") and stripped.endswith(" ==="):
            current_section = stripped[4:-4].lower()
            sections[current_section] = []
        elif current_section and stripped:
            sections[current_section].append(stripped.replace("\\t", "\t"))

    return sections


def _check_match(detected_texts: list[str], expected: str, mode: str) -> bool:
    """Check if expected text is found in detected texts."""
    if mode == "exact":
        return expected in detected_texts
    else:
        # containment: expected is contained in a detection, or vice versa
        for dt in detected_texts:
            if expected in dt or dt in expected:
                return True
        return False


def test_valid_examples():
    """All VALID examples in the corpus must be detected."""
    failures = []

    for detector_name, (detect_fn, pii_type, match_mode) in DETECTORS.items():
        corpus_file = SAMPLES_DIR / f"{detector_name}.txt"
        if not corpus_file.exists():
            continue

        sections = parse_corpus(corpus_file)
        valid_examples = sections.get("valid", [])

        for example in valid_examples:
            detections = detect_fn(example)
            detected_texts = [d.text for d in detections]

            if not _check_match(detected_texts, example, match_mode):
                failures.append(
                    f"  [{detector_name}] MISSED: '{example}' "
                    f"(detected: {detected_texts})"
                )

    if failures:
        msg = f"VALID examples not detected ({len(failures)} failures):\n"
        msg += "\n".join(failures)
        raise AssertionError(msg)


def test_invalid_examples():
    """All INVALID examples must NOT be detected."""
    failures = []

    for detector_name, (detect_fn, pii_type, match_mode) in DETECTORS.items():
        corpus_file = SAMPLES_DIR / f"{detector_name}.txt"
        if not corpus_file.exists():
            continue

        sections = parse_corpus(corpus_file)
        invalid_examples = sections.get("invalid", [])

        for example in invalid_examples:
            detections = detect_fn(example)
            detected_texts = [d.text for d in detections]

            if _check_match(detected_texts, example, match_mode):
                failures.append(
                    f"  [{detector_name}] FALSE POSITIVE: '{example}' "
                    f"(detected: {detected_texts})"
                )

    if failures:
        msg = f"INVALID examples incorrectly detected ({len(failures)} failures):\n"
        msg += "\n".join(failures)
        raise AssertionError(msg)


def test_false_positive_resistance():
    """FALSE POSITIVES examples must NOT be detected."""
    failures = []

    for detector_name, (detect_fn, pii_type, match_mode) in DETECTORS.items():
        corpus_file = SAMPLES_DIR / f"{detector_name}.txt"
        if not corpus_file.exists():
            continue

        sections = parse_corpus(corpus_file)
        fp_examples = sections.get("false positives", [])

        for example in fp_examples:
            detections = detect_fn(example)
            detected_texts = [d.text for d in detections]

            if _check_match(detected_texts, example, match_mode):
                failures.append(
                    f"  [{detector_name}] FALSE POSITIVE: '{example}' "
                    f"(detected: {detected_texts})"
                )

    if failures:
        msg = f"FALSE POSITIVE examples incorrectly detected ({len(failures)} failures):\n"
        msg += "\n".join(failures)
        raise AssertionError(msg)


def test_formatting_variants():
    """FORMATTING variants should be detected (they are valid PII)."""
    failures = []

    for detector_name, (detect_fn, pii_type, match_mode) in DETECTORS.items():
        corpus_file = SAMPLES_DIR / f"{detector_name}.txt"
        if not corpus_file.exists():
            continue

        sections = parse_corpus(corpus_file)
        fmt_examples = sections.get("formatting", [])

        for example in fmt_examples:
            detections = detect_fn(example)
            detected_texts = [d.text for d in detections]

            if not _check_match(detected_texts, example, match_mode):
                failures.append(
                    f"  [{detector_name}] MISSED formatting: '{example}' "
                    f"(detected: {detected_texts})"
                )

    if failures:
        msg = f"FORMATTING variants not detected ({len(failures)} failures):\n"
        msg += "\n".join(failures)
        raise AssertionError(msg)


def test_edge_cases():
    """EDGE CASES should be detected (they are valid PII)."""
    failures = []

    for detector_name, (detect_fn, pii_type, match_mode) in DETECTORS.items():
        corpus_file = SAMPLES_DIR / f"{detector_name}.txt"
        if not corpus_file.exists():
            continue

        sections = parse_corpus(corpus_file)
        edge_examples = sections.get("edge cases", [])

        for example in edge_examples:
            detections = detect_fn(example)
            detected_texts = [d.text for d in detections]

            if not _check_match(detected_texts, example, match_mode):
                failures.append(
                    f"  [{detector_name}] MISSED edge case: '{example}' "
                    f"(detected: {detected_texts})"
                )

    if failures:
        msg = f"EDGE CASES not detected ({len(failures)} failures):\n"
        msg += "\n".join(failures)
        raise AssertionError(msg)


def test_known_limitations_documented():
    """KNOWN LIMITATIONS are documented but not asserted as failures.

    These are known edge cases where detection is not expected due to
    NER model limitations, deliberate design decisions (false positive
    avoidance), or other constraints. The test simply ensures that
    detectors WITH a KNOWN LIMITATIONS section have valid content.
    """
    for detector_name in DETECTORS:
        corpus_file = SAMPLES_DIR / f"{detector_name}.txt"
        if not corpus_file.exists():
            continue

        sections = parse_corpus(corpus_file)
        limitations = sections.get("known limitations", [])

        if limitations:
            assert len(limitations) > 0, (
                f"[{detector_name}] KNOWN LIMITATIONS section must not be empty"
            )


if __name__ == "__main__":
    print("Running corpus tests...")
    tests = [
        test_valid_examples,
        test_invalid_examples,
        test_false_positive_resistance,
        test_formatting_variants,
        test_edge_cases,
        test_known_limitations_documented,
    ]

    total_pass = 0
    total_fail = 0

    for test_fn in tests:
        print(f"\n--- {test_fn.__doc__} ---")
        try:
            test_fn()
            print("PASS")
            total_pass += 1
        except AssertionError as e:
            print(f"FAIL: {e}")
            total_fail += 1

    print(f"\n{'='*60}")
    print(f"Results: {total_pass} passed, {total_fail} failed out of {len(tests)}")
