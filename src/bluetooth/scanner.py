"""
scanner.py — Discover nearby Bluetooth devices.
Uses pybluez for classic Bluetooth (RFCOMM-capable devices).
Falls back gracefully if hardware is unavailable.
"""

import logging

logger = logging.getLogger(__name__)


def scan_devices(duration: int = 8) -> list[dict]:
    """
    Scan for nearby Bluetooth devices.

    Returns:
        List of dicts: [{"addr": "AA:BB:...", "name": "DeviceName"}, ...]
    """
    try:
        import bluetooth
        logger.info("Starting Bluetooth scan for %ds…", duration)
        nearby = bluetooth.discover_devices(
            duration=duration,
            lookup_names=True,
            flush_cache=True
        )
        devices = [{"addr": addr, "name": name or "Unknown"} for addr, name in nearby]
        logger.info("Found %d device(s)", len(devices))
        return devices

    except ImportError:
        logger.error("pybluez not installed. Run: pip install pybluez")
        return _mock_devices()

    except Exception as exc:
        logger.error("Scan failed: %s", exc)
        return []


def find_service(target_addr: str, service_name: str) -> dict | None:
    """
    Search for a specific Bluetooth service on a paired device.

    Args:
        target_addr: Device MAC address
        service_name: Service name to search for (e.g. "SerialPort")

    Returns:
        Service info dict or None
    """
    try:
        import bluetooth
        services = bluetooth.find_service(address=target_addr)
        for svc in services:
            if service_name.lower() in (svc.get("name") or "").lower():
                return svc
        return None
    except Exception as exc:
        logger.error("Service search failed: %s", exc)
        return None


def _mock_devices() -> list[dict]:
    """Return fake devices for testing on desktop (no BT hardware needed)."""
    return [
        {"addr": "AA:BB:CC:DD:EE:01", "name": "Mock Phone"},
        {"addr": "AA:BB:CC:DD:EE:02", "name": "Mock Headset"},
        {"addr": "AA:BB:CC:DD:EE:03", "name": "Mock Speaker"},
    ]
