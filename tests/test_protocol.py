import pytest

from dnsserver.protocol import DNSMessage, DNSPacketError


class TestDNSMessage:
    """Tests for DNS message parsing and response building."""

    def test_parse_valid_header(self):
        """Test parsing a valid DNS header."""
        # Minimal DNS packet: 12-byte header + empty question
        packet = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        message = DNSMessage(packet)
        assert message.header == (0, 0, 0, 0, 0, 0)

    def test_parse_too_short(self):
        """Test that packets shorter than 12 bytes raise an error."""
        with pytest.raises(DNSPacketError, match="DNS packet too short"):
            DNSMessage(b"\x00" * 11)

    def test_question_name_simple(self):
        """Test parsing a simple domain name."""
        # Header + question: google.com
        packet = b"\x00" * 12 + b"\x06google\x03com\x00"
        message = DNSMessage(packet)
        assert message.question_name() == "google.com"

    def test_question_name_single_label(self):
        """Test parsing a single-label domain."""
        packet = b"\x00" * 12 + b"\x07example\x00"
        message = DNSMessage(packet)
        assert message.question_name() == "example"

    def test_build_nxdomain_response(self):
        """Test building an NXDOMAIN response."""
        packet = b"\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00" + b"\x06google\x03com\x00"
        message = DNSMessage(packet)
        response = message.build_nxdomain_response()

        # Check header flags
        assert response[2] == 0x80  # QR=1 (response)
        assert response[3] == 0x83  # RD=1, RCODE=3 (NXDOMAIN)
        # Check that question section is preserved
        assert b"google" in response

    def test_build_response(self):
        """Test building a valid DNS response."""
        packet = b"\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00" + b"\x06google\x03com\x00"
        message = DNSMessage(packet)
        answer = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\x8e\x64\x8e\x65"
        response = message.build_response(answer)

        # Check header flags
        assert response[2] == 0x80  # QR=1 (response)
        assert response[3] == 0x00  # No errors
        # Check ANCOUNT=1
        assert response[6] == 0x00
        assert response[7] == 0x01
