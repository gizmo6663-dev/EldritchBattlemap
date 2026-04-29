"""Eldritch Battlemap root app."""
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


class BattlemapApp(App):
    title = 'Eldritch Battlemap'

    def build(self):
        ensure_dirs()
        Window.clearcolor = (0.06, 0.06, 0.08, 1)

        self.library = AssetLibrary()
        self.project_manager = ProjectManager()

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

        # Restore last session a moment after layout settles
        Clock.schedule_once(
            lambda dt: self.project_manager.load_last_session(self.canvas_area),
            0.3,
        )
        # Auto-save tick
        Clock.schedule_interval(
            lambda dt: self.project_manager.save_last_session(self.canvas_area),
            3.0,
        )

        return root

    # ---------- Asset / floor placement ----------
    def _on_asset_selected(self, source):
        self.canvas_area.add_asset(source)

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
                ca.remove_asset(sel)
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

    # ---------- Lifecycle ----------
    def on_pause(self):
        self.project_manager.save_last_session(self.canvas_area)
        return True

    def on_stop(self):
        self.project_manager.save_last_session(self.canvas_area)

    # ---------- Per-asset long-press menu ----------
    def _show_asset_menu(self, asset):
        ca = self.canvas_area
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        # Fixed dp size — works correctly in landscape where size_hint
        # percentages don't give enough vertical room for 4 buttons.
        popup = Popup(
            title='Asset',
            content=content,
            size_hint=(None, None),
            size=(dp(280), dp(290)),
        )

        def _wrap(fn):
            def handler(*_):
                fn()
                popup.dismiss()
            return handler

        for label, fn in [
            ('Bring to Front', lambda: ca.bring_to_front(asset)),
            ('Send to Back',   lambda: ca.send_to_back(asset)),
            ('Delete',         lambda: ca.remove_asset(asset)),
        ]:
            btn = Button(text=label, size_hint_y=None, height=dp(44))
            btn.bind(on_release=_wrap(fn))
            content.add_widget(btn)

        cancel = Button(text='Cancel', size_hint_y=None, height=dp(44))
        cancel.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(cancel)

        popup.open()

    # ---------- Project dialogs ----------
    def _show_save_dialog(self):
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        content.add_widget(Label(text='Project name:', size_hint_y=None, height=dp(28)))
        ti = TextInput(text='', multiline=False, size_hint_y=None, height=dp(44))
        content.add_widget(ti)
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
        ok = Button(text='Save')
        cancel = Button(text='Cancel')
        btns.add_widget(ok); btns.add_widget(cancel)
        content.add_widget(btns)
        popup = Popup(
            title='Save project', content=content,
            size_hint=(None, None), size=(dp(360), dp(220)),
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
            title='Load project', content=content,
            size_hint=(None, None), size=(dp(360), dp(360)),
        )

        if not names:
            content.add_widget(Label(text='No saved projects yet.'))
        else:
            scroll = ScrollView()
            grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
            grid.bind(minimum_height=grid.setter('height'))
            for n in names:
                b = Button(text=n, size_hint_y=None, height=dp(44))
                def _make_loader(name):
                    def _load(*_):
                        self.project_manager.load_project(self.canvas_area, name)
                        popup.dismiss()
                    return _load
                b.bind(on_release=_make_loader(n))
                grid.add_widget(b)
            scroll.add_widget(grid)
            content.add_widget(scroll)

        close = Button(text='Close', size_hint_y=None, height=dp(44))
        close.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(close)
        popup.open()

    def _show_new_dialog(self):
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        content.add_widget(Label(text='Clear current battlemap?\nUnsaved changes will be lost.'))
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
        ok = Button(text='Yes')
        no = Button(text='Cancel')
        btns.add_widget(ok); btns.add_widget(no)
        content.add_widget(btns)
        popup = Popup(
            title='New battlemap', content=content,
            size_hint=(None, None), size=(dp(360), dp(200)),
        )
        ok.bind(on_release=lambda *_: (self.canvas_area.clear_assets(), popup.dismiss()))
        no.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _do_export(self):
        path = export_canvas_to_png(self.canvas_area, name='battlemap')
        msg = f'Exported to:\n{path}' if path else 'Export failed.\nCheck crash.log.'
        Popup(
            title='Export PNG', content=Label(text=msg),
            size_hint=(None, None), size=(dp(360), dp(180)),
        ).open()
