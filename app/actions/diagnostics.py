from __future__ import annotations

from obd.obd2.base import ConnectionLostError, ScannerError
from obd.utils import cr_timestamp

from ..i18n import t
from ..state import AppState
from ..ui import print_header, print_subheader


def _ensure_connected(state: AppState) -> bool:
    if not state.scanner or not state.scanner.is_connected:
        print(f"\n  ❌ {t('not_connected')}")
        return False
    return True


def action_full_scan(state: AppState) -> None:
    if not _ensure_connected(state):
        return

    print_header(t("full_scan"))
    print(f"  🕐 {t('report_time')}: {cr_timestamp()}")

    try:
        print_subheader(t("vehicle"))
        info = state.scanner.get_vehicle_info()
        print(f"  {t('elm_version')}: {info.get('elm_version', 'unknown')}")
        print(f"  {t('protocol')}: {info.get('protocol', 'unknown')}")
        print(f"  {t('mil_status')}: {info.get('mil_on', 'unknown')}")
        print(f"  {t('dtc_count')}: {info.get('dtc_count', 'unknown')}")

        print_subheader(t("read_codes"))
        dtcs = state.scanner.read_dtcs()
        if dtcs:
            for dtc in dtcs:
                emoji = "🚨" if dtc.status == "stored" else "⚠️"
                print(f"\n  {emoji} {dtc.code} ({dtc.status})")
                print(f"     └─ {dtc.description}")
        else:
            print(f"\n  ✅ {t('no_codes')}")

        print_subheader(t("readiness"))
        readiness = state.scanner.read_readiness()
        if readiness:
            for name, status in readiness.items():
                if name == "MIL (Check Engine Light)":
                    continue
                if not status.available:
                    emoji = "➖"
                elif status.complete:
                    emoji = "✅"
                else:
                    emoji = "❌"
                print(f"  {emoji} {name}: {status}")
        else:
            print(f"\n  ⚠️  {t('readiness')}")

    except ConnectionLostError:
        print(f"\n  ❌ {t('not_connected')}")
    except ScannerError as exc:
        print(f"\n  ❌ {exc}")


def action_read_codes(state: AppState) -> None:
    if not _ensure_connected(state):
        return
    print_header(t("read_codes"))
    try:
        dtcs = state.scanner.read_dtcs()
        if not dtcs:
            print(f"\n  ✅ {t('no_codes')}")
            return
        for dtc in dtcs:
            emoji = "🚨" if dtc.status == "stored" else "⚠️"
            print(f"\n  {emoji} {dtc.code} ({dtc.status})")
            print(f"     └─ {dtc.description}")
    except ConnectionLostError:
        print(f"\n  ❌ {t('not_connected')}")


def action_freeze_frame(state: AppState) -> None:
    if not _ensure_connected(state):
        return
    print_header(t("freeze_frame"))
    try:
        frame = state.scanner.read_freeze_frame()
        if not frame:
            print(f"\n  ⚠️  {t('freeze_frame')}")
            return
        print(f"  DTC: {frame.dtc_code}")
        for reading in frame.readings.values():
            print(f"  {reading.name}: {reading.value} {reading.unit}")
    except ConnectionLostError:
        print(f"\n  ❌ {t('not_connected')}")


def action_readiness(state: AppState) -> None:
    if not _ensure_connected(state):
        return
    print_header(t("readiness"))
    readiness = state.scanner.read_readiness()
    if not readiness:
        print(f"\n  ⚠️  {t('readiness')}")
        return
    for name, status in readiness.items():
        if name == "MIL (Check Engine Light)":
            continue
        if not status.available:
            emoji = "➖"
        elif status.complete:
            emoji = "✅"
        else:
            emoji = "❌"
        print(f"  {emoji} {name}: {status}")


def action_clear_codes(state: AppState) -> None:
    if not _ensure_connected(state):
        return
    print_header(t("clear_codes"))
    try:
        ok = state.scanner.clear_dtcs()
        if ok:
            print("\n  ✅ OK")
        else:
            print("\n  ❌ Failed")
    except ConnectionLostError:
        print(f"\n  ❌ {t('not_connected')}")
