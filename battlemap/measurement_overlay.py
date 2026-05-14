"""Measurement overlay for calculating distances on the battlemap.

Touch once to set start point, touch again to set end point and show distance.
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse
from kivy.properties import BooleanProperty, NumericProperty, ListProperty
from kivy.uix.label import Label
from kivy.metrics import dp
import math


class MeasurementOverlay(Widget):
    active = BooleanProperty(False)
    grid_size = NumericProperty(64.0)
    start_point = ListProperty([None, None])
    end_point = ListProperty([None, None])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            active=self._redraw,
            start_point=self._redraw,
            end_point=self._redraw,
        )
        
        # Label for distance display
        self._distance_label = Label(
            text='',
            size_hint=(None, None),
            size=(200, 40),
            color=(1.0, 0.85, 0.3, 1),  # Gold
            font_size='16sp',
            bold=True,
            outline_width=2,
            outline_color=(0, 0, 0),
        )
        self.add_widget(self._distance_label)

    def _redraw(self, *_):
        self.canvas.clear()
        if not self.active:
            self._distance_label.text = ''
            return
            
        sx, sy = self.start_point
        ex, ey = self.end_point
        
        if sx is None or sy is None:
            self._distance_label.text = 'Tap to set start point'
            return
            
        with self.canvas:
            # Draw start point
            Color(1.0, 0.85, 0.3, 0.8)  # Gold
            Ellipse(pos=(sx - dp(8), sy - dp(8)), size=(dp(16), dp(16)))
            
            if ex is not None and ey is not None:
                # Draw end point
                Ellipse(pos=(ex - dp(8), ey - dp(8)), size=(dp(16), dp(16)))
                
                # Draw line
                Line(points=[sx, sy, ex, ey], width=2.0)
                
                # Calculate distance
                dx = ex - sx
                dy = ey - sy
                pixel_distance = math.sqrt(dx * dx + dy * dy)
                grid_distance = pixel_distance / self.grid_size if self.grid_size > 0 else 0
                
                # Position label at midpoint
                mid_x = (sx + ex) / 2
                mid_y = (sy + ey) / 2
                self._distance_label.pos = (mid_x - 100, mid_y + 20)
                self._distance_label.text = f'{grid_distance:.1f} cells'
            else:
                self._distance_label.text = 'Tap to set end point'

    def on_touch_down(self, touch):
        if not self.active:
            return False
            
        sx, sy = self.start_point
        if sx is None or sy is None:
            # Set start point
            self.start_point = [touch.x, touch.y]
            self.end_point = [None, None]
        else:
            # Set end point
            self.end_point = [touch.x, touch.y]
        return True

    def on_touch_move(self, touch):
        if self.active:
            return True
        return False

    def on_touch_up(self, touch):
        if self.active:
            return True
        return False

    def clear(self):
        """Clear measurement points."""
        self.start_point = [None, None]
        self.end_point = [None, None]
