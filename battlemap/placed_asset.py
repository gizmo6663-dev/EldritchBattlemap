"""A draggable, scalable, rotatable image on the battlemap.

v0.3:
  - Selection highlight is now a child Widget (not canvas.after) so it
    correctly inherits the Scatter's transform. Children of Scatter are
    drawn through the transformation matrix automatically.
  - on_drag_end callback fires when the last finger is released, used by
    CanvasArea for snap-to-grid.
"""
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock

LONGPRESS_SECONDS = 0.6
LONGPRESS_MOVE_TOLERANCE_SQ = 12 * 12  # ~12dp of slop before we cancel


class _SelectionHighlight(Widget):
    """Yellow outline.

    Added as a child of PlacedAsset (which is a Scatter), so it inherits
    the parent's transform — translation, rotation, and scale all apply
    automatically. Touches pass through.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._color = Color(1.0, 0.85, 0.2, 0.0)
            self._line = Line(rectangle=(0, 0, 1, 1), width=1.5)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *_):
        self._line.rectangle = (self.x, self.y, self.width, self.height)

    def set_visible(self, visible):
        self._color.a = 1.0 if visible else 0.0

    # Touch passthrough — never block the asset's drag/scale/rotate
    def on_touch_down(self, touch): return False
    def on_touch_move(self, touch): return False
    def on_touch_up(self, touch): return False


class PlacedAsset(Scatter):
    source = StringProperty('')
    selected = BooleanProperty(False)

    def __init__(self, source, base_size=128,
                 on_select=None, on_longpress=None, on_drag_end=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.do_translation = True
        self.do_rotation = True
        self.do_scale = True
        self.scale_min = 0.1
        self.scale_max = 10.0
        self.size_hint = (None, None)
        self.source = source

        self._on_select = on_select
        self._on_longpress = on_longpress
        self._on_drag_end = on_drag_end
        self._longpress_fired = False

        w, h = self._detect_aspect(source, base_size)
        self.size = (w, h)

        self.image = Image(
            source=source,
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
            mipmap=True,
        )
        self.add_widget(self.image)

        # Highlight is a child widget — it inherits Scatter's transform,
        # so it follows the asset through translation, rotation, and scale.
        self._highlight = _SelectionHighlight(size_hint=(1, 1))
        self.add_widget(self._highlight)

        self.bind(selected=self._update_selection_visual)

    @staticmethod
    def _detect_aspect(source, base_size):
        try:
            from kivy.core.image import Image as CoreImage
            ci = CoreImage(source)
            iw, ih = ci.size
            if iw > 0 and ih > 0:
                if iw >= ih:
                    return (float(base_size), base_size * (ih / iw))
                return (base_size * (iw / ih), float(base_size))
        except Exception:
            pass
        return (float(base_size), float(base_size))

    def _update_selection_visual(self, *_):
        self._highlight.set_visible(self.selected)

    # ---- Touch handling ----
    def on_touch_down(self, touch):
        handled = super().on_touch_down(touch)
        if handled:
            if self._on_select:
                self._on_select(self)
            if len(self._touches) == 1:
                self._longpress_fired = False
                touch.ud['_lp_start'] = touch.pos
                touch.ud['_lp_event'] = Clock.schedule_once(
                    lambda dt: self._fire_longpress(), LONGPRESS_SECONDS
                )
        return handled

    def on_touch_move(self, touch):
        ev = touch.ud.get('_lp_event')
        if ev is not None:
            sp = touch.ud.get('_lp_start')
            if sp:
                dx = touch.x - sp[0]
                dy = touch.y - sp[1]
                if (dx * dx + dy * dy) > LONGPRESS_MOVE_TOLERANCE_SQ:
                    ev.cancel()
                    touch.ud['_lp_event'] = None
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        ev = touch.ud.get('_lp_event')
        if ev is not None:
            ev.cancel()
            touch.ud['_lp_event'] = None

        had_touches = bool(self._touches)
        result = super().on_touch_up(touch)

        # Last finger released → fire drag_end (unless a long-press already fired)
        if had_touches and not self._touches:
            if not self._longpress_fired and self._on_drag_end:
                self._on_drag_end(self)
            self._longpress_fired = False
        return result

    def _fire_longpress(self):
        self._longpress_fired = True
        if self._on_longpress:
            self._on_longpress(self)

    # ---- Serialization ----
    def to_dict(self):
        return {
            'source': self.source,
            'pos': [float(self.x), float(self.y)],
            'size': [float(self.width), float(self.height)],
            'scale': float(self.scale),
            'rotation': float(self.rotation),
        }

    @classmethod
    def from_dict(cls, d, on_select=None, on_longpress=None, on_drag_end=None):
        a = cls(
            source=d['source'],
            base_size=int(d['size'][0]),
            on_select=on_select,
            on_longpress=on_longpress,
            on_drag_end=on_drag_end,
        )
        a.size = (float(d['size'][0]), float(d['size'][1]))
        a.pos = (float(d['pos'][0]), float(d['pos'][1]))
        a.scale = float(d.get('scale', 1.0))
        a.rotation = float(d.get('rotation', 0.0))
        return a
