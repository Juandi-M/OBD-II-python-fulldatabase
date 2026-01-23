from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class OBDPid:
    """Represents an OBD-II Parameter ID (Mode 01)."""
    pid: str
    name: str
    unit: str
    bytes: int
    formula: Callable
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: Optional[str] = None
