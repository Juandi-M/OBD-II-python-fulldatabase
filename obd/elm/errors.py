# obd/elm/errors.py
from __future__ import annotations


class CommunicationError(Exception):
    pass


class DeviceDisconnectedError(CommunicationError):
    pass
