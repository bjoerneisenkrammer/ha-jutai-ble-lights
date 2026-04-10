"""JuTai BLE light entity.

Connection strategy:
  The entity maintains a persistent BleakClient (_client) between commands to
  avoid the latency of a full BLE handshake on every toggle or brightness change.
  _ensure_connected() reuses an existing connection if it is still alive,
  and establishes a new one otherwise.

State management:
  No polling (_attr_should_poll = False). The on/off state and brightness are
  tracked locally and pushed to HA via async_write_ha_state() after each command.

Concurrency:
  An asyncio lock (_lock) prevents two BLE writes from overlapping, which could
  corrupt the command stream or confuse the device.

Brightness mapping:
  HA uses a 0–255 scale; the JuTai protocol uses 0–100 (percentage).
  Conversion: jutai = round((ha_brightness / 255) * 100)
"""

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
    """Set up a JuTai BLE light entity from a config entry."""
    mac = entry.data["mac"]
    # Name may be overridden by the options flow; fall back to the original setup value.
    name = entry.options.get("name", entry.data["name"])

    _LOGGER.info("Setting up JuTai BLE Light: %s (%s)", name, mac)
    light = JutaiBleLight(hass, mac, name)
    async_add_entities([light], update_before_add=False)


class JutaiBleLight(LightEntity):
    """Representation of a JuTai BLE LED light strip."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_should_poll = False

    def __init__(self, hass, mac, name):
        self._hass = hass
        self._mac = mac
        self._attr_name = name
        self._attr_unique_id = f"jutai_ble_lights_{mac.replace(':','')}"
        self._is_on = False
        self._brightness = 255  # Default to full brightness for the first turn-on.
        self._lock = asyncio.Lock()
        self._client: BleakClient | None = None

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._is_on

    @property
    def brightness(self):
        """Return the current brightness (0–255), or None when the light is off."""
        return self._brightness if self._is_on else None

    async def async_turn_on(self, **kwargs):
        """Turn the light on, optionally setting brightness at the same time."""
        if "brightness" in kwargs:
            # HA sends brightness (0–255); convert to JuTai percentage (0–100).
            bri = kwargs["brightness"]
            self._brightness = bri
            jutai = round((bri / 255) * 100)
            _LOGGER.debug(
                "Turn on %s with brightness: HA=%d/255 (%.1f%%), JuTai=%d/100",
                self._attr_name, bri, (bri/255)*100, jutai
            )
            await self._send(build_on_cmd())
            await self._send(build_brightness_cmd(jutai))
        else:
            # No brightness specified — the device will restore its last brightness.
            _LOGGER.debug("Turn on %s (device will use last brightness)", self._attr_name)
            await self._send(build_on_cmd())

        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        _LOGGER.debug("Turn off %s", self._attr_name)
        cmd = build_off_cmd()
        _LOGGER.debug("Sending command: %s", cmd)
        await self._send(cmd)
        self._is_on = False
        self.async_write_ha_state()

    def _on_disconnected(self, client: BleakClient) -> None:
        """Handle an unexpected BLE disconnection."""
        _LOGGER.debug("Device %s disconnected", self._mac)
        self._client = None

    async def _ensure_connected(self) -> None:
        """Connect to the BLE device if not already connected.

        Uses bleak-retry-connector for resilient connection establishment.
        Raises BleakNotFoundError if the device is not in HA's BLE registry.
        """
        if self._client and self._client.is_connected:
            return

        _LOGGER.debug("Looking for BLE device %s", self._mac)
        ble_device = bluetooth.async_ble_device_from_address(
            self._hass, self._mac, connectable=True
        )
        if not ble_device:
            _LOGGER.error("Device %s not found", self._mac)
            raise BleakNotFoundError(f"Device {self._mac} not found")

        _LOGGER.debug("Establishing connection to %s", self._mac)
        self._client = await establish_connection(
            BleakClient,
            ble_device,
            self._mac,
            disconnected_callback=self._on_disconnected,
        )
        _LOGGER.debug("Connected to %s", self._mac)

    async def _send(self, hex_cmd: str) -> None:
        """Send a hex command string to the device over BLE.

        The command is sent as raw ASCII bytes. The asyncio lock ensures
        only one write is in flight at a time.
        """
        async with self._lock:
            await self._ensure_connected()
            encoded_cmd = hex_cmd.encode("ascii")
            _LOGGER.debug(
                "Writing to char %s: cmd='%s' (bytes: %s)",
                WRITE_CHAR_UUID, hex_cmd, encoded_cmd.hex()
            )
            await self._client.write_gatt_char(
                WRITE_CHAR_UUID,
                encoded_cmd,
                response=False,
            )
            _LOGGER.debug("Command sent successfully")

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect cleanly when the entity is removed from HA."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            self._client = None
