"""Adjustable sepia grid overlay.

This is the only widget in the app that uses canvas instructions —
parametric grid lines can't be done any other way. Lines are static
(no .before/.after gymnastics), and touches pass through to layers below.
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty, BooleanProperty, ListProperty


class GridOverlay(Widget):
    grid_size = NumericProperty(64.0)
    visible = BooleanProperty(True)
    line_color = ListProperty([0.7, 0.6, 0.4, 0.5])  # Sepia/brown-gold
    line_width = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            grid_size=self._redraw,
            visible=self._redraw,
            line_color=self._redraw,
            line_width=self._redraw,
        )
        self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()
        if not self.visible or self.grid_size <= 0 or self.width <= 0 or self.height <= 0:
            return
        with self.canvas:
            Color(*self.line_color)
            x0, y0, w, h = self.x, self.y, self.width, self.height
            # vertical lines
            x = x0
            while x <= x0 + w + 0.5:
                Line(points=[x, y0, x, y0 + h], width=self.line_width)
                x += self.grid_size
            # horizontal lines
            y = y0
            while y <= y0 + h + 0.5:
                Line(points=[x0, y, x0 + w, y], width=self.line_width)
                y += self.grid_size

    # Touch passthrough — placed assets below should receive the touch
    def on_touch_down(self, touch):
        return False

    def on_touch_move(self, touch):
        return False

    def on_touch_up(self, touch):
        return False
