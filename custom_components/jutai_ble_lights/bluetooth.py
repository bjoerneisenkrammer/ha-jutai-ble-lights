"""BLE device discovery helper for JuTai lights.

HA's Bluetooth integration continuously scans for nearby BLE devices and fires
callbacks when advertisement data is received. This module registers such a
callback and filters for JuTai devices by their manufacturer data prefix
(0x574C54 = "WLT").

The discovery does not add devices automatically — it only keeps HA's internal
BLE device registry up to date so that async_ble_device_from_address() in
light.py can resolve a MAC address to a BLEDevice at connection time.
"""

from homeassistant.components.bluetooth import async_register_callback, BluetoothCallbackMatcher

PREFIX = bytes.fromhex("574C54")


def async_setup_discovery(hass, callback):
    """Register a BLE advertisement callback that fires for JuTai devices."""

    def _handle(service_info):
        # Check all manufacturer data blobs; JuTai devices always start with PREFIX.
        for data in service_info.manufacturer_data.values():
            if data.startswith(PREFIX):
                callback(service_info)
                return  # Only fire the callback once per advertisement.

    # Match all connectable devices; JuTai filtering happens inside _handle.
    matcher = BluetoothCallbackMatcher(connectable=True)
    async_register_callback(hass, _handle, matcher)
