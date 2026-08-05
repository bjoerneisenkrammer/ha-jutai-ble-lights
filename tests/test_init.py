"""Config entry lifecycle for the JuTai BLE Lights integration."""

import logging

from homeassistant.config_entries import ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType

from custom_components.jutai_ble_lights.const import DOMAIN

from .conftest import setup_integration


async def test_setup_creates_entity(hass, mock_ble, mock_config_entry, caplog):
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get("light.test_light") is not None

    # Home Assistant reports custom-integration deprecations through the
    # logger rather than warnings.warn, so pytest.ini's filterwarnings can't
    # see them. Catching them here turns this suite into an early-warning
    # system for API churn that would otherwise only surface as a user bug
    # report once Home Assistant removes the deprecated path.
    assert not [
        record
        for record in caplog.records
        if record.levelno >= logging.WARNING and "deprecated" in record.message.lower()
    ]


async def test_user_flow_creates_entry(hass, mock_ble):
    """The setup form the user fills in must actually create a working entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Test Light", "mac": "aa:bb:cc:dd:ee:ff"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # config_flow.py upper-cases the MAC on submit; the lowercase input above
    # pins that behaviour rather than assuming it.
    assert result["data"]["mac"] == "AA:BB:CC:DD:EE:FF"


async def test_unload(hass, mock_ble, mock_config_entry):
    await setup_integration(hass, mock_config_entry)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
