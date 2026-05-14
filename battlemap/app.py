"""Eldritch Battlemap root app with full feature set.

v0.4 features:
  - Asset labels for HP/names
  - Measurement tool for distance
  - Undo/Redo functionality
  - Asset duplication and rotation
  - Brown/gold themed UI
"""
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.metrics import dp

from battlemap.config import GRID_STEP, ensure_dirs
from battlemap.canvas_area import CanvasArea
from battlemap.asset_library import AssetLibrary
from battlemap.asset_panel import AssetPanel
from battlemap.toolbar import Toolbar
from battlemap.project_manager import ProjectManager
from battlemap.exporter import export_canvas_to_png
from battlemap.command_history import (
    CommandHistory, AddAssetCommand, RemoveAssetCommand,
    RotateAssetCommand, SetLabelCommand
)


# Brown/gold theme colors
BG_COLOR = (0.12, 0.10, 0.08, 1)
GOLD_COLOR = (0.85, 0.75, 0.55, 1)
BUTTON_BG = (0.20, 0.17, 0.13, 1)
BUTTON_BORDER = (0.7, 0.6, 0.4, 1)


class BattlemapApp(App):
    title = 'Eldritch Battlemap'

    def build(self):
        ensure_dirs()
        Window.clearcolor = BG_COLOR

        self.library = AssetLibrary()
        self.project_manager = ProjectManager()
        self.command_history = CommandHistory()

        root = BoxLayout(orientation='horizontal')

        self.asset_panel = AssetPanel(
            library=self.library,
            on_asset_selected=self._on_asset_selected,
            on_floor_selected=self._on_floor_selected,
            on_refresh_request=self._refresh_library,
        )
        root.add_widget(self.asset_panel)

        right = BoxLayout(orientation='vertical')
        self.toolbar = Toolbar(on_action=self._on_toolbar_action)
        right.add_widget(self.toolbar)

        self.canvas_area = CanvasArea(on_asset_longpress=self._show_asset_menu)
        right.add_widget(self.canvas_area)

        root.add_widget(right)

        # Restore last session
        Clock.schedule_once(
            lambda dt: self.project_manager.load_last_session(self.canvas_area),
            0.3,
        )
        # Auto-save tick
        Clock.schedule_interval(
            lambda dt: self.project_manager.save_last_session(self.canvas_area),
            3.0,
        )

        # Update undo/redo button states
        Clock.schedule_interval(lambda dt: self._update_undo_redo_buttons(), 0.5)

        return root

    # ---------- Asset / floor placement ----------
    def _on_asset_selected(self, source):
        asset = self.canvas_area.add_asset(source)
        cmd = AddAssetCommand(self.canvas_area, asset)
        self.command_history.execute(cmd)

    def _on_floor_selected(self, source):
        self.canvas_area.set_floor(source)

    def _refresh_library(self):
        self.asset_panel.reload()

    # ---------- Toolbar dispatch ----------
    def _on_toolbar_action(self, action, value=None):
        ca = self.canvas_area
        if action == 'toggle_grid':
            ca.toggle_grid()
        elif action == 'grid_bigger':
            ca.adjust_grid(GRID_STEP)
        elif action == 'grid_smaller':
            ca.adjust_grid(-GRID_STEP)
        elif action == 'toggle_snap':
            ca.set_snap_enabled(bool(value))
        elif action == 'measure':
            ca.toggle_measurement()
        elif action == 'clear_floor':
            ca.clear_floor()
        elif action == 'bring_front':
            sel = ca.selected_asset()
            if sel:
                ca.bring_to_front(sel)
        elif action == 'send_back':
            sel = ca.selected_asset()
            if sel:
                ca.send_to_back(sel)
        elif action == 'delete':
            sel = ca.selected_asset()
            if sel:
                cmd = RemoveAssetCommand(ca, sel)
                self.command_history.execute(cmd)
        elif action == 'undo':
            self.command_history.undo()
        elif action == 'redo':
            self.command_history.redo()
        elif action == 'save':
            self._show_save_dialog()
        elif action == 'load':
            self._show_load_dialog()
        elif action == 'new':
            self._show_new_dialog()
        elif action == 'refresh':
            self._refresh_library()
        elif action == 'export':
            self._do_export()

    def _update_undo_redo_buttons(self):
        """Update undo/redo button enabled states."""
        self.toolbar.set_button_enabled('undo', self.command_history.can_undo())
        self.toolbar.set_button_enabled('redo', self.command_history.can_redo())

    # ---------- Lifecycle ----------
    def on_pause(self):
        self.project_manager.save_last_session(self.canvas_area)
        return True

    def on_stop(self):
        self.project_manager.save_last_session(self.canvas_area)

    # ---------- Styled button helper ----------
    def _styled_button(self, text, **kwargs):
        """Create a button with brown/gold theme."""
        return Button(
            text=text,
            background_color=BUTTON_BG,
            color=GOLD_COLOR,
            **kwargs
        )

    # ---------- Per-asset long-press menu ----------
    def _show_asset_menu(self, asset):
        ca = self.canvas_area
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        popup = Popup(
            title='Asset',
            content=content,
            size_hint=(None, None),
            size=(dp(280), dp(420)),  # Increased for label button
            separator_color=BUTTON_BORDER,
            title_color=GOLD_COLOR,
        )

        def _wrap(fn):
            def handler(*_):
                fn()
                popup.dismiss()
            return handler

        for label, fn in [
            ('Set Label',      lambda: self._show_label_dialog(asset)),
            ('Bring to Front', lambda: ca.bring_to_front(asset)),
            ('Send to Back',   lambda: ca.send_to_back(asset)),
            ('Rotate 90° CW',  lambda: self._rotate_asset(asset, 90)),
            ('Rotate 90° CCW', lambda: self._rotate_asset(asset, -90)),
            ('Duplicate',      lambda: self._duplicate_asset(asset)),
            ('Delete',         lambda: self._delete_asset_with_command(asset)),
        ]:
            btn = self._styled_button(label, size_hint_y=None, height=dp(44))
            btn.bind(on_release=_wrap(fn))
            content.add_widget(btn)

        cancel = self._styled_button('Cancel', size_hint_y=None, height=dp(44))
        cancel.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(cancel)

        popup.open()

    def _show_label_dialog(self, asset):
        """Show dialog to edit asset label."""
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        content.add_widget(Label(
            text='Label (HP, name, etc.):',
            size_hint_y=None,
            height=dp(28),
            color=GOLD_COLOR
        ))
        ti = TextInput(
            text=asset.label_text,
            multiline=False,
            size_hint_y=None,
            height=dp(44),
            background_color=BUTTON_BG,
            foreground_color=GOLD_COLOR,
        )
        content.add_widget(ti)
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
        ok = self._styled_button('OK')
        clear = self._styled_button('Clear')
        cancel = self._styled_button('Cancel')
        btns.add_widget(ok)
        btns.add_widget(clear)
        btns.add_widget(cancel)
        content.add_widget(btns)
        
        popup = Popup(
            title='Set Label',
            content=content,
            size_hint=(None, None),
            size=(dp(360), dp(220)),
            separator_color=BUTTON_BORDER,
            title_color=GOLD_COLOR,
        )

        def _do_set(*_):
            new_label = ti.text.strip()
            cmd = SetLabelCommand(asset, asset.label_text, new_label)
            self.command_history.execute(cmd)
            popup.dismiss()

        def _do_clear(*_):
            cmd = SetLabelCommand(asset, asset.label_text, '')
            self.command_history.execute(cmd)
            popup.dismiss()

        ok.bind(on_release=_do_set)
        clear.bind(on_release=_do_clear)
        cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _rotate_asset(self, asset, degrees):
        """Rotate asset with undo support."""
        old_rotation = asset.rotation
        new_rotation = (old_rotation + degrees) % 360
        cmd = RotateAssetCommand(asset, old_rotation, new_rotation)
        self.command_history.execute(cmd)

    def _duplicate_asset(self, asset):
        """Create a duplicate of the asset."""
        ca = self.canvas_area
        offset = 32
        new_asset = ca.add_asset(
            asset.source,
            center=(asset.center_x + offset, asset.center_y + offset)
        )
        new_asset.scale = asset.scale
        new_asset.rotation = asset.rotation
        new_asset.label_text = asset.label_text
        cmd = AddAssetCommand(ca, new_asset)
        self.command_history.execute(cmd)

    def _delete_asset_with_command(self, asset):
        """Delete asset with undo support."""
        cmd = RemoveAssetCommand(self.canvas_area, asset)
        self.command_history.execute(cmd)

    # ---------- Project dialogs ----------
    def _show_save_dialog(self):
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        content.add_widget(Label(
            text='Project name:',
            size_hint_y=None,
            height=dp(28),
            color=GOLD_COLOR
        ))
        ti = TextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(44),
            background_color=BUTTON_BG,
            foreground_color=GOLD_COLOR,
        )
        content.add_widget(ti)
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
        ok = self._styled_button('Save')
        cancel = self._styled_button('Cancel')
        btns.add_widget(ok)
        btns.add_widget(cancel)
        content.add_widget(btns)
        popup = Popup(
            title='Save project',
            content=content,
            size_hint=(None, None),
            size=(dp(360), dp(220)),
            separator_color=BUTTON_BORDER,
            title_color=GOLD_COLOR,
        )

        def _do_save(*_):
            name = ti.text.strip()
            if name:
                self.project_manager.save_project(self.canvas_area, name)
                popup.dismiss()

        ok.bind(on_release=_do_save)
        cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _show_load_dialog(self):
        names = self.project_manager.list_projects()
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        popup = Popup(
            title='Load project',
            content=content,
            size_hint=(None, None),
            size=(dp(360), dp(360)),
            separator_color=BUTTON_BORDER,
            title_color=GOLD_COLOR,
        )

        if not names:
            content.add_widget(Label(
                text='No saved projects yet.',
                color=GOLD_COLOR
            ))
        else:
            scroll = ScrollView()
            grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
            grid.bind(minimum_height=grid.setter('height'))
            for n in names:
                b = self._styled_button(n, size_hint_y=None, height=dp(44))
                def _make_loader(name):
                    def _load(*_):
                        self.project_manager.load_project(self.canvas_area, name)
                        self.command_history.clear()  # Clear undo history on load
                        popup.dismiss()
                    return _load
                b.bind(on_release=_make_loader(n))
                grid.add_widget(b)
            scroll.add_widget(grid)
            content.add_widget(scroll)

        close = self._styled_button('Close', size_hint_y=None, height=dp(44))
        close.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(close)
        popup.open()

    def _show_new_dialog(self):
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        content.add_widget(Label(
            text='Clear current battlemap?\nUnsaved changes will be lost.',
            color=GOLD_COLOR
        ))
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
        ok = self._styled_button('Yes')
        no = self._styled_button('Cancel')
        btns.add_widget(ok)
        btns.add_widget(no)
        content.add_widget(btns)
        popup = Popup(
            title='New battlemap',
            content=content,
            size_hint=(None, None),
            size=(dp(360), dp(200)),
            separator_color=BUTTON_BORDER,
            title_color=GOLD_COLOR,
        )
        
        def _do_new(*_):
            self.canvas_area.clear_assets()
            self.command_history.clear()
            popup.dismiss()
        
        ok.bind(on_release=_do_new)
        no.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _do_export(self):
        path = export_canvas_to_png(self.canvas_area, name='battlemap')
        msg = f'Exported to:\n{path}' if path else 'Export failed.\nCheck crash.log.'
        Popup(
            title='Export PNG',
            content=Label(text=msg, color=GOLD_COLOR),
            size_hint=(None, None),
            size=(dp(360), dp(180)),
            separator_color=BUTTON_BORDER,
            title_color=GOLD_COLOR,
        ).open()
