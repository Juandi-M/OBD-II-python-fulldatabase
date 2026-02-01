from __future__ import annotations

from obd import ELM327
from obd.obd2.base import ConnectionLostError
from obd.utils import cr_timestamp
from obd.legacy_kline.adapter import LegacyKLineAdapter
from obd.legacy_kline.session import LegacyKLineSession
from obd.legacy_kline.profiles import ISO9141_2, KWP2000_5BAUD, KWP2000_FAST, td5_candidates
from obd.legacy_kline.config.errors import KLineDetectError

from app.i18n import t
from app.state import AppState
from app.ui import print_header, handle_disconnection


def connect_vehicle(state: AppState) -> None:
    print_header(t("connect_header"))
    print(f"  {t('time')}: {cr_timestamp()}")

    scanner = state.ensure_scanner()
    if state.active_scanner():
        print(f"\n  ⚠️  {t('already_connected')}")
        confirm = input(f"  {t('disconnect_reconnect')} (y/n): ").strip().lower()
        if confirm not in ["y", "s"]:
            return
        state.disconnect_all()

    print(f"\n🔍 {t('searching_adapter')}")
    ports = ELM327.find_ports()
    if not ports:
        print(f"\n  ❌ {t('no_ports_found')}")
        print(f"  💡 {t('adapter_tip')}")
        return

    print(f"  {t('found_ports', count=len(ports))}")

    for port in ports:
        try:
            print(f"\n  {t('trying_port', port=port)}")
            scanner.elm.port = port
            scanner.connect()
            print(f"  ✅ {t('connected_on', port=port)}")
            state.clear_legacy_scanner()

            try:
                info = scanner.get_vehicle_info()
                print(f"\n  {t('elm_version')}: {info.get('elm_version', 'unknown')}")
                print(f"  {t('protocol')}: {info.get('protocol', 'unknown')}")
                mil_status = f"🔴 {t('on')}" if info.get("mil_on") == "Yes" else f"🟢 {t('off')}"
                print(f"  {t('mil_status')}: {mil_status}")
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

            if _try_kline(state, port):
                return

    print(f"\n  ❌ {t('no_vehicle_response')}")
    print(f"  💡 {t('adapter_tip')}")


def disconnect_vehicle(state: AppState) -> None:
    if not state.active_scanner():
        print(f"\n  ⚠️  {t('disconnected')}")
        return
    state.disconnect_all()
    print(f"\n  🔌 {t('disconnected_at', time=cr_timestamp())}")


def _try_kline(state: AppState, port: str) -> bool:
    print(f"\n  ⚙️  {t('kline_trying')}")
    try:
        elm = ELM327(port=port)
        elm.connect()
    except Exception:
        return False

    candidates = [KWP2000_5BAUD, KWP2000_FAST, ISO9141_2]
    if state.manufacturer == "landrover":
        candidates = candidates + td5_candidates()
    try:
        session = LegacyKLineSession.auto(elm, candidates=candidates)
        adapter = LegacyKLineAdapter(
            session,
            manufacturer=state.manufacturer if state.manufacturer != "generic" else None,
        )
        state.set_legacy_scanner(adapter)
        info = session.info
        print(f"  ✅ {t('kline_detected')}")
        print(f"  {t('kline_profile')}: {info.profile_name}")
        print(f"  {t('kline_reason')}: {info.reason}")
        return True
    except KLineDetectError:
        try:
            elm.close()
        except Exception:
            pass
        return False
    except Exception:
        try:
            elm.close()
        except Exception:
            pass
        return False
