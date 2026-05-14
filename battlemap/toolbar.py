"""Top toolbar with action buttons.

Most entries are regular Buttons fired on release. Entries with a
trailing `True` are ToggleButtons whose handler receives the new on/off
state.
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp


# (label, action_id) for buttons; (label, action_id, True) for toggle buttons
ACTIONS = [
    ('Grid',      'toggle_grid'),
    ('Grid -',    'grid_smaller'),
    ('Grid +',    'grid_bigger'),
    ('Snap',      'toggle_snap',  True),
    ('Measure',   'measure',      True),
    ('Front',     'bring_front'),
    ('Back',      'send_back'),
    ('Delete',    'delete'),
    ('Undo',      'undo'),
    ('Redo',      'redo'),
    ('No Floor',  'clear_floor'),
    ('Load',      'load'),
    ('Save',      'save'),
    ('New',       'new'),
    ('Refresh',   'refresh'),
    ('Export',    'export'),
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
        self.buttons = {}
        
        for action_def in ACTIONS:
            if len(action_def) == 3 and action_def[2]:
                # ToggleButton — handler gets bool state
                label, action, _ = action_def
                btn = ToggleButton(text=label, font_size=dp(12))
                btn.bind(state=lambda b, s, a=action:
                         self.on_action(a, s == 'down'))
            else:
                label, action = action_def[0], action_def[1]
                btn = Button(text=label, font_size=dp(12))
                btn.bind(on_release=lambda b, a=action: self.on_action(a))
            
            self.buttons[action] = btn
            self.add_widget(btn)

    def set_button_enabled(self, action, enabled):
        """Enable or disable a button."""
        if action in self.buttons:
            self.buttons[action].disabled = not enabled
