"""Email address detector."""

import re

from pii_redactor.detectors.detection import Detection

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)


def _validate_email(email: str) -> bool:
    """Reject emails with invalid patterns."""
    # Reject double dots in domain
    if ".." in email.split("@")[1]:
        return False
    # Reject space in local part
    if " " in email.split("@")[0]:
        return False
    return True


def detect_emails_in_text(text: str) -> list[Detection]:
    """Detect email addresses in a text string."""
    return [
        Detection(
            text=match.group(),
            start=match.start(),
            end=match.end(),
            pii_type="email",
            confidence=0.95,
        )
        for match in EMAIL_PATTERN.finditer(text)
        if _validate_email(match.group())
    ]
