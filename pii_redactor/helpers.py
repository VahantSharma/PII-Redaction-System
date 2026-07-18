"""Shared helpers for detectors.

Not a framework. Just removing the duplicated
finditer -> validate -> Detection boilerplate.
"""

import re

from pii_redactor.detectors.detection import Detection


def regex_detect(
    text: str,
    pattern: re.Pattern[str],
    validator: callable,
    pii_type: str,
    confidence: float = 0.90,
) -> list[Detection]:
    """Detect PII using a regex pattern plus a validation function.

    This helper eliminates the repeated pattern of:
        1. Find regex matches
        2. Validate each match
        3. Create Detection objects

    Args:
        text: Text to search.
        pattern: Compiled regex pattern.
        validator: Callable that returns True if the match is valid.
        pii_type: PII type label for Detection objects.
        confidence: Confidence score (0-1).

    Returns:
        List of Detection objects for valid matches.
    """
    detections: list[Detection] = []
    for match in pattern.finditer(text):
        if validator(match.group()):
            detections.append(
                Detection(
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    pii_type=pii_type,
                    confidence=confidence,
                )
            )
    return detections
