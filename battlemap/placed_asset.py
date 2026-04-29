"""A draggable, scalable, rotatable image on the battlemap.

Uses Kivy's built-in Scatter — multitouch drag, pinch-scale, two-finger
rotate are handled natively.

v0.2 additions:
  - selected: BooleanProperty drives a yellow outline drawn in canvas.after
  - long-press detection (~600ms hold without moving) fires _on_longpress
  - any touch-down fires _on_select so the parent can mark this asset selected
"""
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.properties import StringProperty, BooleanProperty
from kivy.graphics import Color, Line
from kivy.clock import Clock

LONGPRESS_SECONDS = 0.6
LONGPRESS_MOVE_TOLERANCE_SQ = 12 * 12  # ~12dp of slop before we cancel


class PlacedAsset(Scatter):
    source = StringProperty('')
    selected = BooleanProperty(False)

    def __init__(self, source, base_size=128, on_select=None, on_longpress=None, **kwargs):
        super().__init__(**kwargs)
        self.do_translation = True
        self.do_rotation = True
        self.do_scale = True
        self.scale_min = 0.1
        self.scale_max = 10.0
        self.size_hint = (None, None)
        self.source = source

        # Callbacks (set by CanvasArea / App)
        self._on_select = on_select
        self._on_longpress = on_longpress

        # Match the Scatter frame to the image's natural aspect ratio so
        # touch targets line up with the visible pixels.
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

        # Selection outline — drawn in canvas.after so it sits on top of
        # the image. Alpha is toggled by `selected`.
        with self.canvas.after:
            self._sel_color = Color(1.0, 0.85, 0.2, 0.0)  # warm yellow
            self._sel_line = Line(rectangle=(0, 0, self.width, self.height), width=1.5)
        self.bind(
            selected=self._update_selection_alpha,
            size=self._update_selection_rect,
        )

    # ---- Aspect detection ----
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

    # ---- Selection visual ----
    def _update_selection_alpha(self, *_):
        self._sel_color.a = 1.0 if self.selected else 0.0

    def _update_selection_rect(self, *_):
        self._sel_line.rectangle = (0, 0, self.width, self.height)

    # ---- Touch handling: select + long-press ----
    def on_touch_down(self, touch):
        handled = super().on_touch_down(touch)
        if handled:
            # Notify parent that this asset was touched (for selection)
            if self._on_select:
                self._on_select(self)
            # Schedule a long-press only on the FIRST finger of this asset
            # (so two-finger rotate/scale doesn't trigger the menu).
            if len(self._touches) == 1:
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
        return super().on_touch_up(touch)

    def _fire_longpress(self):
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
    def from_dict(cls, d, on_select=None, on_longpress=None):
        a = cls(
            source=d['source'],
            base_size=int(d['size'][0]),
            on_select=on_select,
            on_longpress=on_longpress,
        )
        a.size = (float(d['size'][0]), float(d['size'][1]))
        a.pos = (float(d['pos'][0]), float(d['pos'][1]))
        a.scale = float(d.get('scale', 1.0))
        a.rotation = float(d.get('rotation', 0.0))
        return a
