"""The battlemap build area.

Two stacked layers:
  - assets_layer (FloatLayout)  → placed PlacedAsset (Scatter) widgets
  - grid_overlay (GridOverlay)  → drawn on top, touch-passthrough

v0.2: tracks the explicit `_selected` asset (no more "children[0]" guessing),
forwards long-press events to App for the per-asset menu, and brings any
touched asset to the front automatically.
"""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from battlemap.grid_overlay import GridOverlay
from battlemap.placed_asset import PlacedAsset
from battlemap.config import (
    DEFAULT_GRID_SIZE, DEFAULT_ASSET_SIZE, MIN_GRID_SIZE, MAX_GRID_SIZE,
)


class CanvasArea(RelativeLayout):
    def __init__(self, on_asset_longpress=None, **kwargs):
        super().__init__(**kwargs)
        self._on_asset_longpress = on_asset_longpress
        self._selected = None

        self.assets_layer = FloatLayout(size_hint=(1, 1))
        self.add_widget(self.assets_layer)

        self.grid_overlay = GridOverlay(
            size_hint=(1, 1),
            grid_size=DEFAULT_GRID_SIZE,
            visible=True,
        )
        self.add_widget(self.grid_overlay)

    # ----- Asset placement -----
    def add_asset(self, source, center=None):
        asset = PlacedAsset(
            source=source,
            base_size=DEFAULT_ASSET_SIZE,
            on_select=self._handle_asset_select,
            on_longpress=self._on_asset_longpress,
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
        # (matches paint order, which is what we want for save/restore).
        return list(reversed(self.assets_layer.children))

    # ----- Selection -----
    def _handle_asset_select(self, asset):
        # Deselect previous
        if self._selected is not None and self._selected is not asset:
            self._selected.selected = False
        self._selected = asset
        asset.selected = True
        # Touched asset rises to top (visual + Front/Back actions feel right)
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
            self.assets_layer.add_widget(asset)  # default index 0 → top

    def send_to_back(self, asset):
        if asset in self.assets_layer.children:
            self.assets_layer.remove_widget(asset)
            self.assets_layer.add_widget(asset, index=len(self.assets_layer.children))

    # ----- Grid -----
    def toggle_grid(self):
        self.grid_overlay.visible = not self.grid_overlay.visible

    def adjust_grid(self, delta):
        new_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, self.grid_overlay.grid_size + delta))
        self.grid_overlay.grid_size = new_size
