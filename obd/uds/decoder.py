from __future__ import annotations

from typing import Any, Dict


def decode_ascii(data: bytes) -> str:
    """Decode bytes as ASCII, stripping non-printable junk."""
    return data.decode("ascii", errors="ignore").strip()


def decode_uint(data: bytes) -> int:
    """Big-endian unsigned integer."""
    value = 0
    for b in data:
        value = (value << 8) | b
    return value


def decode_hex(data: bytes) -> str:
    """Hex string (uppercase, no spaces)."""
    return data.hex().upper()


def decode_did_value(entry: Dict[str, Any], data: bytes) -> Any:
    """
    Decode a DID value using the 'decoder' key in the entry.

    Supported decoders:
      - "ascii"
      - "uint"
      - "hex" (default)
    """
    decoder = (entry.get("decoder") or "hex").lower()
    if decoder == "ascii":
        return decode_ascii(data)
    if decoder == "uint":
        return decode_uint(data)
    return decode_hex(data)