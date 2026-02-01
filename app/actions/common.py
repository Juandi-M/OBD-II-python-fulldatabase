from __future__ import annotations

from typing import Optional, Union

from obd import OBDScanner
from obd.legacy_kline.adapter import LegacyKLineAdapter

from app.i18n import t
from app.state import AppState


def require_connected_scanner(
    state: AppState,
) -> Optional[Union[OBDScanner, LegacyKLineAdapter]]:
    scanner = state.active_scanner()
    if not scanner:
        print(f"\n  ❌ {t('not_connected')}")
        return None
    return scanner
