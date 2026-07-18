"""
Replacement engine: separates detection planning from document mutation.

Architecture:
    detector(text) → list[Detection]
    resolve_overlaps(detections) → list[Detection]
    plan_replacements(detections, mapping, registry) → list[ReplacementPlan]
    expand_plan(plan, runs) → list[RunEdit]
    apply_edits(edits, runs)  ← only mutation point

Design note: see replacement_engine_design.md
"""

from collections import defaultdict
from dataclasses import dataclass

from pii_redactor.detectors.detection import Detection
from pii_redactor.replacer import EntityRegistry


# Type alias: maps concatenated-text position → (run_index, offset_in_run)
RunMapping = list[tuple[int, int]]


@dataclass(frozen=True)
class ReplacementPlan:
    """Immutable logical replacement spanning one or more runs.

    Validity:
        0 <= start_run_idx <= end_run_idx < len(runs)
        0 <= start_offset < end_offset  (strict — no zero-length)
        end_offset <= len(runs[end_run_idx].text)
    """
    start_run_idx: int
    end_run_idx: int
    start_offset: int
    end_offset: int
    original_text: str
    replacement_text: str
    pii_type: str


@dataclass(frozen=True)
class RunEdit:
    """Physical document mutation within a single run."""
    run_idx: int
    start: int
    end: int
    replacement: str


def build_run_mapping(runs) -> tuple[RunMapping, str]:
    """Build mapping from concatenated-text positions to (run_index, offset).

    Invariant 1: Every character in concat_text maps to exactly one
    (run_index, offset). Runs are sequential and non-overlapping.
    """
    mapping: RunMapping = []
    concat_text = ""
    for i, run in enumerate(runs):
        for j in range(len(run.text)):
            mapping.append((i, j))
        concat_text += run.text
    return mapping, concat_text


def resolve_overlaps(detections: list[Detection]) -> list[Detection]:
    """Remove overlapping detections. Longest match wins; ties broken by earliest start.

    Algorithm:
        1. Sort by: longest match first, then earliest start
        2. Greedily accept non-overlapping detections
        3. Reject every overlapping detection

    Guarantee: returned detections never overlap.
    """
    sorted_dets = sorted(detections, key=lambda d: (-(d.end - d.start), d.start))

    accepted: list[Detection] = []
    occupied: set[int] = set()

    for det in sorted_dets:
        positions = set(range(det.start, det.end))
        if not positions & occupied:
            accepted.append(det)
            occupied |= positions

    return accepted


def plan_replacements(
    detections: list[Detection],
    mapping: RunMapping,
    registry: EntityRegistry,
    runs,
) -> list[ReplacementPlan]:
    """Convert detections to ReplacementPlan objects.

    Invariant 7: Every accepted detection generates exactly one ReplacementPlan.
    """
    plans: list[ReplacementPlan] = []

    for detection in resolve_overlaps(detections):
        start_run, start_off = mapping[detection.start]
        end_idx = min(detection.end - 1, len(mapping) - 1)
        end_run, end_off = mapping[end_idx]
        end_off += 1  # make exclusive

        # Get existing fake or create new one
        fake = registry.get_fake(detection.text, detection.pii_type)

        plans.append(ReplacementPlan(
            start_run_idx=start_run,
            end_run_idx=end_run,
            start_offset=start_off,
            end_offset=end_off,
            original_text=detection.text,
            replacement_text=fake,
            pii_type=detection.pii_type,
        ))

    return plans


def expand_plan(plan: ReplacementPlan, runs) -> list[RunEdit]:
    """Convert a ReplacementPlan into one or more RunEdit objects.

    Single-run plan → one RunEdit.
    Multi-run plan → first run (start to end), middle runs (clear), last run (start to end).
    """
    if plan.start_run_idx == plan.end_run_idx:
        return [RunEdit(
            run_idx=plan.start_run_idx,
            start=plan.start_offset,
            end=plan.end_offset,
            replacement=plan.replacement_text,
        )]

    edits: list[RunEdit] = []

    # First run: start_offset to end of run
    edits.append(RunEdit(
        run_idx=plan.start_run_idx,
        start=plan.start_offset,
        end=len(runs[plan.start_run_idx].text),
        replacement=plan.replacement_text,
    ))

    # Middle runs: clear entirely
    for mid in range(plan.start_run_idx + 1, plan.end_run_idx):
        edits.append(RunEdit(
            run_idx=mid,
            start=0,
            end=len(runs[mid].text),
            replacement="",
        ))

    # Last run: start of run to end_offset
    edits.append(RunEdit(
        run_idx=plan.end_run_idx,
        start=0,
        end=plan.end_offset,
        replacement="",
    ))

    return edits


def apply_edits(edits: list[RunEdit], runs):
    """Apply RunEdits to runs. SOLE MUTATION POINT.

    Only this function modifies run.text.
    Edits are applied per run in descending order.
    """
    by_run: dict[int, list[RunEdit]] = defaultdict(list)
    for edit in edits:
        by_run[edit.run_idx].append(edit)

    for run_idx, run_edits in by_run.items():
        run = runs[run_idx]
        for edit in sorted(run_edits, key=lambda e: e.start, reverse=True):
            run.text = run.text[:edit.start] + edit.replacement + run.text[edit.end:]
