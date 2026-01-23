from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from ..utils import cr_now


@dataclass
class SensorReading:
    name: str
    value: float
    unit: str
    pid: str
    raw_hex: str
    timestamp: datetime = field(default_factory=cr_now)

    @property
    def timestamp_str(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class DiagnosticCode:
    code: str
    description: str
    status: str  # "stored", "pending", "permanent"
    timestamp: datetime = field(default_factory=cr_now)

    @property
    def timestamp_str(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class ReadinessStatus:
    monitor_name: str
    available: bool
    complete: bool

    @property
    def status_str(self) -> str:
        if not self.available:
            return "N/A"
        return "Complete" if self.complete else "Incomplete"


@dataclass
class FreezeFrameData:
    dtc_code: str
    readings: Dict[str, SensorReading]
    timestamp: datetime = field(default_factory=cr_now)
