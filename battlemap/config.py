"""Centralized config: paths, categories, defaults."""
import os

DATA_DIR = '/sdcard/Documents/EldritchBattlemap'
PROJECTS_DIR = os.path.join(DATA_DIR, 'projects')
EXPORTS_DIR = os.path.join(DATA_DIR, 'exports')
IMPORTED_DIR = os.path.join(DATA_DIR, 'imported')
LAST_SESSION_FILE = os.path.join(DATA_DIR, 'last_session.json')

# Bundled assets ship with the APK
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_ASSETS_DIR = os.path.normpath(os.path.join(_THIS_DIR, '..', 'assets', 'bundled'))

# Category names
CATEGORIES = ['Floors', 'Walls', 'Furniture', 'Props', 'Outdoor']

# Grid
DEFAULT_GRID_SIZE = 64.0
MIN_GRID_SIZE = 16.0
MAX_GRID_SIZE = 256.0
GRID_STEP = 8.0

# Asset display
DEFAULT_ASSET_SIZE = 128
THUMBNAIL_SIZE = 96


def ensure_dirs():
    """Make sure all writable directories exist. Safe to call repeatedly."""
    for d in (DATA_DIR, PROJECTS_DIR, EXPORTS_DIR, IMPORTED_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
    # Imported subfolders so the user can find them in the file manager
    for cat in CATEGORIES:
        try:
            os.makedirs(os.path.join(IMPORTED_DIR, cat), exist_ok=True)
        except Exception:
            pass
