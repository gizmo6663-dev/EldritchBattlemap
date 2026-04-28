"""A draggable, scalable, rotatable image on the battlemap.

Uses Kivy's built-in Scatter — multitouch drag, pinch-scale, two-finger
rotate are handled natively. No custom canvas operations.
"""
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.properties import StringProperty


class PlacedAsset(Scatter):
    source = StringProperty('')

    def __init__(self, source, base_size=128, **kwargs):
        super().__init__(**kwargs)
        self.do_translation = True
        self.do_rotation = True
        self.do_scale = True
        self.scale_min = 0.1
        self.scale_max = 10.0
        self.size_hint = (None, None)
        self.source = source

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
    def from_dict(cls, d):
        a = cls(source=d['source'], base_size=int(d['size'][0]))
        a.size = (float(d['size'][0]), float(d['size'][1]))
        a.pos = (float(d['pos'][0]), float(d['pos'][1]))
        # Apply scale and rotation last so transform matrix is consistent
        a.scale = float(d.get('scale', 1.0))
        a.rotation = float(d.get('rotation', 0.0))
        return a
