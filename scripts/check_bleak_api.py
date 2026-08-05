"""Smoke-test the bleak APIs this integration relies on.

Home Assistant installs integration requirements under its own constraints
file, which pins bleak to one exact version. A version range in manifest.json
therefore cannot select a bleak version -- it can only fail to resolve and take
the integration offline. This script replaces that non-protection: it checks the
bleak API surface the integration uses against whatever bleak Home Assistant
currently pins, so an upstream break shows up as a red build rather than as a
broken integration after a user's next upgrade.

It deliberately does not import the integration's own modules. Doing so pulls in
Home Assistant's runtime (bluetooth -> usb -> esphome -> ...), which pip does not
install and which is not what this checks. The bleak imports are read out of the
source instead.

Run locally:
    pip install bleak bleak-retry-connector
    python scripts/check_bleak_api.py

Home Assistant is optional locally; without it, the version-pin check is
skipped and only the bleak API assertions run.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
from importlib.metadata import version
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INTEGRATION_DIR = REPO_ROOT / "custom_components" / "jutai_ble_lights"

FAILURES: list[str] = []


def check(description: str, condition: bool) -> None:
    """Record the outcome of a single API assertion."""
    print(f"  {'OK  ' if condition else 'FAIL'}  {description}")
    if not condition:
        FAILURES.append(description)


def skip(description: str) -> None:
    """Note a check that could not run in this environment."""
    print(f"  SKIP  {description}")


def bleak_imports(source_dir: Path) -> list[tuple[str, str]]:
    """Return every (module, symbol) the integration imports from bleak.

    Parsing the source keeps this honest as the integration grows: a newly
    added bleak import is picked up automatically.
    """
    found: set[tuple[str, str]] = set()

    for path in sorted(source_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in ("bleak", "bleak_retry_connector"):
                    found.update((node.module, alias.name) for alias in node.names)

    return sorted(found)


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

    print("Checking the bleak API surface used by the integration:")

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

    # Verify every bleak symbol the integration imports still resolves.
    print("Checking the bleak symbols imported by the integration:")
    imports = bleak_imports(INTEGRATION_DIR)

    # Finding nothing would mean the parser silently stopped covering the
    # source, which must not read as a pass.
    check(f"found bleak imports in {INTEGRATION_DIR.name}", bool(imports))

    for module_name, symbol in imports:
        module = importlib.import_module(module_name)
        check(f"{module_name}.{symbol}", hasattr(module, symbol))

    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) failed against bleak {bleak_version}.")
        return 1

    print(f"\nAll checks passed against bleak {bleak_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
