from __future__ import annotations

import time

from obd.logger import SessionLogger
from obd.utils import cr_time_only

from ..i18n import t
from ..state import AppState
from ..ui import print_header


def action_live_monitor(state: AppState) -> None:
    if not state.scanner or not state.scanner.is_connected:
        print(f"\n  ❌ {t('not_connected')}")
        return

    print_header(t("live_monitor"))
    save = input(f"\n  {t('save_log')} ").strip().lower() == "y"
    logger = SessionLogger() if save else None
    if logger:
        logger.start_session(format=state.log_format)

    state.stop_monitoring = False
    try:
        while True:
            readings = state.scanner.read_live_data()
            print("\n" + "-" * 40)
            print(f"  {t('report_time')}: {cr_time_only()}")
            for reading in readings.values():
                print(f"  {reading.name}: {reading.value} {reading.unit}")
            if logger:
                logger.log_readings(readings)
            time.sleep(state.monitor_interval)
    except KeyboardInterrupt:
        print(f"\n⏹️  {t('cancelled')}")
    finally:
        if logger:
            logger.end_session()
