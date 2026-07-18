"""
PII Redaction Pipeline.

Usage:
    python -m pii_redactor input.docx output.docx

Architecture:
    detector(text) → list[Detection]
    resolve_overlaps(detections) → list[Detection]
    plan_replacements(detections, mapping, registry) → list[ReplacementPlan]
    expand_plan(plan, runs) → list[RunEdit]
    apply_edits(edits, runs)  ← only mutation point
"""

import sys

from pii_redactor.parser import load_document, save_document
from pii_redactor.detectors import (
    detect_emails_in_text,
    detect_phones_in_text,
    detect_persons_in_text,
    detect_companies_in_text,
    detect_addresses_in_text,
    detect_ipv4_in_text,
    detect_ipv6_in_text,
    detect_dates_in_text,
    detect_credit_cards_in_text,
    detect_national_ids_in_text,
)
from pii_redactor.replacer import EntityRegistry
from pii_redactor.replacement import (
    build_run_mapping,
    plan_replacements,
    expand_plan,
    apply_edits,
)


def process_run(run, registry: EntityRegistry) -> list[dict]:
    """Detect and replace regex-based PII in a single run.

    For email/phone detectors that work on individual runs.
    """
    if not run.text.strip():
        return []

    detections = []
    detections.extend(detect_emails_in_text(run.text))
    detections.extend(detect_phones_in_text(run.text))
    detections.extend(detect_ipv4_in_text(run.text))
    detections.extend(detect_ipv6_in_text(run.text))
    detections.extend(detect_dates_in_text(run.text))
    detections.extend(detect_credit_cards_in_text(run.text))
    detections.extend(detect_national_ids_in_text(run.text))

    if not detections:
        return []

    # Build single-run mapping
    mapping = [(0, j) for j in range(len(run.text))]
    runs = [run]

    plans = plan_replacements(detections, mapping, registry, runs)
    if not plans:
        return []

    edits = []
    for plan in plans:
        edits.extend(expand_plan(plan, runs))

    apply_edits(edits, runs)

    return [{"original": p.original_text, "fake": p.replacement_text, "type": p.pii_type}
            for p in plans]


def process_paragraph_for_names(paragraph, registry: EntityRegistry) -> list[dict]:
    """Detect and replace person names in a paragraph.

    Handles run-splitting: concatenates runs, runs NER, maps back.
    """
    runs = paragraph.runs
    if not runs:
        return []

    mapping, concat_text = build_run_mapping(runs)
    if not concat_text.strip():
        return []

    detections = detect_persons_in_text(concat_text)
    if not detections:
        return []

    plans = plan_replacements(detections, mapping, registry, runs)
    if not plans:
        return []

    edits = []
    for plan in plans:
        edits.extend(expand_plan(plan, runs))

    apply_edits(edits, runs)

    return [{"original": p.original_text, "fake": p.replacement_text, "type": p.pii_type}
            for p in plans]


def process_paragraph_for_companies(paragraph, registry: EntityRegistry) -> list[dict]:
    """Detect and replace company/organization names in a paragraph.

    Handles run-splitting: concatenates runs, detects orgs, maps back.
    Uses the same ReplacementPlan -> RunEdit -> apply_edits() pipeline.
    """
    runs = paragraph.runs
    if not runs:
        return []

    mapping, concat_text = build_run_mapping(runs)
    if not concat_text.strip():
        return []

    detections = detect_companies_in_text(concat_text)
    if not detections:
        return []

    plans = plan_replacements(detections, mapping, registry, runs)
    if not plans:
        return []

    edits = []
    for plan in plans:
        edits.extend(expand_plan(plan, runs))

    apply_edits(edits, runs)

    return [{"original": p.original_text, "fake": p.replacement_text, "type": p.pii_type}
            for p in plans]


