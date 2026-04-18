"""
messenger.py — Bluetooth text messaging via RFCOMM.

Protocol:
  Each message is sent as: <4-byte length header><UTF-8 payload>
  This lets the receiver know exactly how many bytes to read,
  handling partial TCP-style packet splits cleanly.
"""

import logging
import struct
import threading

logger = logging.getLogger(__name__)

RFCOMM_PORT = 3   # Use port 3 for messaging (port 1 is used by caller)
BUFFER_SIZE = 4096


class BluetoothMessenger:
    """Send and receive text messages over Bluetooth RFCOMM."""

    def __init__(self):
        self._sock    = None
        self._lock    = threading.Lock()
        self._connected = False

    # ── Connection ─────────────────────────────────────────
    def connect(self, target_addr: str, port: int = RFCOMM_PORT) -> bool:
        """Connect to target device. Returns True on success."""
        try:
            import bluetooth
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((target_addr, port))
            self._sock = sock
            self._connected = True
            logger.info("Messenger connected to %s", target_addr)
            return True

        except ImportError:
            logger.warning("pybluez not installed — mock messenger mode")
            self._connected = True  # simulate connection for testing
            return True

        except Exception as exc:
            logger.error("Messenger connect failed: %s", exc)
            return False

    def disconnect(self):
        """Close the messaging connection."""
        self._connected = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    # ── Send ───────────────────────────────────────────────
    def send(self, message: str) -> bool:
        """
        Send a UTF-8 text message.
        Returns True if sent successfully.
        """
        if not self._connected:
            logger.warning("Cannot send — not connected")
            return False

        try:
            payload = message.encode("utf-8")
            header  = struct.pack(">I", len(payload))   # 4-byte big-endian length
            with self._lock:
                if self._sock:
                    self._sock.send(header + payload)
                    logger.debug("Sent %d bytes", len(payload))
                else:
                    # Mock mode: just log
                    logger.info("[MOCK] Sent: %s", message)
            return True

        except Exception as exc:
            logger.error("Send failed: %s", exc)
            return False

    # ── Receive ────────────────────────────────────────────
    def receive(self) -> str | None:
        """
        Block until a message arrives, then return it as a string.
        Returns None on connection loss or error.
        """
        if not self._connected or not self._sock:
            return None
        try:
            # Read 4-byte length header
            header = self._recv_exact(4)
            if not header:
                return None
            length = struct.unpack(">I", header)[0]

            # Read exactly `length` bytes
            payload = self._recv_exact(length)
            if not payload:
                return None

            return payload.decode("utf-8")

        except Exception as exc:
            if self._connected:
                logger.error("Receive failed: %s", exc)
            return None

    def _recv_exact(self, n: int) -> bytes | None:
        """Read exactly n bytes from the socket."""
        data = b""
        while len(data) < n:
            try:
                chunk = self._sock.recv(n - len(data))
                if not chunk:
                    return None
                data += chunk
            except Exception:
                return None
        return data

    @property
    def is_connected(self) -> bool:
        return self._connected
