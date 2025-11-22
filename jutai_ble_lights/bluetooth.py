from __future__ import annotations
from homeassistant.components.bluetooth import BluetoothServiceInfo
from homeassistant.components.bluetooth.match import BluetoothCallbackMatcher
from homeassistant.components.bluetooth import async_register_callback
from homeassistant.core import HomeAssistant

DOMAIN = "jutai_ble"

MANUFACTURER_PREFIX = bytes.fromhex("574C54")


def async_setup_discovery(hass: HomeAssistant, callback):
    """Register Bluetooth discovery for Jutai devices."""

    def _handle_ble_adv(service_info: BluetoothServiceInfo):
        # Filter: Manufacturer Data starts with 574C54
        for data in service_info.manufacturer_data.values():
            if data.startswith(MANUFACTURER_PREFIX):
                callback(service_info)
                return

    matcher = BluetoothCallbackMatcher(
        connectable=True,
        manufacturer_id=None,
    )

    async_register_callback(
        hass,
        _handle_ble_adv,
        matcher,
    )
