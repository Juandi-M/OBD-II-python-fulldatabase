from __future__ import annotations

import os
import sys


def platform_name() -> str:
    return sys.platform.lower()


def is_android() -> bool:
    return "android" in platform_name() or "ANDROID_ARGUMENT" in os.environ


def is_ios() -> bool:
    return platform_name().startswith("ios")


def supports_classic_serial() -> bool:
    if is_android() or is_ios():
        return False
    return platform_name() in {"win32", "linux", "darwin"}


def supports_ble() -> bool:
    return is_android() or is_ios()
