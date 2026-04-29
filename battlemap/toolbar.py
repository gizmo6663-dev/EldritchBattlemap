"""Top toolbar with action buttons."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp


# (label, action_id) — action_id is dispatched to BattlemapApp._on_toolbar_action
ACTIONS = [
    ('Grid',     'toggle_grid'),
    ('Grid -',   'grid_smaller'),
    ('Grid +',   'grid_bigger'),
    ('Front',    'bring_front'),
    ('Back',     'send_back'),
    ('Delete',   'delete'),
    ('Load',     'load'),
    ('Save',     'save'),
    ('New',      'new'),
    ('Refresh',  'refresh'),
    ('Export',      'export'),
]


class Toolbar(BoxLayout):
    def __init__(self, on_action, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            spacing=dp(2),
            **kwargs,
        )
        self.on_action = on_action
        for label, action in ACTIONS:
            btn = Button(text=label, font_size=dp(13))
            btn.bind(on_release=lambda b, a=action: self.on_action(a))
            self.add_widget(btn)
