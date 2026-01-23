# obd/elm/protocol.py
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from .errors import CommunicationError

if TYPE_CHECKING:
    from .elm327 import ELM327


_PROTOCOL_MAP = {
    "1": "SAE J1850 PWM",
    "2": "SAE J1850 VPW",
    "3": "ISO 9141-2",
    "4": "ISO 14230-4 KWP (5 baud init)",
    "5": "ISO 14230-4 KWP (fast init)",
    "6": "ISO 15765-4 CAN (11 bit, 500 kbaud)",
    "7": "ISO 15765-4 CAN (29 bit, 500 kbaud)",
    "8": "ISO 15765-4 CAN (11 bit, 250 kbaud)",
    "9": "ISO 15765-4 CAN (29 bit, 250 kbaud)",
    "A": "SAE J1939 CAN",
}


def negotiate_protocol(elm: "ELM327") -> str:
    """
    Tries ATSP0 then common CAN protocols.
    Restores ATSP0 if it can't find a working one.
    """
    candidates = ["0", "6", "7", "8", "9"]
    try:
        for p in candidates:
            elm.send_raw_lines(f"ATSP{p}", timeout=1.0)
            time.sleep(0.05)
            lines = elm.send_raw_lines("0100", timeout=max(elm.timeout, 2.0))
            joined = " ".join(lines).upper().replace(" ", "")
            if "4100" in joined:
                return p
    finally:
        try:
            elm.send_raw_lines("ATSP0", timeout=1.0)
        except Exception:
            pass

    raise CommunicationError("Protocol negotiation failed (0100 did not respond)")


def get_protocol(elm: "ELM327") -> str:
    try:
        resp = elm.send_raw("ATDPN", timeout=1.0).strip().upper()
    except Exception:
        return "Unknown (disconnected)"

    code = None
    m = re.search(r"([0-9A-F])", resp)
    if m:
        code = m.group(1)

    if code and code in _PROTOCOL_MAP:
        elm.protocol = _PROTOCOL_MAP[code]
        return elm.protocol

    return f"Unknown: {resp}"
