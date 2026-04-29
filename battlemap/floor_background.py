"""Tiled floor background.

Renders a single texture tiled across the canvas, drawn beneath all
placed assets. Tile size is bound to the grid size by CanvasArea, so
each grid cell visually corresponds to one tile.
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.properties import StringProperty, NumericProperty


class FloorBackground(Widget):
    source = StringProperty('')
    tile_size = NumericProperty(64.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._color = Color(1, 1, 1, 0)  # invisible until source is set
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            tile_size=self._redraw,
        )

    def set_floor(self, source):
        if not source:
            self.clear_floor()
            return False
        try:
            tex = CoreImage(source).texture
            if tex is None:
                return False
            tex.wrap = 'repeat'
            self._rect.texture = tex
            self.source = source
            self._color.a = 1.0
            self._redraw()
            return True
        except Exception:
            self.clear_floor()
            return False

    def clear_floor(self):
        self.source = ''
        self._rect.texture = None
        self._color.a = 0.0

    def _redraw(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        if not self.source or self.tile_size <= 0:
            return
        # tex_coords > 1 cause the texture to repeat (because wrap='repeat').
        # nx/ny = how many times the texture tiles across width/height.
        nx = self.width / self.tile_size
        ny = self.height / self.tile_size
        # tex_coords corners: (u1,v1, u2,v2, u3,v3, u4,v4)
        # bottom-left, bottom-right, top-right, top-left
        self._rect.tex_coords = (0, 0, nx, 0, nx, ny, 0, ny)

    def to_dict(self):
        return {
            'source': self.source,
            'tile_size': float(self.tile_size),
        }

    # Touch passthrough — never block placed assets above
    def on_touch_down(self, touch): return False
    def on_touch_move(self, touch): return False
    def on_touch_up(self, touch): return False
