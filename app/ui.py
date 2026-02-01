from __future__ import annotations

import os
from typing import Iterable, Tuple

from .i18n import t, get_language


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def press_enter() -> None:
    input(f"\n  {t('press_enter')}")


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_subheader(title: str) -> None:
    print("\n" + "-" * 40)
    print(f"  {title}")
    print("-" * 40)


def print_menu(title: str, options: Iterable[Tuple[str, str]]) -> None:
    print("\n" + "╔" + "═" * 58 + "╗")
    print(f"║  {title:<55} ║")
    print("╠" + "═" * 58 + "╣")
    for key, text in options:
        print(f"║  {key}. {text:<53} ║")
    print("╚" + "═" * 58 + "╝")


def print_status(connected: bool, manufacturer: str, log_format: str) -> None:
    conn_status = f"🟢 {t('connected')}" if connected else f"🔴 {t('disconnected')}"
    lang = get_language().upper()
    print(
        f"\n  {t('status')}: {conn_status} | {t('vehicle')}: "
        f"{manufacturer.capitalize()} | {t('format')}: {log_format.upper()} | {lang}"
    )
