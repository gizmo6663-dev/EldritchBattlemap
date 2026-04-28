"""Eldritch Battlemap — entry point.

Sets up crash logging (consistent with Eldritch Portal) and requests
Android storage permissions before booting Kivy.
"""
import os
import sys
import traceback
from datetime import datetime

DATA_DIR = '/sdcard/Documents/EldritchBattlemap'
CRASH_LOG = os.path.join(DATA_DIR, 'crash.log')


def _log_crash(exc_type, exc_value, exc_tb):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CRASH_LOG, 'a') as f:
            f.write('\n' + ('=' * 60) + '\n')
            f.write(datetime.now().isoformat() + '\n')
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _log_crash

# Request Android permissions before Kivy starts
try:
    from android.permissions import request_permissions, Permission  # type: ignore
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE,
    ])
except ImportError:
    # Desktop dev / non-Android — fine
    pass

from battlemap.app import BattlemapApp  # noqa: E402

if __name__ == '__main__':
    BattlemapApp().run()