def process_paragraph_for_addresses(paragraph, registry: EntityRegistry) -> list[dict]:
    """Detect and replace addresses in a paragraph.

    Handles run-splitting: concatenates runs, detects addresses, maps back.
    Uses the same ReplacementPlan -> RunEdit -> apply_edits() pipeline.

    Known limitation: Cross-paragraph addresses are not detected.
    Each paragraph/cell is processed independently.
    """
    runs = paragraph.runs
    if not runs:
        return []

    mapping, concat_text = build_run_mapping(runs)
    if not concat_text.strip():
        return []

    detections = detect_addresses_in_text(concat_text)
    if not detections:
        return []

    plans = plan_replacements(detections, mapping, registry, runs)
    if not plans:
        return []

    edits = []
    for plan in plans:
        edits.extend(expand_plan(plan, runs))

    apply_edits(edits, runs)

    return [{"original": p.original_text, "fake": p.replacement_text, "type": p.pii_type}
            for p in plans]


def redact_document(input_path: str, output_path: str) -> dict:
    """Redact PII from a .docx document.

    Returns dict with statistics about the redaction.
    """
    doc = load_document(input_path)
    registry = EntityRegistry()

    stats = {
        "email": {"found": 0, "replaced": 0, "unique_originals": set()},
        "phone": {"found": 0, "replaced": 0, "unique_originals": set()},
        "person": {"found": 0, "replaced": 0, "unique_originals": set()},
        "company": {"found": 0, "replaced": 0, "unique_originals": set()},
        "address": {"found": 0, "replaced": 0, "unique_originals": set()},
        "ipv4": {"found": 0, "replaced": 0, "unique_originals": set()},
        "ipv6": {"found": 0, "replaced": 0, "unique_originals": set()},
        "date": {"found": 0, "replaced": 0, "unique_originals": set()},
        "dob": {"found": 0, "replaced": 0, "unique_originals": set()},
        "credit_card": {"found": 0, "replaced": 0, "unique_originals": set()},
        "national_id": {"found": 0, "replaced": 0, "unique_originals": set()},
    }

    def process_paragraph(para):
        # Regex-based: per-run
        for run in para.runs:
            records = process_run(run, registry)
            for r in records:
                pii_type = r["type"]
                if pii_type in stats:
                    stats[pii_type]["found"] += 1
                    stats[pii_type]["replaced"] += 1
                    stats[pii_type]["unique_originals"].add(r["original"])

        # NER-based: per-paragraph (handles run-splitting)
        records = process_paragraph_for_names(para, registry)
        for r in records:
            pii_type = r["type"]
            if pii_type in stats:
                stats[pii_type]["found"] += 1
                stats[pii_type]["replaced"] += 1
                stats[pii_type]["unique_originals"].add(r["original"])

        # Organization detection: per-paragraph (handles run-splitting)
        records = process_paragraph_for_companies(para, registry)
        for r in records:
            pii_type = r["type"]
            if pii_type in stats:
                stats[pii_type]["found"] += 1
                stats[pii_type]["replaced"] += 1
                stats[pii_type]["unique_originals"].add(r["original"])

        # Address detection: per-paragraph (handles run-splitting)
        records = process_paragraph_for_addresses(para, registry)
        for r in records:
            pii_type = r["type"]
            if pii_type in stats:
                stats[pii_type]["found"] += 1
                stats[pii_type]["replaced"] += 1
                stats[pii_type]["unique_originals"].add(r["original"])

    # Walk body paragraphs
    for para in doc.paragraphs:
        process_paragraph(para)

    # Walk table cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    process_paragraph(para)

    save_document(doc, output_path)

    return {
        pii_type: {
            "unique_originals": len(data["unique_originals"]),
            "occurrences_replaced": data["replaced"],
        }
        for pii_type, data in stats.items()
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m pii_redactor input.docx output.docx")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    print(f"Processing: {input_path}")
    stats = redact_document(input_path, output_path)
    print(f"Output: {output_path}")
    print()
    for pii_type, data in stats.items():
        print(f"{pii_type}:")
        print(f"  Unique originals: {data['unique_originals']}")
        print(f"  Occurrences replaced: {data['occurrences_replaced']}")
    print("Done.")


if __name__ == "__main__":
    main()
