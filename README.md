# BluetoothApp

A Python + Kivy Android app for Bluetooth calling and messaging.

## Features
- Scan & pair nearby Bluetooth devices
- Voice calls over RFCOMM
- Text messaging over Bluetooth

## Project Structure

```
bluetooth-app/
├── src/
│   ├── main.py                  ← Kivy app (run this)
│   └── bluetooth/
│       ├── scanner.py           ← scan & pair devices
│       ├── caller.py            ← voice calls via RFCOMM
│       └── messenger.py         ← send/receive messages
├── .github/workflows/build.yml  ← GitHub Actions APK build
├── buildozer.spec               ← Android packaging config
└── requirements.txt
```

## Quick Start (desktop testing)

```bash
cd bluetooth-app
pip install -r requirements.txt
python src/main.py
```

> On desktop, scan returns mock devices so you can test the UI without hardware.

## Build Android APK locally

```bash
pip install buildozer cython
buildozer android debug
# APK will appear in: bin/
```

## Build via GitHub Actions

1. Push this repo to GitHub
2. Go to **Actions** tab → the workflow triggers automatically on every push to `main`
3. After it completes, download `bluetooth-app-debug.apk` from the **Artifacts** section
4. Transfer the APK to your Android phone and install it (enable "Install unknown apps" in settings)

## Android Permissions Required
- `BLUETOOTH` / `BLUETOOTH_ADMIN` — classic Bluetooth access
- `BLUETOOTH_CONNECT` / `BLUETOOTH_SCAN` — Android 12+ permissions
- `RECORD_AUDIO` — microphone access for calls

## Notes
- Tested on Android 8.0+ (API 21+)
- Voice call audio uses 16kHz mono PCM over RFCOMM
- For BLE devices, replace `pybluez` usage in `scanner.py` with `bleak`
