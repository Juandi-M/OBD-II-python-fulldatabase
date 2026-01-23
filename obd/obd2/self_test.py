# obd/obd2/self_test.py
from __future__ import annotations


class SelfTestMixin:
    """
    Minimal self-test utilities.
    Expects BaseScannerMixin to provide:
      - self.elm (connected)
      - self.send_obd(cmd: str) -> str
    """

    def self_test(self) -> dict:
        results = {}

        # ELM present?
        try:
            results["elm_connected"] = bool(self.elm and self.elm.is_connected)
        except Exception:
            results["elm_connected"] = False

        # Vehicle responds to 0100?
        resp = self.send_obd("0100")
        results["0100"] = resp
        results["vehicle_obd_ok"] = ("4100" in resp) if isinstance(resp, str) else False

        return results
