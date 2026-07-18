"""IPv4 address detector using Python's ipaddress library.

Uses the stdlib ipaddress module for validation instead of
reimplementing RFC rules manually.
"""

import ipaddress
import re

from pii_redactor.detectors.detection import Detection

# IPv4 pattern: four groups of 1-3 digits separated by dots.
# Word boundaries prevent matching inside longer numeric strings.
IPV4_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


def _validate_ipv4(ip_str: str) -> bool:
    """Validate an IPv4 address using the ipaddress library.

    Rejects leading zeros (e.g., "01.02.03.04") to avoid ambiguity.
    Rejects addresses where any octet starts with '0' and has more than one digit.
    """
    try:
        ipaddress.IPv4Address(ip_str)
    except ValueError:
        return False

    # Reject leading zeros
    for part in ip_str.split("."):
        if len(part) > 1 and part.startswith("0"):
            return False

    return True


def detect_ipv4_in_text(text: str) -> list[Detection]:
    """Detect IPv4 addresses in a text string.

    Uses regex to find candidates, then validates with ipaddress library.
    Additional post-match validation rejects addresses embedded in longer
    numeric sequences (e.g., version numbers like "1.2.3.4.5").
    """
    detections: list[Detection] = []
    for match in IPV4_PATTERN.finditer(text):
        candidate = match.group()
        if not _validate_ipv4(candidate):
            continue

        # Reject if embedded in a longer dotted-numeric sequence
        # Check character before match
        if match.start() > 0:
            prev_char = text[match.start() - 1]
            if prev_char.isdigit() or prev_char == ".":
                continue

        # Check character after match
        if match.end() < len(text):
            next_char = text[match.end()]
            if next_char.isdigit() or next_char == ".":
                continue

        detections.append(
            Detection(
                text=candidate,
                start=match.start(),
                end=match.end(),
                pii_type="ipv4",
                confidence=0.90,
            )
        )

    return detections
