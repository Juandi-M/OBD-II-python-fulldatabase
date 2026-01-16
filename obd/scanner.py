"""
OBD-II Scanner
==============
High-level scanner interface for vehicle diagnostics.
Includes robust error handling for disconnections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Tuple

from .elm327 import ELM327, DeviceDisconnectedError, CommunicationError
from .pids import PIDS, decode_pid_response, DIAGNOSTIC_PIDS
from .dtc import DTCDatabase, parse_dtc_response, decode_dtc_bytes
from .utils import cr_now

# NEW (Nivel 1): robust parsing helpers
from .obd_parse import group_by_ecu, merge_payloads, find_obd_response_payload


class ScannerError(Exception):
    """Base exception for scanner errors."""
    pass


class NotConnectedError(ScannerError):
    """Raised when operation requires connection but scanner is not connected."""
    pass


class ConnectionLostError(ScannerError):
    """Raised when connection to device is lost during operation."""
    pass


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
    """OBD-II Readiness Monitor Status."""
    monitor_name: str
    available: bool  # Is this monitor supported by the vehicle?
    complete: bool   # Has this monitor completed its self-test?

    @property
    def status_str(self) -> str:
        if not self.available:
            return "N/A"
        return "Complete" if self.complete else "Incomplete"


@dataclass
class FreezeFrameData:
    """Freeze frame data captured when a DTC was set."""
    dtc_code: str
    readings: Dict[str, SensorReading]
    timestamp: datetime = field(default_factory=cr_now)


class OBDScanner:
    """
    High-level OBD-II scanner interface.
    Provides easy-to-use methods for reading DTCs and live data.
    All methods handle disconnection gracefully.
    """

    # Error responses from ELM327
    ERROR_RESPONSES = {"NO DATA", "ERROR", "NO CONNECT", "INVALID", "DISCONNECTED"}

    def __init__(self, port: Optional[str] = None, baudrate: int = 38400, manufacturer: Optional[str] = None):
        self.elm = ELM327(port=port, baudrate=baudrate)
        self.dtc_db = DTCDatabase(manufacturer=manufacturer)
        self._connected = False

    def connect(self) -> bool:
        """Connect to vehicle using current self.elm.port (or auto-select inside ELM)."""
        self.elm.connect()

        # Nivel 1: optional protocol negotiation (doesn't break anything if it fails)
        try:
            self.elm.negotiate_protocol()
        except Exception:
            pass

        if not self.elm.test_vehicle_connection():
            self._connected = False
            raise ConnectionError("No response from vehicle ECU")

        self._connected = True
        return True

    def auto_connect(self) -> str:
        """
        Automatically find and connect to a working ELM327 adapter.
        Returns the port that worked.
        """
        ports = ELM327.find_ports()
        if not ports:
            raise ConnectionError("No USB serial ports found. Is the ELM327 plugged in?")

        last_error: Optional[Exception] = None

        for port in ports:
            try:
                self.elm.port = port
                self.connect()
                return port
            except Exception as e:
                last_error = e
                try:
                    self.disconnect()
                except Exception:
                    pass

        raise ConnectionError(f"No responding OBD device found. Tried: {ports}. Last error: {last_error}")

    def disconnect(self):
        """Disconnect from the adapter."""
        self._connected = False
        try:
            self.elm.close()
        except Exception:
            pass

    @property
    def is_connected(self) -> bool:
        """Check if actually connected (verifies device is still there)."""
        if not self._connected:
            return False
        # Also check the ELM327's connection status
        if not self.elm.is_connected:
            self._connected = False
            return False
        return True

    def _check_connected(self) -> None:
        """Verify we're connected, raise if not."""
        if not self.is_connected:
            raise NotConnectedError("Not connected to vehicle")

    def _handle_disconnection(self) -> None:
        """Handle device disconnection - mark as disconnected."""
        self._connected = False

    def _is_error_response(self, response: str) -> bool:
        """Check if response indicates an error."""
        return response in self.ERROR_RESPONSES

    def set_manufacturer(self, manufacturer: str):
        """Change manufacturer database."""
        self.dtc_db.set_manufacturer(manufacturer)

    # =========================================================================
    # Nivel 1 helper: robust raw-lines OBD parsing (multi-ECU)
    # =========================================================================
    def _obd_query_payload(self, command: str, expected_prefix: List[str]) -> Optional[Tuple[str, List[str]]]:
        """
        Send command using raw lines, group by ECU (requires ATH1 ideally),
        merge payload per ECU, and find the first payload containing expected_prefix.
        Returns (ecu, payload_from_prefix) or None.
        """
        self._check_connected()
        try:
            lines = self.elm.send_obd_lines(command)
        except DeviceDisconnectedError:
            self._handle_disconnection()
            raise ConnectionLostError("Device disconnected")
        except CommunicationError as e:
            raise ScannerError(f"Communication error: {e}")

        grouped = group_by_ecu(lines, headers_on=self.elm.headers_on)
        merged = merge_payloads(grouped, headers_on=self.elm.headers_on)
        found = find_obd_response_payload(merged, expected_prefix)
        return found

    # =========================================================================
    # DTC Methods
    # =========================================================================

    def read_dtcs(self) -> List[DiagnosticCode]:
        """
        Read all diagnostic trouble codes (stored, pending, permanent).

        Raises:
            NotConnectedError: If not connected
            ConnectionLostError: If connection is lost during operation
        """
        self._check_connected()

        dtcs: List[DiagnosticCode] = []
        read_time = cr_now()

        try:
            # Mode 03: Stored DTCs
            # Keep existing logic to avoid breaking parse_dtc_response expectations.
            lines = self.elm.send_obd_lines("03")
            joined = " ".join(lines).upper()
            if "DISCONNECTED" in joined:
                self._handle_disconnection()
                raise ConnectionLostError("Device disconnected while reading DTCs")
            if not any(err in joined for err in ["NO DATA", "UNABLE TO CONNECT", "ERROR", "?"]):
                hex_only = "".join(ch for ch in joined if ch in "0123456789ABCDEF")
                for code in parse_dtc_response(hex_only, "03"):
                    dtcs.append(DiagnosticCode(
                        code=code,
                        description=self.dtc_db.get_description(code),
                        status="stored",
                        timestamp=read_time,
                    ))

            # Mode 07: Pending DTCs
            lines = self.elm.send_obd_lines("07")
            joined = " ".join(lines).upper()
            if "DISCONNECTED" in joined:
                self._handle_disconnection()
                raise ConnectionLostError("Device disconnected while reading pending DTCs")
            if not any(err in joined for err in ["NO DATA", "UNABLE TO CONNECT", "ERROR", "?"]):
                hex_only = "".join(ch for ch in joined if ch in "0123456789ABCDEF")
                for code in parse_dtc_response(hex_only, "07"):
                    if not any(d.code == code for d in dtcs):
                        dtcs.append(DiagnosticCode(
                            code=code,
                            description=self.dtc_db.get_description(code),
                            status="pending",
                            timestamp=read_time,
                        ))

            # Mode 0A: Permanent DTCs (requires CAN protocol)
            lines = self.elm.send_obd_lines("0A")
            joined = " ".join(lines).upper()
            if "DISCONNECTED" in joined:
                self._handle_disconnection()
                raise ConnectionLostError("Device disconnected while reading permanent DTCs")
            if not any(err in joined for err in ["NO DATA", "UNABLE TO CONNECT", "ERROR", "?"]):
                hex_only = "".join(ch for ch in joined if ch in "0123456789ABCDEF")
                for code in parse_dtc_response(hex_only, "0A"):
                    if not any(d.code == code for d in dtcs):
                        dtcs.append(DiagnosticCode(
                            code=code,
                            description=self.dtc_db.get_description(code),
                            status="permanent",
                            timestamp=read_time,
                        ))

        except DeviceDisconnectedError:
            self._handle_disconnection()
            raise ConnectionLostError("Device disconnected")
        except CommunicationError as e:
            raise ScannerError(f"Communication error: {e}")

        return dtcs

    def clear_dtcs(self) -> bool:
        """
        Clear all DTCs (Mode 04). WARNING: Resets readiness monitors!

        Returns:
            True if successful, False otherwise
        """
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

    # =========================================================================
    # Live Data Methods
    # =========================================================================

    def read_pid(self, pid: str) -> Optional[SensorReading]:
        """
        Read a single PID value.

        Returns:
            SensorReading or None if not supported/available

        Raises:
            NotConnectedError: If not connected
            ConnectionLostError: If connection is lost
        """
        self._check_connected()

        pid = pid.upper()
        if pid not in PIDS:
            return None

        pid_info = PIDS[pid]

        # Nivel 1 robust parse: Mode 01 response is 41 <PID> ...
        found = self._obd_query_payload(f"01{pid}", expected_prefix=["41", pid])
        if not found:
            return None

        ecu, payload = found
        # payload: 41 PID A B C...
        if len(payload) < 2:
            return None

        data_tokens = payload[2:]  # drop 41 and PID
        data_hex = "".join(data_tokens)

        value = decode_pid_response(pid, data_hex)
        if value is None:
            return None

        return SensorReading(
            name=pid_info.name,
            value=round(float(value), 2),
            unit=pid_info.unit,
            pid=pid,
            raw_hex=data_hex,
            timestamp=cr_now(),
        )

    def read_live_data(self, pids: Optional[List[str]] = None) -> Dict[str, SensorReading]:
        """
        Read multiple PIDs at once.

        Raises:
            ConnectionLostError: If connection is lost during reading
        """
        if pids is None:
            pids = DIAGNOSTIC_PIDS

        results: Dict[str, SensorReading] = {}
        for pid in pids:
            try:
                reading = self.read_pid(pid)
                if reading:
                    results[reading.pid] = reading
            except ConnectionLostError:
                raise
            except Exception:
                continue
        return results

    # =========================================================================
    # Freeze Frame (Mode 02)
    # =========================================================================

    def read_freeze_frame(self, frame_number: int = 0) -> Optional[FreezeFrameData]:
        """
        Read freeze frame data (Mode 02).

        Freeze frame captures sensor values at the moment a DTC was stored.
        Useful for diagnosing intermittent problems.

        Args:
            frame_number: Which freeze frame to read (usually 0)

        Returns:
            FreezeFrameData object or None if no data available
        """
        self._check_connected()

        try:
            # First, try to get the DTC that triggered the freeze frame
            # Response prefix: 42 02 ...
            found = self._obd_query_payload(f"0202{frame_number:02X}", expected_prefix=["42", "02"])

            dtc_code = "Unknown"
            if found:
                ecu, payload = found
                # payload: 42 02 frame A B...
                if len(payload) >= 5:
                    # after 42 02 frame -> next two bytes are DTC
                    dtc_hex = "".join(payload[3:5])
                    if len(dtc_hex) >= 4:
                        try:
                            dtc_code = decode_dtc_bytes(dtc_hex)
                        except Exception:
                            dtc_code = "Unknown"

            # Now read common freeze frame PIDs
            freeze_pids = ["04", "05", "06", "07", "0B", "0C", "0D", "0E", "0F", "11"]
            readings: Dict[str, SensorReading] = {}

            for pid in freeze_pids:
                if pid not in PIDS:
                    continue

                pid_info = PIDS[pid]
                cmd = f"02{pid}{frame_number:02X}"

                # Response prefix: 42 <PID> ...
                found = self._obd_query_payload(cmd, expected_prefix=["42", pid])
                if not found:
                    continue

                ecu, payload = found
                # payload: 42 PID frame data...
                if len(payload) < 4:
                    continue

                data_tokens = payload[3:]  # drop 42, pid, frame
                data_hex = "".join(data_tokens)

                value = decode_pid_response(pid, data_hex)
                if value is not None:
                    readings[pid] = SensorReading(
                        name=pid_info.name,
                        value=round(float(value), 2),
                        unit=pid_info.unit,
                        pid=pid,
                        raw_hex=data_hex,
                        timestamp=cr_now(),
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

    # =========================================================================
    # Readiness Monitors (Mode 01, PID 01)
    # =========================================================================

    def read_readiness(self) -> Dict[str, ReadinessStatus]:
        """
        Read OBD-II readiness monitor status (Mode 01, PID 01).

        Shows which emission system self-tests have completed.
        Important after clearing DTCs - some tests need specific drive cycles.
        """
        self._check_connected()

        # Robust parse: 41 01 A B C D
        found = self._obd_query_payload("0101", expected_prefix=["41", "01"])
        if not found:
            return {}

        ecu, payload = found
        if len(payload) < 6:
            return {}

        try:
            byte_a = int(payload[2], 16)
            byte_b = int(payload[3], 16)
            byte_c = int(payload[4], 16)
            byte_d = int(payload[5], 16)
        except ValueError:
            return {}

        monitors: Dict[str, ReadinessStatus] = {}

        mil_on = bool(byte_a & 0x80)
        monitors["MIL (Check Engine Light)"] = ReadinessStatus(
            monitor_name="MIL (Check Engine Light)",
            available=True,
            complete=not mil_on,
        )

        is_spark_ignition = not bool(byte_b & 0x08)

        if is_spark_ignition:
            continuous_monitors = [
                ("Misfire", 0),
                ("Fuel System", 1),
                ("Components", 2),
            ]

            for name, bit in continuous_monitors:
                available = bool(byte_b & (1 << bit))
                incomplete = bool(byte_c & (1 << bit))
                monitors[name] = ReadinessStatus(
                    monitor_name=name,
                    available=available,
                    complete=not incomplete if available else False,
                )

            non_continuous_monitors = [
                ("Catalyst", 0),
                ("Heated Catalyst", 1),
                ("Evaporative System", 2),
                ("Secondary Air", 3),
                ("A/C Refrigerant", 4),
                ("Oxygen Sensor", 5),
                ("Oxygen Sensor Heater", 6),
                ("EGR System", 7),
            ]

            for name, d_bit in non_continuous_monitors:
                incomplete = bool(byte_d & (1 << d_bit))
                monitors[name] = ReadinessStatus(
                    monitor_name=name,
                    available=True,
                    complete=not incomplete,
                )
        else:
            diesel_monitors = [
                ("NMHC Catalyst", 0),
                ("NOx/SCR Aftertreatment", 1),
                ("Boost Pressure", 3),
                ("Exhaust Gas Sensor", 5),
                ("PM Filter", 6),
                ("EGR/VVT System", 7),
            ]

            for name, bit in diesel_monitors:
                incomplete = bool(byte_d & (1 << bit))
                monitors[name] = ReadinessStatus(
                    monitor_name=name,
                    available=True,
                    complete=not incomplete,
                )

        return monitors

    def get_mil_status(self) -> Tuple[bool, int]:
        """
        Quick check of MIL status.

        Returns:
            Tuple of (mil_on, dtc_count)
        """
        self._check_connected()

        found = self._obd_query_payload("0101", expected_prefix=["41", "01"])
        if not found:
            return (False, 0)

        ecu, payload = found
        if len(payload) < 3:
            return (False, 0)

        try:
            byte_a = int(payload[2], 16)
            mil_on = bool(byte_a & 0x80)
            dtc_count = byte_a & 0x7F
            return (mil_on, dtc_count)
        except ValueError:
            return (False, 0)

    # =========================================================================
    # Vehicle Info
    # =========================================================================

    def get_vehicle_info(self) -> Dict[str, str]:
        """Get basic vehicle/connection information."""
        self._check_connected()

        info: Dict[str, str] = {}

        try:
            info["protocol"] = self.elm.get_protocol()
            info["elm_version"] = self.elm.elm_version or "unknown"

            # Try to get VIN robustly: 49 02 ...
            found = self._obd_query_payload("0902", expected_prefix=["49", "02"])
            if found:
                ecu, payload = found
                # Typical: 49 02 01 <VIN...>
                vin_tokens = payload[3:] if len(payload) > 3 else []
                vin = ""
                for t in vin_tokens:
                    try:
                        b = int(t, 16)
                        if 32 <= b <= 126:
                            vin += chr(b)
                    except Exception:
                        continue
                if vin:
                    info["vin"] = vin
                info["vin_raw"] = "".join(payload)

            # MIL status
            mil_on, dtc_count = self.get_mil_status()
            info["mil_on"] = "Yes" if mil_on else "No"
            info["dtc_count"] = str(dtc_count)

        except DeviceDisconnectedError:
            self._handle_disconnection()
            raise ConnectionLostError("Device disconnected")

        return info

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
