from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN


PLATFORMS = ["light"]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up via YAML (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Jutai BLE Lights from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Jutai BLE Lights."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "light")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
