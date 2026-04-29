"""The battlemap build area.

Three stacked layers, bottom to top:
  - floor (FloorBackground)     → tiled texture, drawn under everything
  - assets_layer (FloatLayout)  → placed PlacedAsset (Scatter) widgets
  - grid_overlay (GridOverlay)  → drawn on top, touch-passthrough

v0.3 additions:
  - Floor background layer
  - snap_enabled flag + drag-end snapping
  - Floor tile size auto-tracks grid size
"""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from battlemap.grid_overlay import GridOverlay
from battlemap.placed_asset import PlacedAsset
from battlemap.floor_background import FloorBackground
from battlemap.config import (
    DEFAULT_GRID_SIZE, DEFAULT_ASSET_SIZE, MIN_GRID_SIZE, MAX_GRID_SIZE,
)


class CanvasArea(RelativeLayout):
    def __init__(self, on_asset_longpress=None, **kwargs):
        super().__init__(**kwargs)
        self._on_asset_longpress = on_asset_longpress
        self._selected = None
        self.snap_enabled = False

        # Layer 1 — tiled floor (bottom)
        self.floor = FloorBackground(size_hint=(1, 1), tile_size=DEFAULT_GRID_SIZE)
        self.add_widget(self.floor)

        # Layer 2 — placed assets
        self.assets_layer = FloatLayout(size_hint=(1, 1))
        self.add_widget(self.assets_layer)

        # Layer 3 — grid overlay (top, touch-passthrough)
        self.grid_overlay = GridOverlay(
            size_hint=(1, 1),
            grid_size=DEFAULT_GRID_SIZE,
            visible=True,
        )
        self.add_widget(self.grid_overlay)

        # Floor tile size follows grid size — one tile = one grid cell
        self.grid_overlay.bind(
            grid_size=lambda inst, val: setattr(self.floor, 'tile_size', val)
        )

    # ----- Asset placement -----
    def add_asset(self, source, center=None):
        asset = PlacedAsset(
            source=source,
            base_size=DEFAULT_ASSET_SIZE,
            on_select=self._handle_asset_select,
            on_longpress=self._on_asset_longpress,
            on_drag_end=self._handle_drag_end,
        )
        if center is None:
            center = (self.width / 2, self.height / 2)
        asset.center = center
        self.assets_layer.add_widget(asset)
        self._handle_asset_select(asset)  # newly placed = selected
        return asset

    def restore_asset(self, asset_data):
        """Used by ProjectManager when loading a saved project."""
        asset = PlacedAsset.from_dict(
            asset_data,
            on_select=self._handle_asset_select,
            on_longpress=self._on_asset_longpress,
            on_drag_end=self._handle_drag_end,
        )
        self.assets_layer.add_widget(asset)
        return asset

    def remove_asset(self, asset):
        if asset in self.assets_layer.children:
            self.assets_layer.remove_widget(asset)
        if self._selected is asset:
            self._selected = None

    def clear_assets(self):
        for child in list(self.assets_layer.children):
            self.assets_layer.remove_widget(child)
        self._selected = None

    def all_assets(self):
        # children[0] is on top; reverse so the iterator goes bottom → top
        return list(reversed(self.assets_layer.children))

    # ----- Selection -----
    def _handle_asset_select(self, asset):
        if self._selected is not None and self._selected is not asset:
            self._selected.selected = False
        self._selected = asset
        asset.selected = True
        self.bring_to_front(asset)

    def selected_asset(self):
        if self._selected and self._selected in self.assets_layer.children:
            return self._selected
        return None

    def deselect(self):
        if self._selected:
            self._selected.selected = False
        self._selected = None

    # ----- Z-order -----
    def bring_to_front(self, asset):
        if asset in self.assets_layer.children:
            self.assets_layer.remove_widget(asset)
            self.assets_layer.add_widget(asset)

    def send_to_back(self, asset):
        if asset in self.assets_layer.children:
            self.assets_layer.remove_widget(asset)
            self.assets_layer.add_widget(asset, index=len(self.assets_layer.children))

    # ----- Snap-to-grid -----
    def set_snap_enabled(self, enabled):
        self.snap_enabled = bool(enabled)

    def _handle_drag_end(self, asset):
        if not self.snap_enabled:
            return
        gs = self.grid_overlay.grid_size
        if gs <= 0:
            return
        cx, cy = asset.center
        asset.center = (round(cx / gs) * gs, round(cy / gs) * gs)

    # ----- Floor -----
    def set_floor(self, source):
        return self.floor.set_floor(source)

    def clear_floor(self):
        self.floor.clear_floor()

    # ----- Grid -----
    def toggle_grid(self):
        self.grid_overlay.visible = not self.grid_overlay.visible

    def adjust_grid(self, delta):
        new_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, self.grid_overlay.grid_size + delta))
        self.grid_overlay.grid_size = new_size
