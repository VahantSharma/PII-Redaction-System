"""PII detectors — one file per detector, one function per concern."""

from pii_redactor.detectors.detection import Detection
from pii_redactor.detectors.email import detect_emails_in_text
from pii_redactor.detectors.phone import detect_phones_in_text
from pii_redactor.detectors.person import detect_persons_in_text
from pii_redactor.detectors.company import detect_companies_in_text
from pii_redactor.detectors.address import detect_addresses_in_text
from pii_redactor.detectors.ipv4 import detect_ipv4_in_text
from pii_redactor.detectors.ipv6 import detect_ipv6_in_text
from pii_redactor.detectors.date import detect_dates_in_text
from pii_redactor.detectors.credit_card import detect_credit_cards_in_text
from pii_redactor.detectors.national_id import detect_national_ids_in_text

__all__ = [
    "Detection",
    "detect_emails_in_text",
    "detect_phones_in_text",
    "detect_persons_in_text",
    "detect_companies_in_text",
    "detect_addresses_in_text",
    "detect_ipv4_in_text",
    "detect_ipv6_in_text",
    "detect_dates_in_text",
    "detect_credit_cards_in_text",
    "detect_national_ids_in_text",
]
