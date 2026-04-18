"""
caller.py — Bluetooth voice calls via RFCOMM + PyAudio.

How it works:
  - Opens an RFCOMM socket to the target device
  - Captures microphone audio with PyAudio
  - Streams raw PCM chunks over the socket (send thread)
  - Receives remote PCM chunks and plays them (receive thread)

Audio format: 16kHz mono 16-bit PCM — good balance of quality and bandwidth.
"""

import logging
import threading
import socket as _socket

logger = logging.getLogger(__name__)

RFCOMM_PORT    = 1       # Standard RFCOMM port; change if device uses another
CHUNK_SIZE     = 1024    # PCM bytes per network packet
SAMPLE_RATE    = 16000   # Hz
CHANNELS       = 1       # Mono
AUDIO_FORMAT   = 8       # pyaudio.paInt16 = 8


class BluetoothCaller:
    """Handles outgoing and incoming Bluetooth voice calls."""

    def __init__(self):
        self._sock    = None
        self._stream_in  = None  # mic input
        self._stream_out = None  # speaker output
        self._audio   = None
        self._running = False

    # ── Public API ─────────────────────────────────────────
    def start_call(self, target_addr: str, port: int = RFCOMM_PORT) -> bool:
        """
        Connect to target_addr and start audio streaming.
        Returns True on success, False on failure.
        """
        try:
            import bluetooth
            self._sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self._sock.connect((target_addr, port))
            logger.info("RFCOMM connected to %s", target_addr)
            self._running = True
            self._start_audio()
            threading.Thread(target=self._send_audio,  daemon=True).start()
            threading.Thread(target=self._recv_audio,  daemon=True).start()
            return True

        except ImportError:
            logger.warning("pybluez not installed — running in mock call mode")
            self._running = True
            return True  # mock success for testing

        except Exception as exc:
            logger.error("Call failed: %s", exc)
            self._sock = None
            return False

    def end_call(self):
        """Hang up and release all resources."""
        self._running = False
        self._stop_audio()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        logger.info("Call ended")

    # ── Audio setup ────────────────────────────────────────
    def _start_audio(self):
        try:
            import pyaudio
            self._audio = pyaudio.PyAudio()
            self._stream_in = self._audio.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            self._stream_out = self._audio.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE
            )
        except ImportError:
            logger.warning("PyAudio not installed — no audio hardware access")
        except Exception as exc:
            logger.error("Audio init failed: %s", exc)

    def _stop_audio(self):
        for stream in (self._stream_in, self._stream_out):
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
        self._stream_in = self._stream_out = self._audio = None

    # ── Streaming threads ──────────────────────────────────
    def _send_audio(self):
        """Mic → Bluetooth socket."""
        while self._running and self._sock and self._stream_in:
            try:
                data = self._stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
                self._sock.send(data)
            except Exception as exc:
                if self._running:
                    logger.error("Send audio error: %s", exc)
                break

    def _recv_audio(self):
        """Bluetooth socket → Speaker."""
        while self._running and self._sock:
            try:
                data = self._sock.recv(CHUNK_SIZE)
                if data and self._stream_out:
                    self._stream_out.write(data)
            except Exception as exc:
                if self._running:
                    logger.error("Recv audio error: %s", exc)
                break
