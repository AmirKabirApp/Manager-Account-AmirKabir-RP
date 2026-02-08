[app]
title = AmirKabir Manager
package.name = amirkabir_manager
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# این همون آیکون خوشگلته که فرستادی
icon.filename = icon.png

orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# --- بخش جادویی لایسنس (تیر آخر) ---
android.accept_sdk_license = True
android.skip_update = False
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
