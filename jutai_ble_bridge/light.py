from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from bleak import BleakClient

from .jutai_protocol import (
    WRITE_CHAR_UUID,
    build_on_cmd,
    build_off_cmd,
    build_brightness_cmd,
)


class JutaiBleLight(LightEntity):

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, mac: str, name: str):
        self._hass = hass
        self._mac = mac
        self._attr_name = name
        self._attr_unique_id = f"jutai_{mac.replace(':', '')}"

        self._is_on = False
        self._brightness = 255  # HA brightness range 1–255

    @property
    def is_on(self) -> bool:
        return self._is_on

    def _scale_ha_to_jutai(self, bri: int) -> int:
        """Convert HA (0–255) -> Jutai (0–100)."""
        return round((bri / 255) * 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if "brightness" in kwargs:
            ha_bri = kwargs["brightness"]
            jutai_bri = self._scale_ha_to_jutai(ha_bri)
            cmd = build_brightness_cmd(jutai_bri)
            self._brightness = ha_bri
            self._is_on = True
        else:
            cmd = build_on_cmd()
            self._is_on = True

        await self._send(cmd)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._send(build_off_cmd())
        self._is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        # Jutai protokolliert keine Statuswerte
        return

    async def _send(self, hex_cmd: str) -> None:
        payload = hex_cmd.encode("ascii")

        async with BleakClient(self._mac) as client:
            await client.write_gatt_char(
                WRITE_CHAR_UUID,
                payload,
                response=False
            )
