# obd/elm/ports.py
from __future__ import annotations

from typing import List
import serial.tools.list_ports


def find_ports() -> List[str]:
    ranked: List[tuple[int, str]] = []
    try:
        ports_list = serial.tools.list_ports.comports()
    except Exception:
        return []

    for p in ports_list:
        dev = (p.device or "").lower()
        desc = (p.description or "").lower()

        if "bluetooth" in dev or "debug-console" in dev:
            continue

        score = 0
        if "usb" in desc:
            score += 2
        if any(x in desc for x in ["elm", "ch340", "pl2303", "ftdi", "cp210"]):
            score += 3
        if "usbserial" in dev or "wchusbserial" in dev:
            score += 2
        if "slab_usbtouart" in dev or "silicon labs" in desc:
            score += 2

        if score > 0 and p.device:
            ranked.append((score, p.device))

    ranked.sort(reverse=True)
    return [dev for _, dev in ranked]
