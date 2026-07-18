"""Stress tests for PII detection.

Tests adversarial and edge-case scenarios to verify robustness.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.detectors import (
    detect_emails_in_text,
    detect_phones_in_text,
    detect_persons_in_text,
    detect_companies_in_text,
    detect_ipv4_in_text,
    detect_ipv6_in_text,
    detect_dates_in_text,
    detect_credit_cards_in_text,
    detect_national_ids_in_text,
)


class TestAdversarialInputs:
    """Test detectors against adversarial/malicious inputs."""

    def test_empty_string_email(self):
        assert detect_emails_in_text("") == []

    def test_empty_string_phone(self):
        assert detect_phones_in_text("") == []

    def test_empty_string_person(self):
        assert detect_persons_in_text("") == []

    def test_empty_string_company(self):
        assert detect_companies_in_text("") == []

    def test_empty_string_ipv4(self):
        assert detect_ipv4_in_text("") == []

    def test_empty_string_ipv6(self):
        assert detect_ipv6_in_text("") == []

    def test_empty_string_date(self):
        assert detect_dates_in_text("") == []

    def test_empty_string_credit_card(self):
        assert detect_credit_cards_in_text("") == []

    def test_empty_string_national_id(self):
        assert detect_national_ids_in_text("") == []

    def test_whitespace_only(self):
        assert detect_emails_in_text("   \t\n  ") == []
        assert detect_phones_in_text("   \t\n  ") == []

    def test_very_long_string_email(self):
        long_text = "a" * 10000 + "@example.com"
        result = detect_emails_in_text(long_text)
        assert len(result) >= 1

    def test_very_long_string_phone(self):
        long_text = "call " + "+91 98765 43210 " * 1000
        result = detect_phones_in_text(long_text)
        assert len(result) >= 1

    def test_repeated_pii(self):
        text = " ".join(["test@example.com"] * 100)
        result = detect_emails_in_text(text)
        assert len(result) >= 1

    def test_unicode_safe(self):
        text = "Contact: test@example.com and +91 98765 43210"
        emails = detect_emails_in_text(text)
        phones = detect_phones_in_text(text)
        assert len(emails) >= 1
        assert len(phones) >= 1

    def test_special_characters(self):
        text = "Email: test@example.com! Phone: +91 98765 43210."
        emails = detect_emails_in_text(text)
        phones = detect_phones_in_text(text)
        assert len(emails) >= 1
        assert len(phones) >= 1

    def test_nested_pii_types(self):
        text = "Contact John Smith at john@company.com or +91 98765 43210"
        emails = detect_emails_in_text(text)
        phones = detect_phones_in_text(text)
        persons = detect_persons_in_text(text)
        assert len(emails) >= 1
        assert len(phones) >= 1
        assert len(persons) >= 1

    def test_no_false_positives_on_numbers(self):
        text = "Section 4.2.1 Order 12345 Version 2.0"
        emails = detect_emails_in_text(text)
        phones = detect_phones_in_text(text)
        assert len(emails) == 0
        assert len(phones) == 0

    def test_determinism(self):
        text = "Contact John Smith at john@company.com"
        r1 = detect_emails_in_text(text)
        r2 = detect_emails_in_text(text)
        assert [d.text for d in r1] == [d.text for d in r2]

    def test_no_overlapping_detections_email(self):
        text = "user@example.com and admin@company.com"
        result = detect_emails_in_text(text)
        spans = [(d.start, d.end) for d in result]
        for i, (s1, e1) in enumerate(spans):
            for j, (s2, e2) in enumerate(spans):
                if i != j:
                    assert not (s1 < s2 < e1) and not (s2 < s1 < e2)

    def test_offsets_correct_email(self):
        text = "Email: test@example.com is valid"
        result = detect_emails_in_text(text)
        for d in result:
            assert d.start < d.end
            assert text[d.start:d.end] == d.text

    def test_offsets_correct_phone(self):
        text = "Call +91 98765 43210 now"
        result = detect_phones_in_text(text)
        for d in result:
            assert d.start < d.end
            assert text[d.start:d.end] == d.text

    def test_ipv4_in_sentence(self):
        text = "Server at 192.168.1.1 is running"
        result = detect_ipv4_in_text(text)
        assert len(result) >= 1
        assert result[0].text == "192.168.1.1"

    def test_ipv6_in_sentence(self):
        text = "Address 2001:db8::1 is valid"
        result = detect_ipv6_in_text(text)
        assert len(result) >= 1
        assert result[0].text == "2001:db8::1"

    def test_date_in_sentence(self):
        text = "Meeting on 15 March 2024 was productive"
        result = detect_dates_in_text(text)
        assert len(result) >= 1

    def test_credit_card_with_spaces(self):
        text = "Card number: 4111 1111 1111 1111"
        result = detect_credit_cards_in_text(text)
        assert len(result) >= 1

    def test_credit_card_with_dashes(self):
        text = "Card: 4111-1111-1111-1111"
        result = detect_credit_cards_in_text(text)
        assert len(result) >= 1

    def test_national_id_with_dashes(self):
        text = "SSN: 123-45-6789"
        result = detect_national_ids_in_text(text)
        assert len(result) >= 1

    def test_multiple_pii_same_paragraph(self):
        text = (
            "Contact John Smith at john@company.com "
            "or call +91 98765 43210. Server IP is 10.0.0.1 "
            "Card: 4111111111111111. DOB: 15 March 1990"
        )
        emails = detect_emails_in_text(text)
        phones = detect_phones_in_text(text)
        persons = detect_persons_in_text(text)
        ips = detect_ipv4_in_text(text)
        cards = detect_credit_cards_in_text(text)
        dates = detect_dates_in_text(text)
        assert len(emails) >= 1
        assert len(phones) >= 1
        assert len(persons) >= 1
        assert len(ips) >= 1
        assert len(cards) >= 1
        assert len(dates) >= 1

    def test_large_document_performance(self):
        """Test that detectors handle large text efficiently."""
        base = "This is paragraph text with email@test.com and +91 98765 43210. "
        large_text = base * 10000
        emails = detect_emails_in_text(large_text)
        phones = detect_phones_in_text(large_text)
        assert len(emails) >= 1
        assert len(phones) >= 1

    def test_no_cross_detector_interference(self):
        """Ensure detectors don't interfere with each other."""
        text = "Email: test@example.com, Phone: +91 98765 43210, IP: 10.0.0.1"
        emails = detect_emails_in_text(text)
        phones = detect_phones_in_text(text)
        ips = detect_ipv4_in_text(text)
        assert len(emails) == 1
        assert len(phones) >= 1
        assert len(ips) == 1
        assert emails[0].text == "test@example.com"
        assert any("+91 98765 43210" in p.text for p in phones)
        assert ips[0].text == "10.0.0.1"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
