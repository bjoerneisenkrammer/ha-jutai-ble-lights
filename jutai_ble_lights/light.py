from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from bleak import BleakClient
from .jutai_protocol import WRITE_CHAR_UUID, build_on_cmd, build_off_cmd, build_brightness_cmd


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JuTai BLE Light from a config entry."""
    mac = entry.data["mac"]
    name = entry.data["name"]
    
    light = JutaiBleLight(hass, mac, name)
    async_add_entities([light], update_before_add=False)


class JutaiBleLight(LightEntity):
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_should_poll = False

    def __init__(self, hass, mac, name):
        self._hass = hass
        self._mac = mac
        self._attr_name = name
        self._attr_unique_id = f"jutai_ble_lights_{mac.replace(':','')}"
        self._is_on = False
        self._brightness = 255

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        if "brightness" in kwargs:
            bri = kwargs["brightness"]
            jutai = round((bri / 255) * 100)
            cmd = build_brightness_cmd(jutai)
            self._brightness = bri
            self._is_on = True
        else:
            cmd = build_on_cmd()
            self._is_on = True

        await self._send(cmd)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._send(build_off_cmd())
        self._is_on = False
        self.async_write_ha_state()

    async def _send(self, hex_cmd):
        async with BleakClient(self._mac) as client:
            await client.write_gatt_char(
                WRITE_CHAR_UUID,
                hex_cmd.encode("ascii"),
                response=False
            )
