"""Checks against the real bleak modules, unmocked.

Every other test replaces the BLE client with an AsyncMock, which accepts any
keyword argument. A renamed bleak parameter would therefore pass unnoticed
everywhere else, so these tests deliberately use no BLE fixture.
"""

import inspect
import re
from importlib.metadata import version
from pathlib import Path

from bleak import BleakClient
from bleak_retry_connector import establish_connection


def test_write_gatt_char_accepts_response():
    params = inspect.signature(BleakClient.write_gatt_char).parameters
    assert "response" in params


def test_establish_connection_accepts_disconnected_callback():
    params = inspect.signature(establish_connection).parameters
    assert "disconnected_callback" in params


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
    assert version("bleak") == match.group(1)
