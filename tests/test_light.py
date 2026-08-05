"""Entity attributes and service calls for the JuTai BLE light."""

from homeassistant.components.light import ColorMode
from homeassistant.helpers import entity_registry as er

from .conftest import setup_integration

ENTITY_ID = "light.test_light"


def _payloads(mock_ble):
    """Return the bytes written to the device, in order."""
    return [call.args[1] for call in mock_ble.write_gatt_char.call_args_list]


async def test_entity_attributes(hass, mock_ble, mock_config_entry):
    await setup_integration(hass, mock_config_entry)

    entry = er.async_get(hass).async_get(ENTITY_ID)
    assert entry.unique_id == "jutai_ble_lights_AABBCCDDEEFF"

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]


async def test_turn_on_with_brightness(hass, mock_ble, mock_config_entry):
    await setup_integration(hass, mock_config_entry)
    mock_ble.write_gatt_char.reset_mock()

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": ENTITY_ID, "brightness": 128},
        blocking=True,
    )
    await hass.async_block_till_done()

    # On first, then brightness: 128/255 rounds to 50 %, encoded as 0x32.
    assert _payloads(mock_ble) == [b"574C54021101", b"574C5402093200"]

    state = hass.states.get(ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["brightness"] == 128


async def test_turn_on_with_brightness_pins_rounding(hass, mock_ble, mock_config_entry):
    """128/255 rounds to 50% either way; 5/255 does not, so it pins round()."""
    await setup_integration(hass, mock_config_entry)
    mock_ble.write_gatt_char.reset_mock()

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": ENTITY_ID, "brightness": 5},
        blocking=True,
    )
    await hass.async_block_till_done()

    # round(5/255*100) = round(1.96) = 2 (0x02). Truncating methods give 1.
    assert _payloads(mock_ble) == [b"574C54021101", b"574C5402090200"]

    state = hass.states.get(ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["brightness"] == 5


async def test_turn_off(hass, mock_ble, mock_config_entry):
    await setup_integration(hass, mock_config_entry)
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()

    # The prelude turn_on above sent only the on command, with no brightness
    # payload -- the device restores its own last brightness (light.py). A
    # refactor that unified the two branches would push a stale
    # self._brightness (255 on first use) to the device instead, and nothing
    # else would notice.
    assert _payloads(mock_ble) == [b"574C54021101"]
    mock_ble.write_gatt_char.reset_mock()

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()

    assert _payloads(mock_ble) == [b"574C54021102"]
    assert hass.states.get(ENTITY_ID).state == "off"
