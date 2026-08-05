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

import datetime
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
    """Document that the installed bleak matches Home Assistant's pin.

    This cannot actually fail as currently wired: `scripts/ha_test_deps.py`
    installs bleak from the very same Home Assistant's
    `package_constraints.txt` that this test reads it back from, so both
    sides always agree. It is kept anyway because it is cheap and states the
    intent plainly.

    It does NOT guard against an outdated Home Assistant slipping in whole
    (bleak pin and all) -- that incident, where an earlier CI job silently
    validated bleak 2.1.1 while Home Assistant shipped 3.0.2 because too low
    a Python version made pip backtrack to an older
    pytest-homeassistant-custom-component, is guarded by
    `test_home_assistant_version_is_recent` below instead.
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


def test_home_assistant_version_is_recent():
    """Guard against pip silently backtracking to a stale Home Assistant.

    `requirements-test.txt` deliberately leaves
    `pytest-homeassistant-custom-component` unpinned so the weekly CI run
    tracks whatever Home Assistant currently ships, while `pytest.ini` /
    CI pin the interpreter to Python 3.14. If the harness ever raises its
    own Python floor above that, pip will silently backtrack to an older
    release of it -- and with it an older Home Assistant. That old Home
    Assistant is internally consistent (its own bleak pin matches its own
    installed bleak), so `test_installed_bleak_matches_home_assistant_pin`
    above would stay green while this whole suite quietly validates a Home
    Assistant nobody runs. This test catches that by asserting the
    installed Home Assistant isn't stale.
    """
    from homeassistant import const

    if hasattr(const, "MAJOR_VERSION") and hasattr(const, "MINOR_VERSION"):
        year, month = const.MAJOR_VERSION, const.MINOR_VERSION
    else:
        match = re.match(r"(\d+)\.(\d+)", const.__version__)
        assert match, f"cannot parse Home Assistant version {const.__version__!r}"
        year, month = int(match.group(1)), int(match.group(2))

    installed = getattr(const, "__version__", f"{year}.{month}")
    today = datetime.date.today()
    age_months = (today.year - year) * 12 + (today.month - month)
    assert age_months <= 6, (
        f"Home Assistant {installed} is more than 6 months old — pip likely "
        "backtracked to an outdated pytest-homeassistant-custom-component, "
        "so this suite is validating a Home Assistant nobody runs. Check "
        "the Python version in CI against the harness's requires-python."
    )
