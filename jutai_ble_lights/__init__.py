from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .light import JutaiBleLight

DOMAIN = "jutai_ble_lights"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a JuTai BLE device from a config entry."""

    mac = entry.data["mac"]
    name = entry.data["name"]

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"mac": mac, "name": name}

    # Register entity
    await hass.config_entries.async_forward_entry_setups(entry, ["light"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload an integration entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(
        entry, "light"
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
