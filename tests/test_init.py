"""Config entry lifecycle for the JuTai BLE Lights integration."""

from homeassistant.config_entries import ConfigEntryState

from .conftest import setup_integration


async def test_setup_creates_entity(hass, mock_ble, mock_config_entry):
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get("light.test_light") is not None


async def test_unload(hass, mock_ble, mock_config_entry):
    await setup_integration(hass, mock_config_entry)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
