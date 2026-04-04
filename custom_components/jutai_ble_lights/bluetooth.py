from homeassistant.components.bluetooth import async_register_callback, BluetoothCallbackMatcher

PREFIX = bytes.fromhex("574C54")

def async_setup_discovery(hass, callback):
    def _handle(service_info):
        for data in service_info.manufacturer_data.values():
            if data.startswith(PREFIX):
                callback(service_info)
                return

    matcher = BluetoothCallbackMatcher(connectable=True)
    async_register_callback(hass, _handle, matcher)
