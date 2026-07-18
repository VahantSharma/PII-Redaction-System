"""Unit tests for Date detector."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.detectors.date import detect_dates_in_text


class TestDateValid:
    """Valid dates that must be detected."""

    def test_us_format(self):
        dets = detect_dates_in_text("Born on 01/15/1990")
        assert len(dets) >= 1

    def test_iso_format(self):
        dets = detect_dates_in_text("Date: 2024-01-15")
        assert len(dets) >= 1
        assert dets[0].pii_type == "date"

    def test_day_month_year(self):
        dets = detect_dates_in_text("15 January 1990")
        assert len(dets) >= 1

    def test_month_day_year(self):
        dets = detect_dates_in_text("January 15, 1990")
        assert len(dets) >= 1

    def test_month_day_no_comma(self):
        dets = detect_dates_in_text("January 15 1990")
        assert len(dets) >= 1


class TestDateInvalid:
    """Invalid dates that must NOT be detected."""

    def test_impossible_date(self):
        assert len(detect_dates_in_text("13/32/2024")) == 0

    def test_year_out_of_range(self):
        assert len(detect_dates_in_text("01/01/1800")) == 0

    def test_month_zero(self):
        assert len(detect_dates_in_text("00/15/2024")) == 0

    def test_non_date_pattern(self):
        assert len(detect_dates_in_text("Section 4.5.6")) == 0


class TestDateBoundary:
    """Boundary value tests."""

    def test_year_1900(self):
        dets = detect_dates_in_text("01/01/1900")
        assert len(dets) >= 1

    def test_year_2099(self):
        dets = detect_dates_in_text("12/31/2099")
        assert len(dets) >= 1

    def test_leap_year(self):
        dets = detect_dates_in_text("02/29/2024")
        assert len(dets) >= 1

    def test_december_31(self):
        dets = detect_dates_in_text("12/31/2024")
        assert len(dets) >= 1


class TestDateFormatting:
    """Different formatting styles."""

    def test_in_sentence(self):
        text = "The meeting is on 15 January 2024 at noon"
        dets = detect_dates_in_text(text)
        assert len(dets) >= 1
        assert dets[0].pii_type == "date"

    def test_iso_with_time(self):
        text = "Timestamp: 2024-01-15T10:30:00"
        dets = detect_dates_in_text(text)
        assert len(dets) >= 1


class TestDateFalsePositive:
    """False positive rejection tests."""

    def test_version_number(self):
        assert len(detect_dates_in_text("Release 1.2.3")) == 0

    def test_three_digit_number(self):
        assert len(detect_dates_in_text("Call 123-456-7890")) == 0

    def test_phone_number(self):
        assert len(detect_dates_in_text("+91 12345 67890")) == 0


class TestDateDOBContext:
    """DOB contextual detection tests."""

    def test_dob_keyword_before(self):
        text = "Date of birth: 15 January 1990"
        dets = detect_dates_in_text(text)
        assert len(dets) >= 1
        assert dets[0].pii_type == "dob"
        assert dets[0].confidence == 0.90

    def test_dob_keyword_after(self):
        text = "15 January 1990 is the birth date"
        dets = detect_dates_in_text(text)
        assert len(dets) >= 1
        assert dets[0].pii_type == "dob"

    def test_born_keyword(self):
        text = "Born on 01/15/1990 in Mumbai"
        dets = detect_dates_in_text(text)
        assert len(dets) >= 1
        assert dets[0].pii_type == "dob"

    def test_generic_date_no_context(self):
        text = "Meeting on 15 January 2024"
        dets = detect_dates_in_text(text)
        assert len(dets) >= 1
        assert dets[0].pii_type == "date"
        assert dets[0].confidence == 0.70


class TestDateRegression:
    """Regression tests."""

    def test_deterministic(self):
        text = "Date: 15 January 1990"
        assert detect_dates_in_text(text) == detect_dates_in_text(text)

    def test_offsets_correct(self):
        text = "Born: 15 January 1990 here"
        dets = detect_dates_in_text(text)
        assert len(dets) >= 1
        assert text[dets[0].start:dets[0].end] == "15 January 1990"

    def test_multiple_dates(self):
        text = "From 01/01/2024 to 12/31/2024"
        dets = detect_dates_in_text(text)
        assert len(dets) == 2
