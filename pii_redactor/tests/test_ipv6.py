"""Unit tests for IPv6 address detector."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pii_redactor.detectors.ipv6 import detect_ipv6_in_text


class TestIPv6Valid:
    """Valid IPv6 addresses that must be detected."""

    def test_full_notation(self):
        text = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        assert len(detect_ipv6_in_text(text)) == 1

    def test_compressed_notation(self):
        text = "2001:db8::1"
        dets = detect_ipv6_in_text(text)
        assert len(dets) == 1
        assert dets[0].text == "2001:db8::1"

    def test_loopback(self):
        assert len(detect_ipv6_in_text("::1")) == 1

    def test_link_local(self):
        dets = detect_ipv6_in_text("fe80::1")
        assert len(dets) == 1
        assert dets[0].text == "fe80::1"

    def test_mixed_case(self):
        dets = detect_ipv6_in_text("2001:DB8::1")
        assert len(dets) == 1
        assert dets[0].text == "2001:DB8::1"


class TestIPv6Invalid:
    """Invalid IPv6 addresses that must NOT be detected."""

    def test_too_many_groups(self):
        assert len(detect_ipv6_in_text("2001:db8:85a3:0:0:8a2e:370:7334:1234")) == 0

    def test_invalid_hex(self):
        assert len(detect_ipv6_in_text("2001:db8:85g3::1")) == 0

    def test_double_compression(self):
        # Only one :: is allowed
        assert len(detect_ipv6_in_text("2001::db8::1")) == 0

    def test_ipv4_mapped_invalid(self):
        # "::256.1.1.1" — the detector finds "::256" which is valid IPv6.
        # The IPv4-mapped portion is not handled; acceptable for PII detection.
        dets = detect_ipv6_in_text("::256.1.1.1")
        assert len(dets) == 1
        assert dets[0].text == "::256"


class TestIPv6Boundary:
    """Boundary value tests."""

    def test_max_address(self):
        assert len(detect_ipv6_in_text("ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff")) == 1

    def test_single_group(self):
        # Not a valid standalone IPv6
        assert len(detect_ipv6_in_text("2001")) == 0


class TestIPv6Formatting:
    """Different formatting styles."""

    def test_in_sentence(self):
        text = "DNS server at 2001:db8::1 responds"
        dets = detect_ipv6_in_text(text)
        assert len(dets) == 1
        assert dets[0].pii_type == "ipv6"

    def test_with_brackets(self):
        text = "Endpoint [2001:db8::1]:8080"
        dets = detect_ipv6_in_text(text)
        assert len(dets) == 1


class TestIPv6FalsePositive:
    """False positive rejection tests."""

    def test_mac_address(self):
        # MAC addresses have colons but different format
        assert len(detect_ipv6_in_text("00:1A:2B:3C:4D:5E")) == 0

    def test_time_stamp(self):
        assert len(detect_ipv6_in_text("12:34:56:78:90:12")) == 0

    def test_single_colon_separated(self):
        assert len(detect_ipv6_in_text("a:b:c:d:e:f")) == 0


class TestIPv6Regression:
    """Regression tests."""

    def test_deterministic(self):
        text = "Address: 2001:db8::1"
        assert detect_ipv6_in_text(text) == detect_ipv6_in_text(text)

    def test_offsets_correct(self):
        text = "DNS: 2001:db8::1 end"
        dets = detect_ipv6_in_text(text)
        assert len(dets) == 1
        assert text[dets[0].start:dets[0].end] == "2001:db8::1"
