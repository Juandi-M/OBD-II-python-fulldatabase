from __future__ import annotations

from typing import List, Optional

from .models import OBDPid
from .standard_mode01 import PIDS


def get_pid_info(pid: str) -> Optional[OBDPid]:
    pid = (pid or "").strip().upper()
    return PIDS.get(pid)


def list_available_pids() -> List[str]:
    return list(PIDS.keys())
