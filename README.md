# Eldritch Battlemap

Android battlemap maker for Pulp Cthulhu / Call of Cthulhu sessions.
Companion app to **Eldritch Portal**.

## Features (v0.1)

- Two-pane layout: asset browser (left) + canvas (right)
- 5 categories: Floors, Walls, Furniture, Props, Outdoor
- Tap a thumbnail → asset placed at canvas center
- Multitouch drag, pinch-to-scale, two-finger rotate (built-in Kivy `Scatter`)
- Z-order: bring to front / send to back
- Adjustable white grid overlay (toggle + size +/-)
- Auto-save: last session restored on launch
- Save/load named projects
- PNG export of finished battlemap

## On-device folders

```
/sdcard/Documents/EldritchBattlemap/
├── crash.log
├── last_session.json
├── projects/<name>.json
├── exports/<name>_<timestamp>.png
└── imported/<Category>/*.png   ← drop your own images here
```

## Adding assets

**Bundled in the APK** — drop images into `assets/bundled/<Category>/`
before building. Anything that ships in those folders is available offline
forever, no download needed.

**Imported on the device** — copy images into
`/sdcard/Documents/EldritchBattlemap/imported/<Category>/` via a file
manager, then tap **Oppdater** to rescan. PNGs with transparent
backgrounds work best for tokens/props.

## Where to find good public-domain assets

The "free public-domain pictures" idea looks attractive, but Wikimedia /
Met / Smithsonian APIs return historical photos — not top-down game
tokens. Better sources:

- **opengameart.org** (filter to CC0) — top-down tiles and tokens, the
  best single source for this kind of work
- **kenney.nl** — full CC0 asset packs
- **game-icons.net** (CC-BY) — silhouette icons, great for props

## Building

CI: push to `main` → download the APK from the GitHub Actions artifact.

Locally:
```bash
pip install "cython<3.0"
buildozer -v android debug
```

## Architecture

| File | Purpose |
|---|---|
| `main.py` | Entry point, crash logger, Android permissions |
| `battlemap/config.py` | Paths, categories, defaults |
| `battlemap/app.py` | Root layout, dialogs, auto-save loop |
| `battlemap/canvas_area.py` | Build area: assets layer + grid layer |
| `battlemap/placed_asset.py` | `Scatter` + `Image` (drag/scale/rotate) |
| `battlemap/grid_overlay.py` | Adjustable grid (only canvas-drawing widget) |
| `battlemap/asset_panel.py` | Left thumbnail browser |
| `battlemap/toolbar.py` | Top action buttons |
| `battlemap/asset_library.py` | Scans bundled + imported folders |
| `battlemap/project_manager.py` | JSON save/load + auto-save |
| `battlemap/exporter.py` | PNG export (`Widget.export_to_png`) |

## Architectural notes (matches Eldritch Portal conventions)

- **No custom canvas operations on placed assets.** Each asset is a
  `Scatter` containing an `Image` — multitouch is native, no
  `canvas.before` / `canvas.clear` gymnastics.
- **Grid overlay is the only canvas-drawing widget.** Static `Line`
  instructions, redrawn only when grid size / visibility / size change.
  Touches pass through to the assets layer below.
- **Asset thumbnails use `ButtonBehavior` + `Image`** (not `Button`-wrapped
  Images), so they play nicely with `ScrollView` taps vs scrolls.
- **Z-order via `FloatLayout` child reordering** — `add_widget` to index 0
  for front, `len(children)` for back.

## Roadmap

- [ ] Long-press an asset to open a per-asset menu (delete, lock, mirror)
- [ ] Asset-aspect snap to grid
- [ ] Background floor texture (tiled)
- [ ] Fog of war / reveal mask
- [ ] Initiative/token labels on placed assets
- [ ] Higher-resolution PNG export via off-screen FBO
- [ ] Cast battlemap to Chromecast (reuse Eldritch Portal's `pychromecast` setup)
