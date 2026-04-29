"""Persists battlemap state to JSON.

- last_session.json    — auto-saved continuously, restored on launch
- projects/<name>.json — manual named saves, loadable on demand

v0.3: floor source is included in serialization. Loaded projects with
missing files (assets or floor) silently skip those items.
"""
import os
import json
from datetime import datetime
from battlemap.config import LAST_SESSION_FILE, PROJECTS_DIR, ensure_dirs


class ProjectManager:
    def __init__(self):
        ensure_dirs()

    # ----- Serialization -----
    def serialize_canvas(self, canvas_area):
        return {
            'version': 2,
            'saved_at': datetime.now().isoformat(),
            'grid': {
                'size': float(canvas_area.grid_overlay.grid_size),
                'visible': bool(canvas_area.grid_overlay.visible),
            },
            'floor': canvas_area.floor.to_dict(),
            'assets': [a.to_dict() for a in canvas_area.all_assets()],
        }

    def deserialize_into(self, canvas_area, data):
        canvas_area.clear_assets()
        canvas_area.clear_floor()

        grid = data.get('grid', {})
        try:
            canvas_area.grid_overlay.grid_size = float(grid.get('size', 64.0))
            canvas_area.grid_overlay.visible = bool(grid.get('visible', True))
        except Exception:
            pass

        floor = data.get('floor') or {}
        try:
            src = floor.get('source', '')
            if src and os.path.isfile(src):
                canvas_area.set_floor(src)
        except Exception:
            pass

        for asset_data in data.get('assets', []):
            try:
                src = asset_data.get('source', '')
                if not src or not os.path.isfile(src):
                    continue
                canvas_area.restore_asset(asset_data)
            except Exception:
                continue

        canvas_area.deselect()

    # ----- Last session (auto) -----
    def save_last_session(self, canvas_area):
        try:
            data = self.serialize_canvas(canvas_area)
            with open(LAST_SESSION_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def load_last_session(self, canvas_area):
        if not os.path.isfile(LAST_SESSION_FILE):
            return False
        try:
            with open(LAST_SESSION_FILE, 'r') as f:
                data = json.load(f)
            self.deserialize_into(canvas_area, data)
            return True
        except Exception:
            return False

    # ----- Named projects (manual) -----
    def save_project(self, canvas_area, name):
        safe = ''.join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe:
            return None
        path = os.path.join(PROJECTS_DIR, f'{safe}.json')
        data = self.serialize_canvas(canvas_area)
        data['name'] = safe
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return path

    def load_project(self, canvas_area, name):
        path = os.path.join(PROJECTS_DIR, f'{name}.json')
        if not os.path.isfile(path):
            return False
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.deserialize_into(canvas_area, data)
            return True
        except Exception:
            return False

    def list_projects(self):
        ensure_dirs()
        try:
            return sorted([
                os.path.splitext(n)[0]
                for n in os.listdir(PROJECTS_DIR)
                if n.lower().endswith('.json')
            ])
        except Exception:
            return []
