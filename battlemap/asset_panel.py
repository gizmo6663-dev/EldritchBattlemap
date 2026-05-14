"""Left-side asset browser.

Category tabs + thumbnail grid + dynamic hint label.
Tapping a thumbnail in the Floors category sets it as the tiled floor;
tapping in any other category places it as a movable asset.
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp

from battlemap.config import THUMBNAIL_SIZE, CATEGORIES

FLOOR_CATEGORY = 'Floors'


class _ThumbImage(ButtonBehavior, Image):
    """Image with on_release — works inside ScrollView (taps vs scrolls)."""
    pass


class AssetPanel(BoxLayout):
    def __init__(self, library, on_asset_selected, on_floor_selected,
                 on_refresh_request, **kwargs):
        super().__init__(orientation='vertical', size_hint_x=0.30, **kwargs)
        self.library = library
        self.on_asset_selected = on_asset_selected
        self.on_floor_selected = on_floor_selected
        self.on_refresh_request = on_refresh_request
        self._current_category = CATEGORIES[0]

        self.add_widget(Label(
            text='[b]Eldritch Battlemap[/b]',
            markup=True,
            size_hint_y=None,
            height=dp(32),
        ))

        # Category tabs
        tab_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(2),
        )
        self._tabs = {}
        for cat in CATEGORIES:
            tab = ToggleButton(
                text=cat,
                group='category',
                allow_no_selection=False,
                font_size=dp(11),
                state='down' if cat == CATEGORIES[0] else 'normal',
            )
            tab.bind(state=self._on_tab_state)
            self._tabs[cat] = tab
            tab_row.add_widget(tab)
        self.add_widget(tab_row)

        # Hint line
        self._hint = Label(
            text='',
            size_hint_y=None,
            height=dp(22),
            font_size=dp(11),
            color=(0.85, 0.75, 0.55, 1),  # Warm gold/beige
        )
        self.add_widget(self._hint)

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

    def _on_tab_state(self, tab, state):
        if state == 'down':
            self._current_category = tab.text
            self._populate(tab.text)

    def _on_thumb_tap(self, path):
        if self._current_category == FLOOR_CATEGORY:
            self.on_floor_selected(path)
        else:
            self.on_asset_selected(path)

    def _populate(self, category):
        self.thumb_grid.clear_widgets()
        if category == FLOOR_CATEGORY:
            self._hint.text = 'Tap to set as tiled floor'
        else:
            self._hint.text = 'Tap to place'

        items = self.library.assets(category)
        if not items:
            self.thumb_grid.add_widget(Label(
                text=(f'No assets in\n{category}\n\n'
                      f'Drop images into\n/sdcard/Documents/\n'
                      f'EldritchBattlemap/\nimported/{category}/\n\n'
                      f'Then tap Refresh.'),
                halign='center',
                size_hint_y=None,
                height=dp(200),
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
            thumb.bind(on_release=lambda w, p=path: self._on_thumb_tap(p))
            self.thumb_grid.add_widget(thumb)

    def reload(self):
        self.library.refresh()
        self._populate(self._current_category)
