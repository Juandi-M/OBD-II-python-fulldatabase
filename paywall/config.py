from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


CONFIG_DIR = Path.home() / ".obdapp"
CONFIG_PATH = CONFIG_DIR / "config.json"
PAYWALL_KEY = "paywall"


@dataclass
class PaywallIdentity:
    device_id: str
    subject_id: Optional[str]
    access_token: Optional[str]


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_config(config: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _get_paywall_section(config: Dict[str, Any]) -> Dict[str, Any]:
    section = config.get(PAYWALL_KEY)
    if not isinstance(section, dict):
        section = {}
        config[PAYWALL_KEY] = section
    return section


def get_api_base() -> Optional[str]:
    env_base = os.environ.get("PAYWALL_API_BASE")
    if env_base:
        return env_base.strip()
    config = load_config()
    section = _get_paywall_section(config)
    value = section.get("api_base")
    return value.strip() if isinstance(value, str) and value.strip() else None


def set_api_base(api_base: str) -> None:
    config = load_config()
    section = _get_paywall_section(config)
    section["api_base"] = api_base.strip()
    save_config(config)


def ensure_device_id() -> str:
    config = load_config()
    section = _get_paywall_section(config)
    device_id = section.get("device_id")
    if not isinstance(device_id, str) or not device_id.strip():
        device_id = str(uuid.uuid4())
        section["device_id"] = device_id
        save_config(config)
    return device_id


def get_identity() -> PaywallIdentity:
    config = load_config()
    section = _get_paywall_section(config)
    device_id = section.get("device_id")
    if not isinstance(device_id, str) or not device_id.strip():
        device_id = ensure_device_id()
        section = _get_paywall_section(load_config())
    subject_id = section.get("subject_id")
    access_token = section.get("access_token")
    return PaywallIdentity(
        device_id=device_id,
        subject_id=subject_id if isinstance(subject_id, str) else None,
        access_token=access_token if isinstance(access_token, str) else None,
    )


def update_identity(subject_id: str, access_token: str) -> None:
    config = load_config()
    section = _get_paywall_section(config)
    section["subject_id"] = subject_id
    section["access_token"] = access_token
    save_config(config)


def reset_identity() -> None:
    config = load_config()
    section = _get_paywall_section(config)
    section.pop("subject_id", None)
    section.pop("access_token", None)
    save_config(config)


def save_balance(free_remaining: int, paid_credits: int) -> None:
    config = load_config()
    section = _get_paywall_section(config)
    section["balance"] = {
        "free_remaining": int(free_remaining),
        "paid_credits": int(paid_credits),
    }
    save_config(config)


def load_balance() -> Optional[Tuple[int, int]]:
    config = load_config()
    section = _get_paywall_section(config)
    balance = section.get("balance")
    if not isinstance(balance, dict):
        return None
    free_remaining = balance.get("free_remaining")
    paid_credits = balance.get("paid_credits")
    if isinstance(free_remaining, int) and isinstance(paid_credits, int):
        return (free_remaining, paid_credits)
    return None


def is_bypass_enabled() -> bool:
    return _is_truthy(os.environ.get("OBD_SUPERUSER")) or _is_truthy(
        os.environ.get("PAYWALL_BYPASS")
    )


def _is_truthy(value: Optional[str]) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}
