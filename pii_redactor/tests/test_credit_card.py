"""Unit tests for Credit Card detector."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.detectors.credit_card import (
    detect_credit_cards_in_text,
    _luhn_check,
    detect_card_brand,
)


# ---------------------------------------------------------------------------
# Luhn algorithm tests
# ---------------------------------------------------------------------------

class TestLuhnAlgorithm:
    """Direct tests of the Luhn validation."""

    def test_valid_visa(self):
        assert _luhn_check("4111111111111111")

    def test_valid_mastercard(self):
        assert _luhn_check("5500000000000004")

    def test_valid_amex(self):
        assert _luhn_check("340000000000009")

    def test_invalid_checksum(self):
        assert not _luhn_check("4111111111111112")

    def test_too_short(self):
        assert not _luhn_check("123456789012")

    def test_too_long(self):
        assert not _luhn_check("12345678901234567890")


# ---------------------------------------------------------------------------
# Brand detection tests
# ---------------------------------------------------------------------------

class TestCardBrandDetection:
    """Test card brand identification."""

    def test_visa(self):
        assert detect_card_brand("4111111111111111") == "Visa"

    def test_mastercard(self):
        assert detect_card_brand("5500000000000004") == "MasterCard"

    def test_amex(self):
        assert detect_card_brand("340000000000009") == "Amex"

    def test_discover(self):
        assert detect_card_brand("6011000000000004") == "Discover"

    def test_unknown_brand(self):
        assert detect_card_brand("1234567890123456") is None


# ---------------------------------------------------------------------------
# Valid detection tests
# ---------------------------------------------------------------------------

class TestCreditCardValid:
    """Valid credit card numbers that must be detected."""

    def test_visa_16_digit(self):
        dets = detect_credit_cards_in_text("Card: 4111111111111111")
        assert len(dets) == 1
        assert dets[0].pii_type == "credit_card"
        assert dets[0].confidence == 0.95

    def test_visa_13_digit(self):
        dets = detect_credit_cards_in_text("Card: 4222222222222")
        assert len(dets) == 1

    def test_mastercard(self):
        dets = detect_credit_cards_in_text("Pay with 5500000000000004")
        assert len(dets) == 1

    def test_amex(self):
        dets = detect_credit_cards_in_text("Amex: 340000000000009")
        assert len(dets) == 1

    def test_with_spaces(self):
        dets = detect_credit_cards_in_text("4111 1111 1111 1111")
        assert len(dets) == 1

    def test_with_dashes(self):
        dets = detect_credit_cards_in_text("4111-1111-1111-1111")
        assert len(dets) == 1


class TestCreditCardInvalid:
    """Invalid credit card numbers that must NOT be detected."""

    def test_invalid_checksum(self):
        assert len(detect_credit_cards_in_text("4111111111111112")) == 0

    def test_all_zeros(self):
        assert len(detect_credit_cards_in_text("0000000000000000")) == 0

    def test_random_digits(self):
        assert len(detect_credit_cards_in_text("1234567890123456")) == 0

    def test_too_short(self):
        assert len(detect_credit_cards_in_text("411111111111")) == 0


class TestCreditCardBoundary:
    """Boundary value tests."""

    def test_min_length_visa(self):
        # 13 digits
        dets = detect_credit_cards_in_text("4222222222222")
        assert len(dets) == 1

    def test_max_length_visa(self):
        # Visa supports 13 and 16 digits (most common).
        # 19-digit Visa exists but is rare; the detector supports 13/16.
        dets = detect_credit_cards_in_text("4111111111111111")
        assert len(dets) == 1
        assert dets[0].pii_type == "credit_card"


class TestCreditCardFormatting:
    """Different formatting styles."""

    def test_in_sentence(self):
        text = "Please charge card 4111111111111111 for the order"
        dets = detect_credit_cards_in_text(text)
        assert len(dets) == 1
        assert text[dets[0].start:dets[0].end] == "4111111111111111"

    def test_with_label(self):
        text = "Card Number: 4111111111111111, Exp: 12/25"
        dets = detect_credit_cards_in_text(text)
        assert len(dets) == 1


class TestCreditCardFalsePositive:
    """False positive rejection tests."""

    def test_phone_number(self):
        assert len(detect_credit_cards_in_text("+91 98765 43210")) == 0

    def test_date(self):
        assert len(detect_credit_cards_in_text("01/15/2024")) == 0

    def test_ssn_format(self):
        assert len(detect_credit_cards_in_text("123-45-6789")) == 0


class TestCreditCardRegression:
    """Regression tests."""

    def test_deterministic(self):
        text = "Card: 4111111111111111"
        assert detect_credit_cards_in_text(text) == detect_credit_cards_in_text(text)

    def test_no_duplicates(self):
        text = "Card: 4111111111111111"
        dets = detect_credit_cards_in_text(text)
        assert len(dets) == 1
