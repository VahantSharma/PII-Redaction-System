"""Round-trip test: parse .docx -> rebuild -> verify structure preserved."""

import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.parser import (
    load_document,
    save_document,
    validate_structure,
    validate_run_formatting,
)

DOC_PATH = Path(__file__).resolve().parent.parent.parent / "sample_input.docx"


def test_roundtrip():
    """Parse and rebuild the document, verify structure is identical."""
    original = load_document(str(DOC_PATH))

    with NamedTemporaryFile(suffix=".docx", delete=False) as f:
        output_path = f.name

    try:
        save_document(original, output_path)
        output = load_document(output_path)

        results = validate_structure(original, output)
        assert results["all_match"], f"Structure mismatch: {results}"

        fmt = validate_run_formatting(original, output)
        assert fmt["all_match"], f"Formatting mismatch: {fmt['details']}"

        return True
    finally:
        Path(output_path).unlink(missing_ok=True)


def test_longer_replacement():
    """Regression: verify longer replacement preserves structure.

    This replaces 'Rajesh Kushal Hegde' (19 chars) with
    'Alexander James Hamilton III' (28 chars, +9 chars).
    Structure must remain intact.
    """
    original = load_document(str(DOC_PATH))

    target = "Rajesh Kushal Hegde"
    replacement = "Alexander James Hamilton III"

    replaced_count = 0
    for table in original.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if target in run.text:
                            run.text = run.text.replace(target, replacement)
                            replaced_count += 1

    assert replaced_count > 0, "Target text not found in document"

    with NamedTemporaryFile(suffix=".docx", delete=False) as f:
        output_path = f.name

    try:
        save_document(original, output_path)
        output = load_document(output_path)

        results = validate_structure(original, output)
        assert results["all_match"], f"Structure mismatch: {results}"

        found = any(
            replacement in cell.text
            for table in output.tables
            for row in table.rows
            for cell in row.cells
        )
        assert found, "Replacement text not found in output"

        return True
    finally:
        Path(output_path).unlink(missing_ok=True)


if __name__ == "__main__":
    r1 = test_roundtrip()
    r2 = test_longer_replacement()
    sys.exit(0 if (r1 and r2) else 1)
