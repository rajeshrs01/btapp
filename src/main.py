"""
BluetoothApp - Main Entry Point
Kivy-based Android app for Bluetooth calls and messaging.
"""

import kivy
kivy.require("2.3.0")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window

import threading
from bluetooth.scanner import scan_devices
from bluetooth.caller import BluetoothCaller
from bluetooth.messenger import BluetoothMessenger

Window.clearcolor = (0.1, 0.1, 0.15, 1)

# ── Shared state ────────────────────────────────────────────
caller = BluetoothCaller()
messenger = BluetoothMessenger()
paired_device = {"addr": None, "name": None}


# ── Screen: Home ─────────────────────────────────────────────
class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=12)

        layout.add_widget(Label(
            text="[b]BluetoothApp[/b]",
            markup=True, font_size="28sp", size_hint_y=None, height=60,
            color=(0.4, 0.8, 1, 1)
        ))

        self.status_lbl = Label(
            text="No device connected", font_size="14sp",
            size_hint_y=None, height=36, color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(self.status_lbl)

        for text, screen in [
            ("🔍  Scan & Pair Devices", "scan"),
            ("📞  Make a Call",          "call"),
            ("💬  Messages",             "messages"),
        ]:
            btn = Button(
                text=text, font_size="17sp",
                size_hint_y=None, height=56,
                background_color=(0.2, 0.5, 0.9, 1),
                background_normal=""
            )
            btn.bind(on_press=lambda e, s=screen: self._go(s))
            layout.add_widget(btn)

        self.add_widget(layout)

    def _go(self, screen):
        self.manager.current = screen

    def on_enter(self):
        addr = paired_device["addr"]
        name = paired_device["name"]
        self.status_lbl.text = f"Connected: {name} ({addr})" if addr else "No device connected"


# ── Screen: Scan ─────────────────────────────────────────────
class ScanScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = BoxLayout(orientation="vertical", padding=16, spacing=10)

        self.layout.add_widget(Label(
            text="Scan for Devices", font_size="22sp",
            size_hint_y=None, height=50, color=(0.4, 0.8, 1, 1)
        ))

        self.scan_btn = Button(
            text="Start Scan", font_size="16sp",
            size_hint_y=None, height=50,
            background_color=(0.2, 0.7, 0.4, 1),
            background_normal=""
        )
        self.scan_btn.bind(on_press=self.start_scan)
        self.layout.add_widget(self.scan_btn)

        self.status = Label(text="", font_size="13sp", size_hint_y=None, height=30,
                            color=(0.9, 0.7, 0.2, 1))
        self.layout.add_widget(self.status)

        scroll = ScrollView()
        self.device_list = BoxLayout(
            orientation="vertical", spacing=6,
            size_hint_y=None, padding=[0, 4]
        )
        self.device_list.bind(minimum_height=self.device_list.setter("height"))
        scroll.add_widget(self.device_list)
        self.layout.add_widget(scroll)

        back = Button(text="← Back", size_hint_y=None, height=44,
                      background_color=(0.3, 0.3, 0.3, 1), background_normal="")
        back.bind(on_press=lambda e: setattr(self.manager, "current", "home"))
        self.layout.add_widget(back)

        self.add_widget(self.layout)

    def start_scan(self, *_):
        self.status.text = "Scanning… (up to 10s)"
        self.scan_btn.disabled = True
        self.device_list.clear_widgets()
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        devices = scan_devices()
        Clock.schedule_once(lambda dt: self._show_devices(devices))

    def _show_devices(self, devices):
        self.scan_btn.disabled = False
        if not devices:
            self.status.text = "No devices found"
            return
        self.status.text = f"Found {len(devices)} device(s)"
        for dev in devices:
            btn = Button(
                text=f"{dev['name']}  |  {dev['addr']}",
                font_size="14sp", size_hint_y=None, height=50,
                background_color=(0.15, 0.35, 0.65, 1),
                background_normal=""
            )
            btn.bind(on_press=lambda e, d=dev: self._pair(d))
            self.device_list.add_widget(btn)

    def _pair(self, dev):
        paired_device["addr"] = dev["addr"]
        paired_device["name"] = dev["name"]
        self.status.text = f"Paired with {dev['name']}"


# ── Screen: Call ─────────────────────────────────────────────
class CallScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=14)

        layout.add_widget(Label(
            text="Bluetooth Call", font_size="22sp",
            size_hint_y=None, height=50, color=(0.4, 0.8, 1, 1)
        ))

        self.device_lbl = Label(text="No device paired", font_size="15sp",
                                size_hint_y=None, height=36, color=(0.75, 0.75, 0.75, 1))
        layout.add_widget(self.device_lbl)

        self.call_status = Label(text="Idle", font_size="17sp",
                                 size_hint_y=None, height=40, color=(0.9, 0.9, 0.9, 1))
        layout.add_widget(self.call_status)

        self.call_btn = Button(
            text="📞  Start Call", font_size="18sp",
            size_hint_y=None, height=60,
            background_color=(0.2, 0.7, 0.35, 1),
            background_normal=""
        )
        self.call_btn.bind(on_press=self.toggle_call)
        layout.add_widget(self.call_btn)

        back = Button(text="← Back", size_hint_y=None, height=44,
                      background_color=(0.3, 0.3, 0.3, 1), background_normal="")
        back.bind(on_press=lambda e: setattr(self.manager, "current", "home"))
        layout.add_widget(back)

        self.add_widget(layout)
        self._in_call = False

    def on_enter(self):
        addr = paired_device["addr"]
        self.device_lbl.text = f"Device: {paired_device['name']} ({addr})" if addr else "No device paired"

    def toggle_call(self, *_):
        if not paired_device["addr"]:
            self._alert("Pair a device first from the Scan screen.")
            return
        if not self._in_call:
            self._in_call = True
            self.call_status.text = "Connecting…"
            self.call_btn.text = "📵  End Call"
            self.call_btn.background_color = (0.85, 0.2, 0.2, 1)
            threading.Thread(target=self._start_call, daemon=True).start()
        else:
            caller.end_call()
            self._in_call = False
            self.call_status.text = "Call ended"
            self.call_btn.text = "📞  Start Call"
            self.call_btn.background_color = (0.2, 0.7, 0.35, 1)

    def _start_call(self):
        ok = caller.start_call(paired_device["addr"])
        Clock.schedule_once(lambda dt: self._on_connected(ok))

    def _on_connected(self, ok):
        if ok:
            self.call_status.text = "In call ●"
        else:
            self._in_call = False
            self.call_status.text = "Connection failed"
            self.call_btn.text = "📞  Start Call"
            self.call_btn.background_color = (0.2, 0.7, 0.35, 1)

    def _alert(self, msg):
        popup = Popup(title="Notice", content=Label(text=msg),
                      size_hint=(0.8, 0.3))
        popup.open()


