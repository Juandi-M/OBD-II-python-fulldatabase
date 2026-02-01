from __future__ import annotations

from ..i18n import t
from ..state import AppState
from ..ui import print_header


def action_lookup_code(state: AppState) -> None:
    print_header(t("lookup_code"))
    code = input(f"\n  {t('lookup_prompt')}: ").strip().upper()
    if not code:
        return
    db = state.ensure_dtc_db()
    desc = db.get_description(code)
    if desc:
        print(f"\n  {code}: {desc}")
    else:
        print(f"\n  {t('no_codes_found')}")


def action_search_codes(state: AppState) -> None:
    print_header(t("search_codes"))
    query = input(f"\n  {t('search_prompt')}: ").strip().lower()
    if not query:
        return
    db = state.ensure_dtc_db()
    results = db.search(query)
    if not results:
        print(f"\n  {t('no_codes_found')}")
        return
    for item in results[:20]:
        print(f"  {item.code}: {item.description}")
