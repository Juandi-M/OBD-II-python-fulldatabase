from __future__ import annotations

from typing import Dict, List, Tuple

from .actions.ai_report import action_ai_report
from .actions.connection import action_connect, action_disconnect
from .actions.diagnostics import (
    action_full_scan,
    action_read_codes,
    action_freeze_frame,
    action_readiness,
    action_clear_codes,
)
from .actions.monitoring import action_live_monitor
from .actions.lookup import action_lookup_code, action_search_codes
from .actions.settings import action_settings
from .actions.uds import action_uds_tools
from .i18n import get_available_languages, set_language, t
from .state import AppState
from .ui import clear_screen, print_header, print_menu, print_status, press_enter


def _select_language() -> None:
    options: Dict[str, str] = get_available_languages()
    while True:
        print_header(t("select_language"))
        for code, label in options.items():
            print(f"  {code}: {label}")
        choice = input("\n  > ").strip().lower()
        if choice in options:
            set_language(choice)
            return


def _select_brand(state: AppState) -> None:
    brands = ["generic", "jeep", "land_rover"]
    print_header(t("select_brand"))
    print(f"  1. {t('brand_generic')}")
    print("  2. Jeep")
    print("  3. Land Rover")
    choice = input("\n  > ").strip()
    if choice == "2":
        state.set_manufacturer("jeep")
    elif choice == "3":
        state.set_manufacturer("land_rover")
    else:
        state.set_manufacturer("generic")


def run_cli() -> None:
    clear_screen()
    _select_language()
    state = AppState()
    _select_brand(state)

    menu_items: List[Tuple[str, str, callable]] = [
        ("1", t("connect"), lambda: action_connect(state)),
        ("2", t("disconnect"), lambda: action_disconnect(state)),
        ("3", t("full_scan"), lambda: action_full_scan(state)),
        ("4", t("read_codes"), lambda: action_read_codes(state)),
        ("5", t("live_monitor"), lambda: action_live_monitor(state)),
        ("6", t("freeze_frame"), lambda: action_freeze_frame(state)),
        ("7", t("readiness"), lambda: action_readiness(state)),
        ("8", t("clear_codes"), lambda: action_clear_codes(state)),
        ("9", t("lookup_code"), lambda: action_lookup_code(state)),
        ("10", t("search_codes"), lambda: action_search_codes(state)),
        ("11", t("uds_tools"), lambda: action_uds_tools(state)),
        ("12", t("ai_report"), action_ai_report),
        ("S", t("settings"), lambda: action_settings(state)),
        ("0", t("exit"), lambda: None),
    ]

    while True:
        clear_screen()
        print_header(t("app_title"))
        connected = state.scanner.is_connected if state.scanner else False
        print_status(connected, state.manufacturer, state.log_format)
        print_menu(t("main_menu"), [(k, label) for k, label, _ in menu_items])
        choice = input("\n  > ").strip().upper()
        if choice == "0":
            return
        matched = next((item for item in menu_items if item[0] == choice), None)
        if matched:
            matched[2]()
            press_enter()
