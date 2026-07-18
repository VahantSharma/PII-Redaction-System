"""National identifier detector (US SSN today, extensible for Aadhaar, PAN, etc.).

Currently supports:
    - US Social Security Number (SSN): XXX-XX-XXXX, XXX XX XXXX, XXXXXXXXX

Designed for easy extension to:
    - Aadhaar (India): 12 digits, may be grouped as XXXX XXXX XXXX
    - PAN (India): 5 letters + 4 digits + 1 letter
    - SIN (Canada): XXX-XXX-XXX
    - NINO (UK): XX XX XX XX
"""

import re

from pii_redactor.detectors.detection import Detection

# ---------------------------------------------------------------------------
# US SSN patterns
# ---------------------------------------------------------------------------

SSN_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),   # XXX-XX-XXXX
    re.compile(r"\b\d{3}\s\d{2}\s\d{4}\b"),  # XXX XX XXXX
]

# SSNs that are invalid regardless of format
_INVALID_SSN_AREAS = {0, 666, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909,
                      910, 911, 912, 913, 914, 915, 916, 917, 918, 919,
                      920, 921, 922, 923, 924, 925, 926, 927, 928, 929,
                      930, 931, 932, 933, 934, 935, 936, 937, 938, 939,
                      940, 941, 942, 943, 944, 945, 946, 947, 948, 949,
                      950, 951, 952, 953, 954, 955, 956, 957, 958, 959,
                      960, 961, 962, 963, 964, 965, 966, 967, 968, 969,
                      970, 971, 972, 973, 974, 975, 976, 977, 978, 979,
                      980, 981, 982, 983, 984, 985, 986, 987, 988, 989,
                      990, 991, 992, 993, 994, 995, 996, 997, 998, 999}


def _validate_ssn(ssn_str: str) -> bool:
    """Validate a US Social Security Number.

    Rules (simplified):
    - Area (first 3 digits): 001-899, excluding 666 and 900-999
    - Group (middle 2 digits): 01-99
    - Serial (last 4 digits): 0001-9999
    """
    digits = re.sub(r"\D", "", ssn_str)
    if len(digits) != 9:
        return False

    area = int(digits[:3])
    group = int(digits[3:5])
    serial = int(digits[5:])

    if area in _INVALID_SSN_AREAS or area < 1:
        return False
    if group < 1 or group > 99:
        return False
    if serial < 1 or serial > 9999:
        return False

    return True


def detect_national_ids_in_text(text: str) -> list[Detection]:
    """Detect national identifiers in a text string.

    Currently detects US SSNs in XXX-XX-XXXX and XXX XX XXXX formats.
    """
    detections: list[Detection] = []
    seen_spans: set[tuple[int, int]] = set()

    for pattern in SSN_PATTERNS:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if span in seen_spans:
                continue

            if _validate_ssn(match.group()):
                seen_spans.add(span)
                detections.append(
                    Detection(
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        pii_type="national_id",
                        confidence=0.95,
                    )
                )

    return sorted(detections, key=lambda d: d.start)
