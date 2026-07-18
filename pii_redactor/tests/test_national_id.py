"""Unit tests for National ID (US SSN) detector."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.detectors.national_id import detect_national_ids_in_text


class TestSSNValid:
    """Valid SSNs that must be detected."""

    def test_standard_ssn(self):
        dets = detect_national_ids_in_text("SSN: 123-45-6789")
        assert len(dets) == 1
        assert dets[0].pii_type == "national_id"
        assert dets[0].confidence == 0.95

    def test_low_area_number(self):
        dets = detect_national_ids_in_text("001-01-0001")
        assert len(dets) == 1

    def test_high_area_number(self):
        dets = detect_national_ids_in_text("899-99-9999")
        assert len(dets) == 1


class TestSSNInvalid:
    """Invalid SSNs that must NOT be detected."""

    def test_area_666(self):
        assert len(detect_national_ids_in_text("666-01-0001")) == 0

    def test_area_900(self):
        assert len(detect_national_ids_in_text("900-01-0001")) == 0

    def test_area_000(self):
        assert len(detect_national_ids_in_text("000-01-0001")) == 0

    def test_group_00(self):
        assert len(detect_national_ids_in_text("123-00-6789")) == 0

    def test_serial_0000(self):
        assert len(detect_national_ids_in_text("123-45-0000")) == 0

    def test_area_999(self):
        assert len(detect_national_ids_in_text("999-01-0001")) == 0

    def test_wrong_format_dashes(self):
        assert len(detect_national_ids_in_text("12-345-6789")) == 0

    def test_no_dashes(self):
        assert len(detect_national_ids_in_text("123456789")) == 0


class TestSSNBoundary:
    """Boundary value tests."""

    def test_min_valid_area(self):
        dets = detect_national_ids_in_text("001-01-0001")
        assert len(dets) == 1

    def test_max_valid_area(self):
        dets = detect_national_ids_in_text("899-99-9999")
        assert len(dets) == 1

    def test_area_899(self):
        dets = detect_national_ids_in_text("899-01-0001")
        assert len(dets) == 1

    def test_area_901(self):
        # 901 is in the invalid range
        assert len(detect_national_ids_in_text("901-01-0001")) == 0


class TestSSNFormatting:
    """Different formatting styles."""

    def test_in_sentence(self):
        text = "Please provide your SSN 123-45-6789 for verification"
        dets = detect_national_ids_in_text(text)
        assert len(dets) == 1
        assert text[dets[0].start:dets[0].end] == "123-45-6789"

    def test_with_label(self):
        text = "Social Security Number: 123-45-6789"
        dets = detect_national_ids_in_text(text)
        assert len(dets) == 1


class TestSSNFalsePositive:
    """False positive rejection tests."""

    def test_credit_card(self):
        assert len(detect_national_ids_in_text("4111-1111-1111-1111")) == 0

    def test_phone_number(self):
        assert len(detect_national_ids_in_text("123-456-7890")) == 0

    def test_date(self):
        assert len(detect_national_ids_in_text("12-34-5678")) == 0

    def test_ip_address(self):
        assert len(detect_national_ids_in_text("192-168-1-1")) == 0


class TestSSNRegression:
    """Regression tests."""

    def test_deterministic(self):
        text = "SSN: 123-45-6789"
        assert detect_national_ids_in_text(text) == detect_national_ids_in_text(text)

    def test_offsets_correct(self):
        text = "ID: 123-45-6789 end"
        dets = detect_national_ids_in_text(text)
        assert len(dets) == 1
        assert text[dets[0].start:dets[0].end] == "123-45-6789"

    def test_multiple_ssns(self):
        text = "A: 123-45-6789 and B: 234-56-7890"
        dets = detect_national_ids_in_text(text)
        assert len(dets) == 2
