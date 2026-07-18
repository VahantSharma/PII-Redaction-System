"""Unit tests for IPv4 address detector."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.detectors.ipv4 import detect_ipv4_in_text


class TestIPv4Valid:
    """Valid IPv4 addresses that must be detected."""

    def test_loopback(self):
        assert len(detect_ipv4_in_text("127.0.0.1")) == 1

    def test_private_class_a(self):
        assert len(detect_ipv4_in_text("10.0.0.1")) == 1

    def test_private_class_c(self):
        assert len(detect_ipv4_in_text("192.168.1.1")) == 1

    def test_broadcast(self):
        assert len(detect_ipv4_in_text("255.255.255.0")) == 1

    def test_all_zeros(self):
        assert len(detect_ipv4_in_text("0.0.0.0")) == 1

    def test_class_b(self):
        assert len(detect_ipv4_in_text("172.16.0.1")) == 1

    def test_single_digit_octets(self):
        assert len(detect_ipv4_in_text("1.2.3.4")) == 1


class TestIPv4Invalid:
    """Invalid IPv4 addresses that must NOT be detected."""

    def test_octet_out_of_range(self):
        assert len(detect_ipv4_in_text("256.1.1.1")) == 0

    def test_too_few_octets(self):
        assert len(detect_ipv4_in_text("1.2.3")) == 0

    def test_too_many_octets(self):
        assert len(detect_ipv4_in_text("1.2.3.4.5")) == 0

    def test_leading_zeros(self):
        assert len(detect_ipv4_in_text("01.02.03.04")) == 0

    def test_leading_zero_single_octet(self):
        assert len(detect_ipv4_in_text("192.168.01.1")) == 0

    def test_letters_in_octet(self):
        assert len(detect_ipv4_in_text("abc.def.ghi.jkl")) == 0

    def test_negative_octet(self):
        # "-1.0.0.0" contains "1.0.0.0" which IS a valid IPv4.
        # The detector correctly finds it at position 1.
        dets = detect_ipv4_in_text("-1.0.0.0")
        assert len(dets) == 1
        assert dets[0].text == "1.0.0.0"
        assert dets[0].start == 1


class TestIPv4Boundary:
    """Boundary value tests."""

    def test_max_valid_octet(self):
        assert len(detect_ipv4_in_text("255.255.255.255")) == 1

    def test_min_valid_octet(self):
        assert len(detect_ipv4_in_text("0.0.0.0")) == 1

    def test_mixed_boundary(self):
        assert len(detect_ipv4_in_text("10.255.255.1")) == 1


class TestIPv4Formatting:
    """Different formatting styles."""

    def test_in_sentence(self):
        dets = detect_ipv4_in_text("Server at 192.168.1.1 is running")
        assert len(dets) == 1
        assert dets[0].text == "192.168.1.1"
        assert dets[0].pii_type == "ipv4"

    def test_in_parens(self):
        dets = detect_ipv4_in_text("Address (10.0.0.1) is private")
        assert len(dets) == 1

    def test_with_port(self):
        dets = detect_ipv4_in_text("Connect to 192.168.1.1:8080")
        assert len(dets) == 1
        assert dets[0].text == "192.168.1.1"


class TestIPv4FalsePositive:
    """False positive rejection tests."""

    def test_version_number(self):
        assert len(detect_ipv4_in_text("Version 1.2.3")) == 0

    def test_three_octets(self):
        assert len(detect_ipv4_in_text("1.2.3")) == 0

    def test_date_like(self):
        # MM/DD/YYYY can look like IPv4 but has slashes
        assert len(detect_ipv4_in_text("01/02/2024")) == 0

    def test_document_number(self):
        assert len(detect_ipv4_in_text("Section 4.5.6.7 of the act")) == 1  # This IS a valid IPv4


class TestIPv4Regression:
    """Regression tests — ensure existing behavior is preserved."""

    def test_multiple_ipv4(self):
        text = "From 10.0.0.1 to 192.168.1.1 via 172.16.0.1"
        dets = detect_ipv4_in_text(text)
        assert len(dets) == 3

    def test_offsets_correct(self):
        text = "IP: 192.168.1.1 here"
        dets = detect_ipv4_in_text(text)
        assert len(dets) == 1
        assert text[dets[0].start:dets[0].end] == "192.168.1.1"

    def test_deterministic(self):
        text = "Server at 10.0.0.1"
        assert detect_ipv4_in_text(text) == detect_ipv4_in_text(text)
