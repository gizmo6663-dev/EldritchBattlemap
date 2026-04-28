"""PNG export via Widget.export_to_png().

The exported image is the canvas_area widget's pixel content at its
current on-screen size — so it includes both placed assets and the
grid overlay (if visible). To export without grid, hide it first.
"""
import os
from datetime import datetime
from battlemap.config import EXPORTS_DIR, ensure_dirs


def export_canvas_to_png(canvas_area, name='battlemap'):
    ensure_dirs()
    safe = ''.join(c for c in (name or 'battlemap') if c.isalnum() or c in ('-', '_')) or 'battlemap'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{safe}_{timestamp}.png'
    filepath = os.path.join(EXPORTS_DIR, filename)
    try:
        ok = canvas_area.export_to_png(filepath)
        # export_to_png returns True/None depending on Kivy version
        if ok is False:
            return None
        return filepath if os.path.isfile(filepath) else None
    except Exception:
        return None
