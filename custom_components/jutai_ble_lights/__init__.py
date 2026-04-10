"""The JuTai BLE Lights integration.

Lifecycle:
  async_setup_entry  — called by HA when the integration is loaded.
                       Forwards setup to the light platform and registers
                       an options listener that reloads on config changes.
  async_unload_entry — called by HA when the integration is removed or reloaded.
                       Tears down the light platform and cleans up shared data.
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light"]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up via YAML (not used — all config goes through the UI flow)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a JuTai BLE light from a config entry."""
    _LOGGER.info("Setting up JuTai BLE Lights integration for %s", entry.data.get("name"))
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the integration when the user saves new options (e.g. a renamed device).
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _LOGGER.debug("JuTai BLE Lights setup complete")
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a JuTai BLE light config entry."""
    _LOGGER.info("Unloading JuTai BLE Lights integration")
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "light")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("JuTai BLE Lights unloaded successfully")
    return unload_ok
