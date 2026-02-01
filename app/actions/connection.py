from __future__ import annotations

from obd import ELM327
from obd.obd2.base import ConnectionLostError
from obd.utils import cr_timestamp

from ..i18n import t
from ..state import AppState
from ..ui import print_header


def handle_disconnection(state: AppState) -> None:
    if state.scanner:
        state.scanner._connected = False
    print(f"\n  ❌ {t('not_connected')}")


def action_connect(state: AppState) -> None:
    print_header(t("connect"))
    print(f"  {t('report_time')}: {cr_timestamp()}")

    scanner = state.ensure_scanner()
    if scanner.is_connected:
        scanner.disconnect()

    print(f"\n🔍 {t('searching_adapter')}")
    ports = ELM327.find_ports()
    if not ports:
        print(f"\n  ❌ {t('no_ports')}")
        return

    for port in ports:
        try:
            print(f"\n  {t('trying_port', port=port)}")
            scanner.elm.port = port
            scanner.connect()
            print(f"  ✅ {t('connected_on', port=port)}")
            try:
                info = scanner.get_vehicle_info()
                print(f"\n  {t('elm_version')}: {info.get('elm_version', 'unknown')}")
                print(f"  {t('protocol')}: {info.get('protocol', 'unknown')}")
                print(f"  {t('mil_status')}: {info.get('mil_on', 'unknown')}")
                print(f"  {t('dtc_count')}: {info.get('dtc_count', '?')}")
            except ConnectionLostError:
                handle_disconnection(state)
            return
        except Exception as exc:
            print(f"  ❌ {t('connection_failed', error=str(exc))}")
            try:
                scanner.disconnect()
            except Exception:
                pass

    print(f"\n  ❌ {t('no_vehicle_response')}")


def action_disconnect(state: AppState) -> None:
    if not state.scanner or not state.scanner.is_connected:
        print(f"\n  ⚠️  {t('disconnected')}")
        return
    state.scanner.disconnect()
    print(f"\n  🔌 {t('disconnected')}")
