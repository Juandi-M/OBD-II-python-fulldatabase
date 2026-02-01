from __future__ import annotations

from ..i18n import t
from ..state import AppState
from ..ui import print_header, print_menu


def action_settings(state: AppState) -> None:
    while True:
        print_header(t("settings"))
        options = [
            ("1", f"{t('monitor_interval')} ({state.monitor_interval}s)"),
            ("2", f"{t('format')}: {state.log_format.upper()}"),
            ("0", t("exit")),
        ]
        print_menu(t("settings"), options)
        choice = input("\n  > ").strip()
        if choice == "1":
            value = input(f"\n  {t('monitor_interval')}: ").strip()
            try:
                interval = float(value)
            except ValueError:
                print(f"\n  ❌ {t('invalid_number')}")
                continue
            if not 0.5 <= interval <= 10:
                print(f"\n  ❌ {t('invalid_range')}")
                continue
            state.monitor_interval = interval
            print(f"\n  ✅ {t('interval_set', value=interval)}")
        elif choice == "2":
            state.log_format = "json" if state.log_format == "csv" else "csv"
        elif choice == "0":
            return
