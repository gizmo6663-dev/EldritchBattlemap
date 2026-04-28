"""Scans bundled and user-imported assets, grouped by category."""
import os
from battlemap.config import BUNDLED_ASSETS_DIR, IMPORTED_DIR, CATEGORIES

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}


class AssetLibrary:
    """Discovers asset files in bundled (read-only, in APK) and imported (writable, on device) folders."""

    def __init__(self):
        self.assets_by_category = {cat: [] for cat in CATEGORIES}
        self.refresh()

    def refresh(self):
        for cat in CATEGORIES:
            paths = []
            for base in (BUNDLED_ASSETS_DIR, IMPORTED_DIR):
                folder = os.path.join(base, cat)
                if not os.path.isdir(folder):
                    continue
                try:
                    for name in sorted(os.listdir(folder)):
                        full = os.path.join(folder, name)
                        ext = os.path.splitext(name)[1].lower()
                        if os.path.isfile(full) and ext in IMAGE_EXTENSIONS:
                            paths.append(full)
                except Exception:
                    pass
            self.assets_by_category[cat] = paths

    def categories(self):
        return list(CATEGORIES)

    def assets(self, category):
        return list(self.assets_by_category.get(category, []))
