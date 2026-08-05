"""Print the Python requirements Home Assistant loads for this integration.

`pip install homeassistant` ships the component source but none of the
per-integration requirements -- Home Assistant installs those at runtime, for
the whole dependency closure of an integration. Importing light.py therefore
needs more than the bluetooth integration's own requirements: bluetooth depends
on usb, which needs aiousbwatcher, and so on.

This walks our manifest's `dependencies` through Home Assistant's component
manifests and prints every requirement in that closure, so CI can install
exactly what the integration would have at runtime.

Usage:
    python scripts/ha_dep_requirements.py > requirements.txt

Set HA_COMPONENTS_DIR to point at a component tree other than the installed
Home Assistant (used by the script's own tests).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUR_MANIFEST = REPO_ROOT / "custom_components" / "jutai_ble_lights" / "manifest.json"


def components_dir() -> Path:
    """Locate Home Assistant's bundled components directory."""
    if override := os.environ.get("HA_COMPONENTS_DIR"):
        return Path(override)

    import homeassistant

    return Path(homeassistant.__file__).parent / "components"


def collect(domains: list[str], root: Path) -> list[str]:
    """Return the requirements of `domains` and everything they depend on."""
    requirements: list[str] = []
    seen: set[str] = set()
    queue = list(domains)

    while queue:
        domain = queue.pop(0)
        if domain in seen:
            continue
        seen.add(domain)

        manifest_path = root / domain / "manifest.json"
        if not manifest_path.is_file():
            print(f"warning: no manifest for dependency '{domain}'", file=sys.stderr)
            continue

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        requirements.extend(manifest.get("requirements", []))
        queue.extend(manifest.get("dependencies", []))

    # Deduplicate while keeping the order stable for readable CI logs.
    return sorted(set(requirements))


def main() -> int:
    our_manifest = json.loads(OUR_MANIFEST.read_text(encoding="utf-8"))
    dependencies = our_manifest.get("dependencies", [])
    print(f"resolving dependencies of {our_manifest['domain']}: {dependencies}", file=sys.stderr)

    for requirement in collect(dependencies, components_dir()):
        print(requirement)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
