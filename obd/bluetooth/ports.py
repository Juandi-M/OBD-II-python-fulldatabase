from __future__ import annotations

import glob
from typing import Iterable, List, Optional, Tuple

import serial.tools.list_ports


def is_bluetooth_port_info(
    device: Optional[str],
    description: Optional[str],
    hwid: Optional[str],
) -> bool:
    dev = (device or "").lower()
    desc = (description or "").lower()
    hw = (hwid or "").lower()

    if "incoming-port" in dev:
        return False

    if dev.startswith("/dev/rfcomm"):
        return True

    if "bluetooth" in desc or "bluetooth" in hw or "bluetooth" in dev:
        return True

    if "bthenum" in hw:
        return True

    if "rfcomm" in desc or "rfcomm" in hw:
        return True

    return False


def find_bluetooth_ports() -> List[str]:
    ports: List[str] = []

    try:
        ports_list = serial.tools.list_ports.comports()
    except Exception:
        ports_list = []

    for p in ports_list:
        if is_bluetooth_port_info(p.device, p.description, getattr(p, "hwid", "")):
            if p.device:
                ports.append(p.device)

    for path in glob.glob("/dev/rfcomm*"):
        if path not in ports:
            ports.append(path)

    return ports
