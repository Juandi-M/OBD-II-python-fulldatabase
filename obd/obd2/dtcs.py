from __future__ import annotations

from typing import List, Optional

from .models import DiagnosticCode, FreezeFrameData, SensorReading
from .base import ConnectionLostError, ScannerError
from ..elm import DeviceDisconnectedError, CommunicationError
from ..dtc import parse_dtc_response, decode_dtc_bytes
from ..pids.standard_mode01 import PIDS
from ..pids.decode import decode_pid_response
from ..utils import cr_now


class DtcMixin:
    """
    DTC + Freeze Frame methods.
    Requires BaseScanner providing:
      - _check_connected()
      - _obd_query_payload()
      - elm, _handle_disconnection()
    Also requires self.dtc_db in concrete class.
    """

    def read_dtcs(self) -> List[DiagnosticCode]:
        self._check_connected()

        dtcs: List[DiagnosticCode] = []
        seen: set[str] = set()
        read_time = cr_now()

        modes = [
            ("03", "stored", ["43"]),
            ("07", "pending", ["47"]),
            ("0A", "permanent", ["4A"]),
        ]

        try:
            for mode, status, prefix in modes:
                found = self._obd_query_payload(mode, expected_prefix=prefix)
                if not found:
                    continue

                ecu, payload = found
                hex_payload = "".join(payload).upper()
                if not hex_payload:
                    continue

                for code in parse_dtc_response(hex_payload, mode):
                    if code in seen:
                        continue
                    seen.add(code)
                    dtcs.append(
                        DiagnosticCode(
                            code=code,
                            description=self.dtc_db.get_description(code),
                            status=status,
                            timestamp=read_time,
                        )
                    )

        except DeviceDisconnectedError:
            self._handle_disconnection()
            raise ConnectionLostError("Device disconnected")
        except CommunicationError as e:
            raise ScannerError(f"Communication error: {e}")

        return dtcs

    def clear_dtcs(self) -> bool:
        self._check_connected()
        try:
            response = self.elm.send_obd("04")
            if response == "DISCONNECTED":
                self._handle_disconnection()
                raise ConnectionLostError("Device disconnected")
            return "44" in response.upper()
        except DeviceDisconnectedError:
            self._handle_disconnection()
            raise ConnectionLostError("Device disconnected")
        except CommunicationError as e:
            raise ScannerError(f"Communication error: {e}")

    def read_freeze_frame(self, frame_number: int = 0) -> Optional[FreezeFrameData]:
        """
        Pragmatic freeze-frame reader:
        - Reads a set of Mode 02 PIDs.
        - DTC for the freeze frame is optional / best-effort (often inconsistent).
        """
        self._check_connected()

        try:
            dtc_code = "Unknown"

            # NOTE: Many ECUs don't provide the freeze-frame DTC in a consistent way via OBD Mode 02.
            # We'll keep it Unknown unless you later validate a working query on a specific vehicle/ECU.

            freeze_pids = ["04", "05", "06", "07", "0B", "0C", "0D", "0E", "0F", "11"]
            readings: dict[str, SensorReading] = {}

            for pid in freeze_pids:
                pid = pid.upper()
                pid_info = PIDS.get(pid)
                if not pid_info:
                    continue

                found = self._obd_query_payload(f"02{pid}", expected_prefix=["42", pid])
                if not found:
                    continue

                ecu, payload = found
                if not payload or len(payload) < 3:
                    continue

                # payload example: ["42", "<PID>", "<A>", "<B>", ...]
                if payload[0].upper() != "42" or payload[1].upper() != pid:
                    continue

                data_tokens = payload[2:]
                data_hex = "".join(data_tokens).upper()

                value = decode_pid_response(pid, data_hex)
                if value is None:
                    continue

                readings[pid] = SensorReading(
                    name=pid_info.name,
                    value=round(float(value), 2),
                    unit=pid_info.unit,
                    pid=pid,
                    raw_hex=data_hex,
                    timestamp=cr_now(),
                    ecu=ecu,  # remove if SensorReading doesn't support ecu
                )

            if not readings:
                return None

            return FreezeFrameData(
                dtc_code=dtc_code,
                readings=readings,
                timestamp=cr_now(),
            )

        except DeviceDisconnectedError:
            self._handle_disconnection()
            raise ConnectionLostError("Device disconnected")
        except CommunicationError as e:
            raise ScannerError(f"Communication error: {e}")
