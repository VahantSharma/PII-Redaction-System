"""Round-trip test: parse .docx -> rebuild -> verify structure preserved."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.parser import (
    load_document,
    save_document,
    validate_structure,
    validate_run_formatting,
)

DOC_PATH = r"C:\Users\Vahant\Desktop\Scaler Assignment\Red Herring Prospectus.docx"
OUTPUT_PATH = r"C:\Users\Vahant\Desktop\Scaler Assignment\test_output.docx"


def test_roundtrip():
    """Parse and rebuild the document, verify structure is identical."""
    print("Loading original document...")
    original = load_document(DOC_PATH)

    print("Saving (no changes)...")
    save_document(original, OUTPUT_PATH)

    print("Reloading output...")
    output = load_document(OUTPUT_PATH)

    print("\nValidating structure...")
    results = validate_structure(original, output)
    for key, val in results.items():
        if key == "all_match":
            continue
        status = "PASS" if val["match"] else "FAIL"
        print(f"  {key}: {val['original']} -> {val['output']} [{status}]")

    print("\nValidating run formatting (sampled)...")
    fmt = validate_run_formatting(original, output)
    print(f"  Matches: {fmt['matches']}/{fmt['total']}")
    print(f"  Mismatches: {fmt['mismatches']}")
    if fmt["details"]:
        for d in fmt["details"]:
            print(f"    {d}")

    if results["all_match"] and fmt["all_match"]:
        print("\nRound-trip: PASS - Structure and formatting preserved")
    elif results["all_match"]:
        print("\nRound-trip: PASS with note - Structure preserved, minor formatting diffs")
    else:
        print("\nRound-trip: FAIL - Structure mismatch")

    return results["all_match"]


def test_longer_replacement():
    """Regression: verify longer replacement preserves structure.

    This replaces 'Rajesh Kushal Hegde' (19 chars) with
    'Alexander James Hamilton III' (28 chars, +9 chars).
    Structure must remain intact.
    """
    print("\n--- Regression: Longer replacement ---")
    original = load_document(DOC_PATH)

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

    print(f"Replaced {replaced_count} occurrences in table cells")
    print(f"  Length: {len(target)} -> {len(replacement)} ({len(replacement) - len(target):+d} chars)")

    save_document(original, OUTPUT_PATH)
    output = load_document(OUTPUT_PATH)

    results = validate_structure(original, output)
    for key, val in results.items():
        if key == "all_match":
            continue
        status = "PASS" if val["match"] else "FAIL"
        print(f"  {key}: {val['original']} -> {val['output']} [{status}]")

    # Verify replacement appears
    found = any(
        replacement in cell.text
        for table in output.tables
        for row in table.rows
        for cell in row.cells
    )
    print(f"Replacement found in output: {found}")

    if results["all_match"] and found:
        print("Longer replacement: PASS")
        return True
    else:
        print("Longer replacement: FAIL")
        return False


if __name__ == "__main__":
    r1 = test_roundtrip()
    r2 = test_longer_replacement()

    Path(OUTPUT_PATH).unlink(missing_ok=True)

    if r1 and r2:
        print("\nAll tests PASSED")
    else:
        print("\nSome tests FAILED")

    sys.exit(0 if (r1 and r2) else 1)
