"""Left-side asset browser.

Category dropdown + scrollable thumbnail grid. Thumbnails are raw Image
widgets with ButtonBehavior mixed in — no Button widget wrapping (matches
Eldritch Portal's image-handling architecture).
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp

from battlemap.config import THUMBNAIL_SIZE, CATEGORIES


class _ThumbImage(ButtonBehavior, Image):
    """Image with on_release — works inside ScrollView (taps vs scrolls)."""
    pass


class AssetPanel(BoxLayout):
    def __init__(self, library, on_asset_selected, on_refresh_request, **kwargs):
        super().__init__(orientation='vertical', size_hint_x=0.30, **kwargs)
        self.library = library
        self.on_asset_selected = on_asset_selected
        self.on_refresh_request = on_refresh_request

        self.add_widget(Label(
            text='[b]Eldritch Battlemap[/b]',
            markup=True,
            size_hint_y=None,
            height=dp(36),
        ))

        self.category_spinner = Spinner(
            text=CATEGORIES[0],
            values=CATEGORIES,
            size_hint_y=None,
            height=dp(44),
        )
        self.category_spinner.bind(text=lambda spinner, val: self._populate(val))
        self.add_widget(self.category_spinner)

        # Refresh button (re-scans imported folder for new files)
        refresh = _ThumbImage(  # repurposed — a tappable label-style row
            source='',
            size_hint_y=None,
            height=dp(0),  # invisible placeholder; refresh happens via toolbar action
        )

        scroll = ScrollView(size_hint=(1, 1))
        self.thumb_grid = GridLayout(
            cols=2,
            spacing=dp(4),
            padding=dp(4),
            size_hint_y=None,
        )
        self.thumb_grid.bind(minimum_height=self.thumb_grid.setter('height'))
        scroll.add_widget(self.thumb_grid)
        self.add_widget(scroll)

        self._populate(CATEGORIES[0])

    def _populate(self, category):
        self.thumb_grid.clear_widgets()
        items = self.library.assets(category)
        if not items:
            self.thumb_grid.add_widget(Label(
                text=f'No assets in\n{category}\n\nDrop images into\n/sdcard/Documents/\nEldritchBattlemap/\nimported/{category}/',
                halign='center',
                size_hint_y=None,
                height=dp(180),
                font_size=dp(11),
            ))
            return
        for path in items:
            thumb = _ThumbImage(
                source=path,
                size_hint_y=None,
                height=dp(THUMBNAIL_SIZE),
                allow_stretch=True,
                keep_ratio=True,
                mipmap=True,
            )
            thumb.bind(on_release=lambda w, p=path: self.on_asset_selected(p))
            self.thumb_grid.add_widget(thumb)

    def reload(self):
        self.library.refresh()
        self._populate(self.category_spinner.text)
