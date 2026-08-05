"""Smoke-test the bleak APIs this integration relies on.

Home Assistant installs integration requirements under its own constraints
file, which pins bleak to one exact version. A version range in manifest.json
therefore cannot select a bleak version -- it can only fail to resolve and take
the integration offline. This script replaces that non-protection: it imports
the integration against whatever bleak Home Assistant currently ships and
asserts that the specific API surface used by light.py still exists.

Run locally (needs the Python version HA requires, currently >=3.14):
    pip install homeassistant
    python -c "import homeassistant,pathlib,json; r=pathlib.Path(homeassistant.__file__).parent; print('\n'.join(json.loads((r/'components/bluetooth/manifest.json').read_text())['requirements']))" > bt.txt
    pip install -r bt.txt
    python scripts/check_bleak_api.py

Without Home Assistant installed, the HA-dependent checks are skipped and only
the raw bleak API assertions run.
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAILURES: list[str] = []


def check(description: str, condition: bool) -> None:
    """Record the outcome of a single API assertion."""
    print(f"  {'OK  ' if condition else 'FAIL'}  {description}")
    if not condition:
        FAILURES.append(description)


def skip(description: str) -> None:
    """Note a check that could not run in this environment."""
    print(f"  SKIP  {description}")


def ha_pinned_bleak_version() -> str | None:
    """Return the bleak version Home Assistant pins, or None if HA is absent.

    This is the version the integration will actually run against, so it is
    also the only version worth testing.
    """
    try:
        import homeassistant
    except ModuleNotFoundError:
        return None

    constraints = Path(homeassistant.__file__).parent / "package_constraints.txt"
    match = re.search(r"^bleak==(\S+)$", constraints.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def main() -> int:
    from bleak import BleakClient
    from bleak_retry_connector import BleakNotFoundError, establish_connection

    # bleak dropped the __version__ attribute, so read it from package metadata.
    bleak_version = version("bleak")
    print(f"bleak {bleak_version} / bleak-retry-connector {version('bleak-retry-connector')}")

    # Guard against silently validating the wrong version: if the environment
    # resolved a different bleak than HA pins (e.g. an older HA got installed
    # because the Python version was too low), every check below would be
    # meaningless.
    print("Checking the test environment matches Home Assistant:")
    pinned = ha_pinned_bleak_version()
    if pinned is None:
        skip("bleak matches HA's pin (homeassistant not installed)")
    else:
        check(
            f"installed bleak {bleak_version} matches HA's pin {pinned}",
            bleak_version == pinned,
        )

    print("Checking the bleak API surface used by light.py:")

    write_params = inspect.signature(BleakClient.write_gatt_char).parameters
    check("BleakClient.write_gatt_char accepts 'response'", "response" in write_params)

    connect_params = inspect.signature(establish_connection).parameters
    check(
        "establish_connection accepts 'disconnected_callback'",
        "disconnected_callback" in connect_params,
    )
    check("BleakClient.is_connected exists", hasattr(BleakClient, "is_connected"))
    check("BleakClient.disconnect exists", hasattr(BleakClient, "disconnect"))
    check("BleakNotFoundError is an exception", issubclass(BleakNotFoundError, Exception))

    # Importing the platform proves every symbol light.py pulls from bleak and
    # bleak-retry-connector still resolves at this version. This needs both
    # Home Assistant and the requirements of its bluetooth integration.
    try:
        import custom_components.jutai_ble_lights.light  # noqa: F401
    except ModuleNotFoundError as err:
        if err.name == "homeassistant":
            # Expected when running locally without HA.
            skip("light.py import (homeassistant not installed)")
        else:
            # HA is present but its bluetooth stack is incomplete -- treat as a
            # failure rather than skipping, so CI never reports a green build
            # on an environment that could not actually run the check.
            check(f"light.py import (missing '{err.name}')", False)
    else:
        check("custom_components.jutai_ble_lights.light imports", True)

    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) failed against bleak {bleak_version}.")
        return 1

    print(f"\nAll checks passed against bleak {bleak_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
