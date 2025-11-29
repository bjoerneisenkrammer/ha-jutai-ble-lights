from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import bluetooth
from bleak import BleakClient
from bleak_retry_connector import establish_connection, BleakNotFoundError
import asyncio
import logging
from .jutai_protocol import WRITE_CHAR_UUID, build_on_cmd, build_off_cmd, build_brightness_cmd

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JuTai BLE Light from a config entry."""
    mac = entry.data["mac"]
    name = entry.data["name"]
    
    _LOGGER.info("Setting up JuTai BLE Light: %s (%s)", name, mac)
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
        self._lock = asyncio.Lock()

    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        """Return the brightness of the light (0-255)."""
        return self._brightness if self._is_on else None

    async def async_turn_on(self, **kwargs):
        if "brightness" in kwargs:
            bri = kwargs["brightness"]
            jutai = round((bri / 255) * 100)
            _LOGGER.debug(
                "Turn on %s with brightness: HA=%d/255 (%.1f%%), JuTai=%d/100",
                self._attr_name, bri, (bri/255)*100, jutai
            )
            cmd = build_brightness_cmd(jutai)
            self._brightness = bri
            self._is_on = True
        else:
            # Turn on without brightness change - use last brightness or send ON command
            _LOGGER.debug("Turn on %s (no brightness, using last: %d)", self._attr_name, self._brightness)
            # Send brightness command with stored value to ensure device reflects correct state
            jutai = round((self._brightness / 255) * 100)
            cmd = build_brightness_cmd(jutai)
            self._is_on = True

        _LOGGER.debug("Sending command: %s", cmd)
        await self._send(cmd)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug("Turn off %s", self._attr_name)
        cmd = build_off_cmd()
        _LOGGER.debug("Sending command: %s", cmd)
        await self._send(cmd)
        self._is_on = False
        self.async_write_ha_state()

    async def _send(self, hex_cmd):
        async with self._lock:
            _LOGGER.debug("Looking for BLE device %s", self._mac)
            ble_device = bluetooth.async_ble_device_from_address(
                self._hass, self._mac, connectable=True
            )
            if not ble_device:
                _LOGGER.error("Device %s not found", self._mac)
                raise BleakNotFoundError(f"Device {self._mac} not found")
            
            _LOGGER.debug("Establishing connection to %s", self._mac)
            client = await establish_connection(
                BleakClient,
                ble_device,
                self._mac,
            )
            try:
                encoded_cmd = hex_cmd.encode("ascii")
                _LOGGER.debug(
                    "Writing to char %s: cmd='%s' (bytes: %s)",
                    WRITE_CHAR_UUID, hex_cmd, encoded_cmd.hex()
                )
                await client.write_gatt_char(
                    WRITE_CHAR_UUID,
                    encoded_cmd,
                    response=False
                )
                _LOGGER.debug("Command sent successfully")
            finally:
                await client.disconnect()
                _LOGGER.debug("Disconnected from %s", self._mac)
