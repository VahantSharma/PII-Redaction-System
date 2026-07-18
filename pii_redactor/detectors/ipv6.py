"""IPv6 address detector using Python's ipaddress library.

Uses a permissive regex to find candidate sequences, then validates
with ipaddress.IPv6Address. This avoids complex pattern engineering
for every edge case in RFC 5952.
"""

import ipaddress
import re

from pii_redactor.detectors.detection import Detection

# Match any sequence of hex digits and colons (3+ chars), then validate
IPV6_CANDIDATE_PATTERN = re.compile(r"[0-9a-fA-F:]{3,}")


def _validate_ipv6(ip_str: str) -> bool:
    """Validate an IPv6 address using the ipaddress library."""
    try:
        ipaddress.IPv6Address(ip_str)
        if ip_str.count("::") > 1:
            return False
        return True
    except ValueError:
        return False


def _is_boundary_safe(text: str, start: int, end: int) -> bool:
    """Check that the match is not embedded in a longer hex/colon sequence."""
    if start > 0:
        prev = text[start - 1]
        if prev.isalnum() or prev == ":":
            return False
    if end < len(text):
        nxt = text[end]
        if nxt.isalnum() or nxt == ":":
            return False
    return True


def detect_ipv6_in_text(text: str) -> list[Detection]:
    """Detect IPv6 addresses in a text string."""
    detections: list[Detection] = []

    for match in IPV6_CANDIDATE_PATTERN.finditer(text):
        candidate = match.group()
        if not _validate_ipv6(candidate):
            continue
        if not _is_boundary_safe(text, match.start(), match.end()):
            continue

        detections.append(
            Detection(
                text=candidate,
                start=match.start(),
                end=match.end(),
                pii_type="ipv6",
                confidence=0.90,
            )
        )

    return detections
