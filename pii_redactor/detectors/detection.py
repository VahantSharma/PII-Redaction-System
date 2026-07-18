"""Detection data type — the single currency between detectors and the replacement engine."""

from typing import NamedTuple


class Detection(NamedTuple):
    """A single PII detection.

    Contract (enforced by tests, not by this class):
        - start < end
        - text == source[start:end]
        - confidence in [0, 1]
        - no negative offsets
        - deterministic output for identical input
    """

    text: str
    start: int
    end: int
    pii_type: str
    confidence: float
