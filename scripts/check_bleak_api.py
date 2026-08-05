"""Smoke-test the bleak APIs this integration relies on.

Home Assistant installs integration requirements under its own constraints
file, which pins bleak to one exact version. A version range in manifest.json
therefore cannot select a bleak version -- it can only fail to resolve and take
the integration offline. This script replaces that non-protection: it imports
the integration against whatever bleak Home Assistant currently ships and
asserts that the specific API surface used by light.py still exists.

Run locally with:
    pip install homeassistant
    pip install -c <ha>/package_constraints.txt bleak bleak-retry-connector
    python scripts/check_bleak_api.py
"""

from __future__ import annotations

import inspect
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


def main() -> int:
    from bleak import BleakClient
    from bleak_retry_connector import BleakNotFoundError, establish_connection

    # bleak dropped the __version__ attribute, so read it from package metadata.
    bleak_version = version("bleak")
    print(f"bleak {bleak_version} / bleak-retry-connector {version('bleak-retry-connector')}")
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
    # bleak-retry-connector still resolves at this version. Home Assistant
    # itself is only installed in CI, so skip rather than fail without it.
    try:
        import custom_components.jutai_ble_lights.light  # noqa: F401
    except ModuleNotFoundError as err:
        if err.name == "homeassistant":
            print("  SKIP  light.py import (homeassistant not installed)")
        else:
            raise
    else:
        check("custom_components.jutai_ble_lights.light imports", True)

    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) failed against bleak {bleak_version}.")
        return 1

    print(f"\nAll checks passed against bleak {bleak_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
