from __future__ import annotations

from typing import Any, Dict, Optional

from ..elm import ELM327
from .decoder import decode_did_value
from .dids import find_did, find_did_by_name
from .routines import find_routine
from .services import UdsService
from .transport import UdsTransport
from .exceptions import UdsNegativeResponse, UdsResponseError
from .modules import find_module
from .brands import normalize_brand


def _to_did_bytes(did: str | int) -> bytes:
    if isinstance(did, int):
        return did.to_bytes(2, byteorder="big")
    cleaned = did.strip().replace("0x", "").replace(" ", "")
    return int(cleaned, 16).to_bytes(2, byteorder="big")


def _to_hex_bytes(value: str) -> bytes:
    cleaned = (value or "").strip().replace("0x", "").replace(" ", "")
    return bytes.fromhex(cleaned) if cleaned else b""


class UdsClient:
    """
    High-level UDS client over an ELM327 transport.

    Typical usage:

        elm = ELM327(...)
        # Generic engine ECU (7E0/7E8)
        uds = UdsClient.from_module(elm, "jeep", "generic_engine")

        # VIN via DID F190
        vin_info = uds.read_vin("jeep")

        # Raw reverse-engineering command
        resp = uds.send_raw(0x22, b"\\xF1\\x90")  # 22 F1 90
    """

    def __init__(
        self,
        elm: ELM327,
        tx_id: str = "7E0",
        rx_id: str = "7E8",
        protocol: str = "6",
        auto_configure: bool = True,
    ):
        self.transport = UdsTransport(elm, tx_id=tx_id, rx_id=rx_id, protocol=protocol)
        self._configured = False
        self._auto_configure = auto_configure

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_module(
        cls,
        elm: ELM327,
        brand: str,
        module_name: str,
        protocol: str = "6",
        auto_configure: bool = True,
    ) -> "UdsClient":
        """
        Build a client by looking up CAN IDs from modules.json:

            UdsClient.from_module(elm, "jeep", "generic_engine")
            UdsClient.from_module(elm, "jeep", "bcm")
        """
        norm = normalize_brand(brand)
        mod = find_module(norm, module_name)
        if not mod:
            raise UdsResponseError(
                f"Unknown module '{module_name}' for brand '{norm}'"
            )

        tx_id = (mod.get("tx_id") or "7E0").upper()
        rx_id = (mod.get("rx_id") or "7E8").upper()
        return cls(elm, tx_id=tx_id, rx_id=rx_id, protocol=protocol, auto_configure=auto_configure)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def configure(self) -> None:
        self.transport.configure()
        self._configured = True

    def _ensure_configured(self) -> None:
        if self._auto_configure and not self._configured:
            self.configure()

    def _send_and_expect(self, service_id: int, data: bytes) -> bytes:
        """
        Send a UDS request and EXPECT a positive response for that service.

        Raises:
          - UdsResponseError on empty/malformed response
          - UdsNegativeResponse on 0x7F
        """
        self._ensure_configured()
        request = UdsService.build_request(service_id, data)
        response = self.transport.send(request)

        if not response:
            raise UdsResponseError("Empty UDS response")

        if UdsService.is_negative_response(response):
            svc, nrc = UdsService.parse_negative(response)
            raise UdsNegativeResponse(svc, nrc)

        expected = UdsService.positive_response(service_id)
        if response[0] != expected:
            raise UdsResponseError(
                f"Unexpected response SID 0x{response[0]:02X} "
                f"(expected 0x{expected:02X})"
            )

        return response

    # ------------------------------------------------------------------
    # Generic raw UDS (for reverse engineering)
    # ------------------------------------------------------------------

    def send_raw(
        self,
        service_id: int,
        data: bytes = b"",
        *,
        raise_on_negative: bool = False,
    ) -> bytes:
        """
        Send a raw UDS request and return the raw response bytes.

        This is what you'll use for "Josh-style" reverse engineering:
            - brute forcing DIDs
            - testing routines
            - etc.

        By default it does NOT raise on 0x7F so you can see NRC codes.
        """
        self._ensure_configured()
        request = UdsService.build_request(service_id, data)
        response = self.transport.send(request)

        if not response:
            raise UdsResponseError("Empty UDS response")

        if raise_on_negative and UdsService.is_negative_response(response):
            svc, nrc = UdsService.parse_negative(response)
            raise UdsNegativeResponse(svc, nrc)

        return response

    # ------------------------------------------------------------------
    # Session / tester-present helpers
    # ------------------------------------------------------------------

    def diagnostic_session(self, session_type: int = 0x03) -> None:
        """
        Enter a diagnostic session (0x10).

        Common values:
          - 0x01: default session
          - 0x03: extended diagnostic session
        """
        self._send_and_expect(0x10, bytes([session_type]))

    def tester_present(self) -> None:
        """Send Tester Present (0x3E 00)."""
        self._send_and_expect(0x3E, b"\x00")

    # ------------------------------------------------------------------
    # DID handling
    # ------------------------------------------------------------------

    def read_did(self, brand: str, did: str | int) -> Dict[str, Any]:
        """
        Read a DID (0x22) and decode its value if known.

        Returns:
          {
            "did": "F190",
            "raw": "313233...",
            "name": "VIN",
            "value": "XXX..."
          }
        """
        norm_brand = normalize_brand(brand)
        did_str = f"{int(did):04X}" if isinstance(did, int) else did
        entry = find_did(norm_brand, did_str)

        did_bytes = _to_did_bytes(did)
        response = self._send_and_expect(0x22, did_bytes)

        if len(response) < 3:
            raise UdsResponseError("Response too short for DID read")

        resp_did = response[1:3]
        data = response[3:]

        info: Dict[str, Any] = {
            "did": f"{int.from_bytes(resp_did, 'big'):04X}",
            "raw": data.hex().upper(),
        }
        if entry:
            info["name"] = entry.get("name")
            info["value"] = decode_did_value(entry, data)
        return info

    def read_did_named(self, brand: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Read a DID by logical name, e.g. 'VIN'.
        """
        norm_brand = normalize_brand(brand)
        entry = find_did_by_name(norm_brand, name)
        if not entry:
            return None
        return self.read_did(norm_brand, entry["did"])

    def read_vin(self, brand: str) -> Dict[str, Any]:
        """
        Convenience helper for VIN via DID F190.
        """
        return self.read_did(brand, "F190")

    def write_did(
        self,
        brand: str | None,
        did: str | int,
        data: bytes,
    ) -> Dict[str, Any]:
        """
        WriteDataByIdentifier (0x2E).

        'brand' is only used for metadata lookup; can be None.
        """
        norm_brand = normalize_brand(brand) if brand else None
        did_str = f"{int(did):04X}" if isinstance(did, int) else did

        entry = find_did(norm_brand, did_str) if norm_brand else None
        did_bytes = _to_did_bytes(did)

        payload = did_bytes + data
        response = self._send_and_expect(0x2E, payload)

        if len(response) < 3:
            raise UdsResponseError("Response too short for DID write")

        resp_did = response[1:3]

        info: Dict[str, Any] = {
            "did": f"{int.from_bytes(resp_did, 'big'):04X}",
            "raw": data.hex().upper(),
        }
        if entry:
            info["name"] = entry.get("name")
        return info

    # ------------------------------------------------------------------
    # RoutineControl
    # ------------------------------------------------------------------

    def routine_control(
        self,
        brand: str,
        routine_name: str,
        *,
        subfunction: int = 0x01,
        payload_hex: str = "",
    ) -> Dict[str, Any]:
        """
        Run a RoutineControl (0x31) by logical name from routines.json.

        'subfunction' defaults to 0x01 (start routine).
        'payload_hex' is optional extra data as a hex string (e.g. '01 02').
        """
        norm_brand = normalize_brand(brand)
        routine = find_routine(norm_brand, routine_name)
        if not routine:
            raise UdsResponseError(f"Unknown routine: {routine_name}")

        routine_id = int(routine["routine_id"], 16)
        data = bytes([subfunction]) + routine_id.to_bytes(2, "big") + _to_hex_bytes(payload_hex)
        response = self._send_and_expect(0x31, data)

        return {
            "routine": routine_name,
            "routine_id": routine["routine_id"],
            "status": response[3:].hex().upper() if len(response) > 3 else "",
        }