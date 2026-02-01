from .compat import (
    platform_name,
    is_android,
    is_ios,
    supports_classic_serial,
    supports_ble,
)
from .ports import find_bluetooth_ports, is_bluetooth_port_info

__all__ = [
    "platform_name",
    "is_android",
    "is_ios",
    "supports_classic_serial",
    "supports_ble",
    "find_bluetooth_ports",
    "is_bluetooth_port_info",
]
