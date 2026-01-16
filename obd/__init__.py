# obd/__init__.py
"""
OBD-II Scanner Package
======================
A modular, multi-language OBD-II diagnostic tool.
"""

from .scanner import (
    OBDScanner, 
    SensorReading, 
    DiagnosticCode, 
    ReadinessStatus, 
    FreezeFrameData,
    ScannerError,
    NotConnectedError,
    ConnectionLostError,
)
from .dtc import DTCDatabase, DTCInfo
from .elm327 import ELM327, CommunicationError, DeviceDisconnectedError
from .pids import PIDS, DIAGNOSTIC_PIDS, THROTTLE_PIDS
from .logger import SessionLogger, QuickLog
from .utils import cr_now, cr_timestamp, CR_TZ, VERSION, APP_NAME
from .lang import t, set_language, get_language, get_available_languages, get_language_name

__version__ = VERSION

__all__ = [
    # Scanner
    "OBDScanner",
    "SensorReading", 
    "DiagnosticCode",
    "ReadinessStatus",
    "FreezeFrameData",
    
    # Exceptions
    "ScannerError",
    "NotConnectedError",
    "ConnectionLostError",
    "CommunicationError",
    "DeviceDisconnectedError",
    
    # DTC
    "DTCDatabase",
    "DTCInfo",
    
    # ELM327
    "ELM327",
    
    # PIDs
    "PIDS",
    "DIAGNOSTIC_PIDS",
    "THROTTLE_PIDS",
    
    # Logger
    "SessionLogger",
    "QuickLog",
    
    # Utils
    "cr_now",
    "cr_timestamp",
    "CR_TZ",
    "VERSION",
    "APP_NAME",
    
    # Language
    "t",
    "set_language",
    "get_language",
    "get_available_languages",
    "get_language_name",
]
