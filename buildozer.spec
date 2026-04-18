[app]

# App metadata
title = BluetoothApp
package.name = bluetoothapp
package.domain = com.example

source.dir = src
source.include_exts = py,png,jpg,kv,atlas

version = 1.0.0

# Kivy entry point
entrypoint = main

# Python requirements (comma-separated)
requirements = python3,kivy==2.3.0,pybluez,pyaudio

# Orientation
orientation = portrait

# Android settings
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Permissions needed for Bluetooth
android.permissions = \
    BLUETOOTH, \
    BLUETOOTH_ADMIN, \
    BLUETOOTH_CONNECT, \
    BLUETOOTH_SCAN, \
    RECORD_AUDIO, \
    INTERNET

# Android features
android.features = android.hardware.bluetooth

# Icon (place a 512x512 icon.png in assets/ folder)
# icon.filename = %(source.dir)s/../assets/icon.png

# Splash screen (optional)
# presplash.filename = %(source.dir)s/../assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
