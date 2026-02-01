# obd/elm/ports.py
from __future__ import annotations

from typing import List
import serial.tools.list_ports

from obd.bluetooth.ports import is_bluetooth_port_info

def find_ports(include_bluetooth: bool = False) -> List[str]:
    ranked: List[tuple[int, str]] = []
    try:
        ports_list = serial.tools.list_ports.comports()
    except Exception:
        return []

    for p in ports_list:
        dev = (p.device or "").lower()
        desc = (p.description or "").lower()
        hwid = (getattr(p, "hwid", "") or "").lower()

        if "debug-console" in dev:
            continue
        if not include_bluetooth and is_bluetooth_port_info(dev, desc, hwid):
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
        elif include_bluetooth and is_bluetooth_port_info(dev, desc, hwid) and p.device:
            ranked.append((1, p.device))

    ranked.sort(reverse=True)
    return [dev for _, dev in ranked]
