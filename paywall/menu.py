from __future__ import annotations

import webbrowser

from app.i18n import t
from app.ui import clear_screen, press_enter, print_header, print_menu

from .client import PaywallClient, PaywallError, PaymentRequired
from .config import get_api_base, set_api_base, get_identity, reset_identity


def paywall_menu() -> None:
    while True:
        clear_screen()
        identity = get_identity()
        api_base = get_api_base() or "-"
        subject_id = _short_id(identity.subject_id) if identity.subject_id else "-"
        print_menu(
            t("paywall_menu"),
            [
                ("1", f"{t('paywall_api_base')}: {api_base}"),
                ("2", f"{t('paywall_subject_id')}: {subject_id}"),
                ("3", t("paywall_balance")),
                ("4", t("paywall_checkout")),
                ("5", t("paywall_reset_identity")),
                ("0", t("back")),
            ],
        )
        choice = input(f"\n  {t('select_option')}: ").strip()
        if choice == "1":
            _configure_api_base()
        elif choice == "2":
            _ensure_identity()
        elif choice == "3":
            _show_balance()
        elif choice == "4":
            _start_checkout()
        elif choice == "5":
            reset_identity()
            print(f"\n  {t('paywall_reset_done')}")
            press_enter()
        elif choice == "0":
            break


def _configure_api_base() -> None:
    print_header(t("paywall_api_base"))
    current = get_api_base() or "-"
    print(f"  {t('paywall_current')}: {current}")
    api_base = input(f"\n  {t('paywall_api_base_prompt')}: ").strip()
    if api_base:
        set_api_base(api_base)
        print(f"\n  {t('paywall_api_base_set')}")
    else:
        print(f"\n  {t('invalid_number')}")
    press_enter()


def _ensure_identity() -> None:
    client = PaywallClient()
    if not client.is_configured:
        print(f"\n  {t('paywall_not_configured')}")
        press_enter()
        return
    try:
        client.ensure_identity()
        identity = client.identity
        print(f"\n  {t('paywall_identity_ready')}")
        print(f"  {t('paywall_subject_id')}: {identity.subject_id}")
    except PaywallError as exc:
        print(f"\n  {t('paywall_identity_failed')}: {exc}")
    press_enter()


def _show_balance() -> None:
    client = PaywallClient()
    if not client.is_configured:
        print(f"\n  {t('paywall_not_configured')}")
        press_enter()
        return
    try:
        balance = client.get_balance()
        print(f"\n  {t('paywall_balance')}:")
        print(f"    {t('paywall_free_remaining')}: {balance.free_remaining}")
        print(f"    {t('paywall_paid_credits')}: {balance.paid_credits}")
    except PaywallError as exc:
        print(f"\n  {t('paywall_error')}: {exc}")
    press_enter()


def _start_checkout() -> None:
    client = PaywallClient()
    if not client.is_configured:
        print(f"\n  {t('paywall_not_configured')}")
        press_enter()
        return
    try:
        url = client.checkout()
        print(f"\n  {t('paywall_checkout_url')}: {url}")
        print(f"  {t('paywall_checkout_hint')}")
        webbrowser.open(url)
    except PaymentRequired as exc:
        print(f"\n  {t('paywall_payment_required')}: {exc}")
    except PaywallError as exc:
        print(f"\n  {t('paywall_error')}: {exc}")
    press_enter()


def _short_id(value: str) -> str:
    if len(value) <= 8:
        return value
    return f"{value[:4]}...{value[-4:]}"
