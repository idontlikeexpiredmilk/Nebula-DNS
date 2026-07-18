from __future__ import annotations

import struct
from typing import Final


class DNSPacketError(ValueError):
    """Raised when a malformed DNS packet is encountered."""


class DNSMessage:
    """Minimal DNS message parser/serializer for queries and basic responses."""

    HEADER_STRUCT: Final[struct.Struct] = struct.Struct("!HHHHHH")

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.header = self._parse_header(data)

    def _parse_header(self, data: bytes) -> tuple[int, int, int, int, int, int]:
        if len(data) < 12:
            raise DNSPacketError("DNS packet too short")
        return self.HEADER_STRUCT.unpack(data[:12])

    def question_name(self) -> str:
        offset = 12
        labels: list[str] = []
        jumped = False
        jumped_offset = 0
        while True:
            if offset >= len(self.data):
                raise DNSPacketError("Truncated DNS name")
            length = self.data[offset]
            if length == 0:
                offset += 1
                break
            if length & 0xC0:
                if offset + 1 >= len(self.data):
                    raise DNSPacketError("Malformed pointer")
                pointer = ((length & 0x3F) << 8) | self.data[offset + 1]
                if not jumped:
                    jumped = True
                    jumped_offset = offset + 2
                offset = pointer
                continue
            offset += 1
            labels.append(self.data[offset : offset + length].decode("ascii", errors="replace"))
            offset += length
        if jumped:
            offset = jumped_offset
        return ".".join(labels)

    def build_nxdomain_response(self) -> bytes:
        """Build an NXDOMAIN (non-existent domain) response."""
        response = bytearray(self.data[:12])
        # Set response bit (bit 15), recursion desired (bit 8), and set RCODE to 3 (NXDOMAIN)
        response[2] = 0x80  # QR=1 (response)
        response[3] = 0x83  # RD=1, RCODE=3 (NXDOMAIN)
        response[6] = 0x00  # Clear ANCOUNT
        response[7] = 0x00
        response[8] = 0x00  # Clear NSCOUNT
        response[9] = 0x00
        response[10] = 0x00  # Clear ARCOUNT
        response[11] = 0x00
        # Keep the question section from the original query
        response.extend(self.data[12:])
        return bytes(response)

    def build_response(self, answer: bytes) -> bytes:
        """Build a DNS response with the provided answer section."""
        response = bytearray(self.data[:12])
        # Set response bit (bit 15) and recursion desired
        response[2] = 0x80  # QR=1 (response)
        response[3] = 0x00  # No errors
        # Set ANCOUNT to 1 (one answer record)
        response[6] = 0x00
        response[7] = 0x01
        response[8] = 0x00  # NSCOUNT=0
        response[9] = 0x00
        response[10] = 0x00  # ARCOUNT=0
        response[11] = 0x00
        # Keep the question section and add the answer
        response.extend(self.data[12:])
        response.extend(answer)
        return bytes(response)
