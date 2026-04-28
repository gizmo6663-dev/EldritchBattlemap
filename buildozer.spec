[app]
title = Eldritch Battlemap
package.name = eldritchbattlemap
package.domain = no.gizmo.eldritchbattlemap

source.dir = .
source.include_exts = py,png,jpg,jpeg,webp,kv,atlas,json
source.include_patterns = assets/bundled/*/*

version = 0.1.0

requirements = python3,kivy==2.3.0,pillow,pyjnius,android

orientation = landscape
fullscreen = 0

# Storage access for /sdcard/Documents/EldritchBattlemap/
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.accept_sdk_license = True
android.api = 33
android.minapi = 24
android.build_tools_version = 33.0.2
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
