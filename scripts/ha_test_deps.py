"""Install the Home Assistant dependencies the tests need.

`pip install homeassistant` ships the component source but none of the
per-integration requirements Home Assistant installs at runtime. Importing
light.py reaches homeassistant.components.bluetooth, which needs habluetooth,
dbus-fast and friends, and which imports homeassistant.components.usb, needing
aiousbwatcher.

This reads the `requirements` of a known set of components from the manifests
of the installed Home Assistant, applying that same Home Assistant's
constraints, so the installed versions keep matching whichever Home Assistant
the harness resolved to.

Run after installing requirements-test.txt:
    python scripts/ha_test_deps.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Components whose requirements light.py needs at import time. `bluetooth` is
# a direct dependency of this integration; `usb` is pulled in because Home
# Assistant's `bluetooth` component imports `homeassistant.components.usb`
# (routed through `bluetooth_adapters`, not a manifest `dependencies` entry).
COMPONENTS = ("bluetooth", "usb")


def main() -> int:
    import homeassistant

    ha_root = Path(homeassistant.__file__).parent

    requirements: list[str] = []
    for component in COMPONENTS:
        manifest = ha_root / "components" / component / "manifest.json"
        requirements += json.loads(manifest.read_text(encoding="utf-8")).get(
            "requirements", []
        )

    requirements = sorted(set(requirements))
    print("Installing Home Assistant's bluetooth stack:")
    for requirement in requirements:
        print(f"  {requirement}")

    # Home Assistant's own constraints keep transitive versions consistent with
    # what it ships.
    constraints = ha_root / "package_constraints.txt"

    return subprocess.call(
        [sys.executable, "-m", "pip", "install", "-c", str(constraints), *requirements]
    )


if __name__ == "__main__":
    raise SystemExit(main())
