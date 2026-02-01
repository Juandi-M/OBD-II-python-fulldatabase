from __future__ import annotations

from typing import List

from obd.uds import UdsClient
from obd.uds.dids import load_standard_dids

from ..i18n import t
from ..state import AppState
from ..ui import print_header, print_menu


STANDARD_DID_KEYS: List[str] = ["F190", "F187", "F188", "F189", "F18C"]


def _ensure_connected(state: AppState) -> bool:
    if not state.scanner or not state.scanner.is_connected:
        print(f"\n  ❌ {t('not_connected')}")
        return False
    return True


def action_uds_tools(state: AppState) -> None:
    if not _ensure_connected(state):
        return

    client = UdsClient(state.scanner.elm)
    while True:
        print_header(t("uds_menu"))
        options = [
            ("1", t("uds_read_standard")),
            ("2", t("uds_run_routine")),
            ("3", t("uds_write_did")),
            ("0", t("exit")),
        ]
        print_menu(t("uds_menu"), options)
        choice = input("\n  > ").strip()
        if choice == "1":
            _read_standard_dids(client)
        elif choice == "2":
            _run_routine(client, state.manufacturer)
        elif choice == "3":
            _write_did(client)
        elif choice == "0":
            return


def _read_standard_dids(client: UdsClient) -> None:
    print_header(t("uds_read_standard"))
    dids = load_standard_dids()
    for entry in dids:
        if entry["did"] not in STANDARD_DID_KEYS:
            continue
        try:
            result = client.read_did("generic", entry["did"])
            name = entry.get("name", entry["did"])
            print(f"  {name}: {result.get('value', result.get('raw'))}")
        except Exception as exc:
            print(f"  {entry['did']}: {exc}")


def _run_routine(client: UdsClient, brand: str) -> None:
    name = input("\n  Routine name: ").strip()
    if not name:
        return
    try:
        result = client.routine_control(brand, name)
        print(f"\n  ✅ {result}")
    except Exception as exc:
        print(f"\n  ❌ {exc}")


def _write_did(client: UdsClient) -> None:
    did = input("\n  DID (hex): ").strip()
    payload = input("  Data (hex): ").strip()
    confirm = input(f"  {t('confirm_write')}").strip()
    if confirm != "YES":
        print(f"\n  {t('cancelled')}")
        return
    try:
        result = client.write_data_by_identifier(did, bytes.fromhex(payload))
        print(f"\n  ✅ {result}")
    except Exception as exc:
        print(f"\n  ❌ {exc}")
