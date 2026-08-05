"""Checks against the real bleak modules, unmocked.

Every other test replaces the BLE client with an AsyncMock, which accepts any
keyword argument. A renamed bleak parameter would therefore pass unnoticed
everywhere else, so these tests deliberately use no BLE fixture.

This also covers instance-level API surface that an unspecced AsyncMock hides
just as effectively: `light.py` reads `self._client.is_connected` and calls
`self._client.disconnect()`, and every other test's `self._client` is an
unspecced `AsyncMock()` (see `tests/conftest.py`), which accepts any attribute
access or call whether or not bleak still provides it. The `hasattr` checks
below close that gap.
"""

import inspect
import re
from importlib.metadata import version
from pathlib import Path

from bleak import BleakClient
from bleak_retry_connector import BleakNotFoundError, establish_connection


def test_write_gatt_char_accepts_response():
    params = inspect.signature(BleakClient.write_gatt_char).parameters
    assert "response" in params


def test_establish_connection_accepts_disconnected_callback():
    params = inspect.signature(establish_connection).parameters
    assert "disconnected_callback" in params


def test_bleak_client_has_is_connected():
    assert hasattr(BleakClient, "is_connected")


def test_bleak_client_has_disconnect():
    assert hasattr(BleakClient, "disconnect")


def test_bleak_not_found_error_is_exception():
    assert issubclass(BleakNotFoundError, Exception)


def test_installed_bleak_matches_home_assistant_pin():
    """Guard against testing a bleak other than the one users will run.

    An earlier CI job silently validated bleak 2.1.1 while Home Assistant
    shipped 3.0.2, because the Python version was too low and pip backtracked
    to an older Home Assistant.
    """
    import homeassistant

    constraints = Path(homeassistant.__file__).parent / "package_constraints.txt"
    match = re.search(r"^bleak==(\S+)$", constraints.read_text(), re.MULTILINE)
    assert match, "no bleak pin found in package_constraints.txt"
    installed = version("bleak")
    pinned = match.group(1)
    assert installed == pinned, (
        f"installed bleak {installed} != Home Assistant's pinned {pinned}"
    )
