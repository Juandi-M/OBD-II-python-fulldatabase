from __future__ import annotations

from typing import Dict, Tuple

from .models import ReadinessStatus


class ReadinessMixin:
    def read_readiness(self) -> Dict[str, ReadinessStatus]:
        self._check_connected()

        found = self._obd_query_payload("0101", expected_prefix=["41", "01"])
        if not found:
            return {}

        ecu, payload = found
        if len(payload) < 6:
            return {}

        try:
            A = int(payload[2], 16)
            B = int(payload[3], 16)
            C = int(payload[4], 16)
            D = int(payload[5], 16)
        except ValueError:
            return {}

        monitors: Dict[str, ReadinessStatus] = {}

        mil_on = bool(A & 0x80)
        monitors["MIL (Check Engine Light)"] = ReadinessStatus("MIL (Check Engine Light)", True, not mil_on)

        is_spark = not bool(B & 0x08)

        if is_spark:
            cont = [("Misfire", 0), ("Fuel System", 1), ("Components", 2)]
            for name, bit in cont:
                supported = bool(B & (1 << bit))
                incomplete = bool(C & (1 << bit))
                monitors[name] = ReadinessStatus(name, supported, (not incomplete) if supported else False)

            noncont = [
                ("Catalyst", ("B", 4), 0),
                ("Heated Catalyst", ("B", 5), 1),
                ("Evaporative System", ("B", 6), 2),
                ("Secondary Air", ("B", 7), 3),
                ("A/C Refrigerant", ("C", 3), 4),
                ("Oxygen Sensor", ("C", 4), 5),
                ("Oxygen Sensor Heater", ("C", 5), 6),
                ("EGR System", ("C", 6), 7),
            ]
            for name, (src, bit), d_bit in noncont:
                supported = bool((B if src == "B" else C) & (1 << bit))
                incomplete = bool(D & (1 << d_bit))
                monitors[name] = ReadinessStatus(name, supported, (not incomplete) if supported else False)

        else:
            diesel = [
                ("NMHC Catalyst", ("C", 0), 0),
                ("NOx/SCR Aftertreatment", ("C", 1), 1),
                ("Boost Pressure", ("C", 3), 3),
                ("Exhaust Gas Sensor", ("C", 5), 5),
                ("PM Filter", ("C", 6), 6),
                ("EGR/VVT System", ("C", 7), 7),
            ]
            for name, (_src, bit), d_bit in diesel:
                supported = bool(C & (1 << bit))
                incomplete = bool(D & (1 << d_bit))
                monitors[name] = ReadinessStatus(name, supported, (not incomplete) if supported else False)

        return monitors

    def get_mil_status(self) -> Tuple[bool, int]:
        self._check_connected()

        found = self._obd_query_payload("0101", expected_prefix=["41", "01"])
        if not found:
            return (False, 0)

        ecu, payload = found
        if len(payload) < 3:
            return (False, 0)

        try:
            A = int(payload[2], 16)
        except ValueError:
            return (False, 0)

        mil_on = bool(A & 0x80)
        dtc_count = A & 0x7F
        return (mil_on, dtc_count)
