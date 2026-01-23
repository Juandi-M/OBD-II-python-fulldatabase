from __future__ import annotations

from typing import Optional

from .standard_mode01 import PIDS


def decode_pid_response(pid: str, hex_data: str) -> Optional[float]:
    """
    Decode Mode 01 PID response data using the PID's formula.

    Args:
        pid: PID code (e.g., "05")
        hex_data: data bytes only, as hex string, no spaces (e.g., "7B")

    Returns:
        float value or None
    """
    pid = (pid or "").strip().upper()
    if pid not in PIDS:
        return None

    pid_info = PIDS[pid]

    try:
        if pid_info.bytes == 1 and len(hex_data) >= 2:
            a = int(hex_data[0:2], 16)
            return pid_info.formula(a)

        if pid_info.bytes == 2 and len(hex_data) >= 4:
            a = int(hex_data[0:2], 16)
            b = int(hex_data[2:4], 16)
            return pid_info.formula(a, b)

    except (ValueError, TypeError):
        return None

    return None
