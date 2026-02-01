from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .config import (
    PaywallIdentity,
    add_pending_consumption,
    ensure_device_id,
    get_api_base,
    get_identity,
    is_offline_enabled,
    load_balance,
    load_pending_consumptions,
    reset_identity,
    save_balance,
    save_pending_consumptions,
    update_identity,
)


@dataclass(frozen=True)
class PaywallBalance:
    free_remaining: int
    paid_credits: int


class PaywallError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PaymentRequired(PaywallError):
    pass


class PaywallClient:
    def __init__(self, api_base: Optional[str] = None, timeout: int = 20) -> None:
        self.api_base = (api_base or get_api_base() or "").rstrip("/")
        self.timeout = timeout
        self._identity: PaywallIdentity = get_identity()
        if not self._identity.device_id:
            ensure_device_id()
            self._identity = get_identity()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_base)

    @property
    def identity(self) -> PaywallIdentity:
        return self._identity

    def ensure_identity(self) -> bool:
        if not self.is_configured:
            return False
        if self._identity.subject_id and self._identity.access_token:
            return True
        payload = {"device_id": self._identity.device_id}
        data = self._request_json("POST", "/v1/identity/anonymous", payload, use_auth=False)
        subject_id = data.get("subject_id")
        access_token = data.get("access_token")
        if not subject_id or not access_token:
            raise PaywallError("Invalid identity response")
        update_identity(subject_id, access_token)
        self._identity = get_identity()
        return True

    def consume(self, action: str, cost: int = 1) -> PaywallBalance:
        self.sync_pending()
        self.ensure_identity()
        payload = {
            "subject_id": self._identity.subject_id,
            "action": action,
            "cost": cost,
        }
        try:
            data = self._request_json("POST", "/v1/credits/consume", payload, use_auth=True)
        except PaywallError as exc:
            if exc.status_code is None and is_offline_enabled():
                return self._offline_consume(action, cost)
            raise
        balance = _parse_balance(data)
        if balance:
            save_balance(balance.free_remaining, balance.paid_credits)
            return balance
        cached = load_balance()
        if cached:
            return PaywallBalance(*cached)
        return PaywallBalance(0, 0)

    def checkout(self) -> str:
        self.ensure_identity()
        payload = {"subject_id": self._identity.subject_id}
        data = self._request_json("POST", "/v1/billing/checkout", payload, use_auth=True)
        url = data.get("checkout_url") or data.get("url")
        if not url:
            raise PaywallError("Checkout URL missing")
        return str(url)

    def get_balance(self) -> PaywallBalance:
        self.ensure_identity()
        data = self._request_json("GET", "/v1/me/balance", None, use_auth=True)
        balance = _parse_balance(data)
        if not balance:
            cached = load_balance()
            if cached:
                return PaywallBalance(*cached)
            return PaywallBalance(0, 0)
        save_balance(balance.free_remaining, balance.paid_credits)
        return balance

    def sync_pending(self) -> None:
        if not self.is_configured:
            return
        pending = load_pending_consumptions()
        if not pending:
            return
        try:
            self.ensure_identity()
        except PaywallError:
            return
        remaining = []
        for item in pending:
            action = item.get("action")
            cost = item.get("cost")
            request_id = item.get("id")
            if not isinstance(action, str) or not isinstance(cost, int) or not request_id:
                continue
            payload = {
                "subject_id": self._identity.subject_id,
                "action": action,
                "cost": cost,
                "request_id": request_id,
            }
            try:
                data = self._request_json(
                    "POST",
                    "/v1/credits/consume",
                    payload,
                    use_auth=True,
                    extra_headers={"Idempotency-Key": str(request_id)},
                )
            except PaywallError as exc:
                remaining.append(item)
                if exc.status_code is None:
                    break
                continue
            balance = _parse_balance(data)
            if balance:
                save_balance(balance.free_remaining, balance.paid_credits)
        save_pending_consumptions(remaining)

    def _offline_consume(self, action: str, cost: int) -> PaywallBalance:
        cached = load_balance()
        if not cached:
            raise PaymentRequired("No cached credits available for offline use.")
        free_remaining, paid_credits = cached
        total = free_remaining + paid_credits
        if total < cost:
            raise PaymentRequired("Insufficient cached credits for offline use.")

        remaining_cost = cost
        use_free = min(free_remaining, remaining_cost)
        free_remaining -= use_free
        remaining_cost -= use_free
        if remaining_cost > 0:
            paid_credits -= remaining_cost

        add_pending_consumption(action, cost)
        save_balance(free_remaining, paid_credits)
        return PaywallBalance(free_remaining, paid_credits)

    def wait_for_balance(
        self,
        *,
        min_paid: int = 1,
        poll_interval: float = 2.0,
        timeout_seconds: int = 120,
    ) -> PaywallBalance:
        start = time.time()
        last_balance = self.get_balance()
        while time.time() - start < timeout_seconds:
            if last_balance.paid_credits >= min_paid:
                return last_balance
            time.sleep(poll_interval)
            last_balance = self.get_balance()
        return last_balance

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]],
        *,
        use_auth: bool,
        retry_auth: bool = True,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            raise PaywallError("Paywall API base URL not configured")

        url = f"{self.api_base}{path}"
        body = None
        headers = {
            "Content-Type": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        if use_auth and self._identity.access_token:
            headers["Authorization"] = f"Bearer {self._identity.access_token}"
        if extra_headers:
            headers.update(extra_headers)

        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else ""
            status = exc.code
            message = _extract_error_message(raw) or exc.reason
            if status == 401:
                reset_identity()
                self._identity = get_identity()
                if use_auth and retry_auth:
                    self.ensure_identity()
                    return self._request_json(
                        method,
                        path,
                        payload,
                        use_auth=use_auth,
                        retry_auth=False,
                    )
            if status == 402:
                raise PaymentRequired(message, status_code=status)
            raise PaywallError(message, status_code=status)
        except urllib.error.URLError as exc:
            raise PaywallError(str(exc)) from exc

        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise PaywallError("Invalid JSON response") from exc
        return data


def _extract_error_message(raw: str) -> Optional[str]:
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    for key in ("error", "message", "detail"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_balance(payload: Dict[str, Any]) -> Optional[PaywallBalance]:
    if not isinstance(payload, dict):
        return None
    free_remaining = payload.get("free_remaining")
    paid_credits = payload.get("paid_credits")
    if isinstance(free_remaining, int) and isinstance(paid_credits, int):
        return PaywallBalance(free_remaining=free_remaining, paid_credits=paid_credits)
    return None
