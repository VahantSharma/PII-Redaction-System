"""Detector Protocol — formal contract for PII detectors.

This is not a framework. It's a documented contract so every
detector has the same shape and can be composed uniformly.
"""

from typing import Protocol

from pii_redactor.detectors.detection import Detection


class Detector(Protocol):
    """Protocol for PII detectors.

    Every detector must satisfy:
        detect(text: str) -> list[Detection]

    No inheritance required — just match the signature.
    """

    def detect(self, text: str) -> list[Detection]: ...
