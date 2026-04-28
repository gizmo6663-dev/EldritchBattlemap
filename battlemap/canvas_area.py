"""The battlemap build area.

Two stacked layers:
  - assets_layer (FloatLayout)  → placed PlacedAsset (Scatter) widgets
  - grid_overlay (GridOverlay)  → drawn on top, touch-passthrough

Z-ordering helpers reorder children of assets_layer only.
PNG export captures both layers via Widget.export_to_png().
"""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from battlemap.grid_overlay import GridOverlay
from battlemap.placed_asset import PlacedAsset
from battlemap.config import (
    DEFAULT_GRID_SIZE, DEFAULT_ASSET_SIZE, MIN_GRID_SIZE, MAX_GRID_SIZE,
)


class CanvasArea(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        asset = PlacedAsset(source=source, base_size=DEFAULT_ASSET_SIZE)
        if center is None:
            center = (self.width / 2, self.height / 2)
        asset.center = center
        self.assets_layer.add_widget(asset)
        return asset

    def remove_asset(self, asset):
        if asset in self.assets_layer.children:
            self.assets_layer.remove_widget(asset)

    def clear_assets(self):
        for child in list(self.assets_layer.children):
            self.assets_layer.remove_widget(child)

    def all_assets(self):
        # children[0] is on top; reverse so the iterator goes bottom → top
        # (matches paint order, which is what we want for save/restore).
        return list(reversed(self.assets_layer.children))

    # ----- Z-order -----
    def bring_to_front(self, asset):
        if asset in self.assets_layer.children:
            self.assets_layer.remove_widget(asset)
            self.assets_layer.add_widget(asset)  # default index 0 → top

    def send_to_back(self, asset):
        if asset in self.assets_layer.children:
            self.assets_layer.remove_widget(asset)
            self.assets_layer.add_widget(asset, index=len(self.assets_layer.children))

    # ----- Selection (most recently touched Scatter rises to children[0]) -----
    def selected_asset(self):
        if self.assets_layer.children:
            return self.assets_layer.children[0]
        return None

    # ----- Grid -----
    def toggle_grid(self):
        self.grid_overlay.visible = not self.grid_overlay.visible

    def adjust_grid(self, delta):
        new_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, self.grid_overlay.grid_size + delta))
        self.grid_overlay.grid_size = new_size
