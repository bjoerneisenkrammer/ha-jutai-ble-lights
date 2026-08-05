"""Shared fixtures for the JuTai BLE Lights tests."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jutai_ble_lights.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load anything from custom_components/."""
    yield


@pytest.fixture
def mock_ble(mock_bluetooth: None):
    """Replace the BLE layer and hand back the fake client.

    light.py resolves the MAC through Home Assistant's bluetooth manager before
    connecting, so both seams need patching. Assertions read
    mock_ble.write_gatt_char.call_args_list.

    `jutai_ble_lights` declares `bluetooth` as a dependency, so setting up the
    config entry also sets up the real `bluetooth` integration, which would
    otherwise start a real BleakScanner and probe for adapters. Depending on
    pytest-homeassistant-custom-component's `mock_bluetooth` fixture (rather
    than hand-patching more seams here) stops that at its source, matching how
    Home Assistant's own test suite handles bluetooth-dependent config entries.
    """
    client = AsyncMock()
    client.is_connected = True

    with (
        patch(
            "custom_components.jutai_ble_lights.light.bluetooth"
            ".async_ble_device_from_address",
            return_value=object(),
        ),
        patch(
            "custom_components.jutai_ble_lights.light.establish_connection",
            new=AsyncMock(return_value=client),
        ),
    ):
        yield client


@pytest.fixture
def mock_config_entry():
    """A config entry for a single JuTai light."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Light",
        data={"name": "Test Light", "mac": "AA:BB:CC:DD:EE:FF"},
    )


async def setup_integration(hass, entry):
    """Add the entry to hass and set it up."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
