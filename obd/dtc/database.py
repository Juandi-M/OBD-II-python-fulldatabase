from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional, List, Dict

from .models import DTCInfo
from .paths import data_dir


class DTCDatabase:
    MANUFACTURER_FILES = {
        "chrysler": "dtc_jeep_dodge_chrysler.csv",
        "jeep": "dtc_jeep_dodge_chrysler.csv",
        "dodge": "dtc_jeep_dodge_chrysler.csv",
        "landrover": "dtc_land_rover.csv",
        "land_rover": "dtc_land_rover.csv",
        "jaguar": "dtc_land_rover.csv",
    }

    def __init__(self, manufacturer: Optional[str] = None):
        self.codes: Dict[str, DTCInfo] = {}
        self.manufacturer = manufacturer
        self._loaded_files: List[str] = []
        self._load_databases()

    def _load_databases(self) -> None:
        dd = data_dir()
        if not dd.exists():
            return

        generic_path = dd / "dtc_generic.csv"
        if generic_path.exists():
            self._load_from_csv(generic_path, "generic")

        if self.manufacturer:
            mfr_lower = self.manufacturer.lower().replace(" ", "_")
            filename = self.MANUFACTURER_FILES.get(mfr_lower)
            if filename:
                p = dd / filename
                if p.exists():
                    self._load_from_csv(p, mfr_lower)
        else:
            loaded_files = set()
            for mfr_name, filename in self.MANUFACTURER_FILES.items():
                if filename in loaded_files:
                    continue
                p = dd / filename
                if p.exists():
                    self._load_from_csv(p, mfr_name)
                    loaded_files.add(filename)

    def _load_from_csv(self, csv_path: Path, source: str) -> None:
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                self._loaded_files.append(csv_path.name)
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    try:
                        row = next(csv.reader([line]))
                    except Exception:
                        continue

                    if len(row) < 2:
                        continue

                    code = row[0].strip().upper()
                    desc = row[1].strip()
                    if not code:
                        continue

                    self.codes[code] = DTCInfo(code=code, description=desc, source=source)

        except (OSError, IOError) as e:
            # No loggers aquí; dejar eso al caller si quiere
            print(f"Warning: Could not load {csv_path}: {e}")

    def set_manufacturer(self, manufacturer: str) -> None:
        self.manufacturer = manufacturer
        self.codes.clear()
        self._loaded_files.clear()
        self._load_databases()

    def lookup(self, code: str) -> Optional[DTCInfo]:
        if not code:
            return None
        return self.codes.get(code.strip().upper())

    def get_description(self, code: str) -> str:
        info = self.lookup(code)
        return info.description if info else "Unknown code - not in database"

    def search(self, query: str) -> List[DTCInfo]:
        if not query:
            return []
        q = query.strip().lower()
        out: List[DTCInfo] = []
        for info in self.codes.values():
            if q in (info.description or "").lower() or q in (info.code or "").lower():
                out.append(info)
        return out

    @property
    def count(self) -> int:
        return len(self.codes)

    @property
    def loaded_files(self) -> List[str]:
        return self._loaded_files.copy()

    @property
    def available_manufacturers(self) -> List[str]:
        dd = data_dir()
        available: List[str] = []
        seen_files = set()
        for mfr, filename in self.MANUFACTURER_FILES.items():
            if filename in seen_files:
                continue
            if (dd / filename).exists():
                available.append(mfr)
                seen_files.add(filename)
        return available