# ── Screen: Messages ─────────────────────────────────────────
class MessageScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=12, spacing=8)

        layout.add_widget(Label(
            text="Bluetooth Messages", font_size="22sp",
            size_hint_y=None, height=50, color=(0.4, 0.8, 1, 1)
        ))

        # Chat history
        scroll = ScrollView(size_hint=(1, 1))
        self.chat_box = BoxLayout(
            orientation="vertical", spacing=6, padding=[4, 4],
            size_hint_y=None
        )
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        scroll.add_widget(self.chat_box)
        layout.add_widget(scroll)

        # Input row
        input_row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        self.msg_input = TextInput(
            hint_text="Type a message…", multiline=False,
            font_size="15sp", size_hint_x=0.75,
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1)
        )
        send_btn = Button(
            text="Send", font_size="15sp", size_hint_x=0.25,
            background_color=(0.2, 0.5, 0.9, 1),
            background_normal=""
        )
        send_btn.bind(on_press=self.send_message)
        input_row.add_widget(self.msg_input)
        input_row.add_widget(send_btn)
        layout.add_widget(input_row)

        back = Button(text="← Back", size_hint_y=None, height=44,
                      background_color=(0.3, 0.3, 0.3, 1), background_normal="")
        back.bind(on_press=lambda e: setattr(self.manager, "current", "home"))
        layout.add_widget(back)

        self.add_widget(layout)
        self._connected = False

    def on_enter(self):
        if not self._connected and paired_device["addr"]:
            threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        ok = messenger.connect(paired_device["addr"])
        if ok:
            self._connected = True
            Clock.schedule_once(lambda dt: self._add_bubble("System", "Connected!", (0.2, 0.6, 0.3, 1)))
            threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        while self._connected:
            msg = messenger.receive()
            if msg:
                Clock.schedule_once(lambda dt, m=msg: self._add_bubble("Them", m, (0.25, 0.25, 0.35, 1)))

    def send_message(self, *_):
        text = self.msg_input.text.strip()
        if not text:
            return
        if not self._connected:
            self._add_bubble("System", "Not connected. Pair a device first.", (0.7, 0.3, 0.3, 1))
            return
        ok = messenger.send(text)
        if ok:
            self._add_bubble("You", text, (0.15, 0.4, 0.75, 1))
            self.msg_input.text = ""

    def _add_bubble(self, sender, text, color):
        lbl = Label(
            text=f"[b]{sender}:[/b] {text}", markup=True,
            font_size="14sp", size_hint_y=None,
            text_size=(self.width - 40, None),
            halign="left", valign="middle",
            padding=(8, 6), color=(1, 1, 1, 1)
        )
        lbl.bind(texture_size=lbl.setter("size"))

        from kivy.uix.anchorlayout import AnchorLayout
        container = BoxLayout(size_hint_y=None, height=lbl.height + 12)
        bg = Button(
            background_color=color,
            background_normal="",
            size_hint=(1, 1)
        )
        bg.add_widget(lbl)
        container.add_widget(bg)
        self.chat_box.add_widget(container)


# ── App ───────────────────────────────────────────────────────
class BluetoothApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ScanScreen(name="scan"))
        sm.add_widget(CallScreen(name="call"))
        sm.add_widget(MessageScreen(name="messages"))
        return sm


if __name__ == "__main__":
    BluetoothApp().run()
