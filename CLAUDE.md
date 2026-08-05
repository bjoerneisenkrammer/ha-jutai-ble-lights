# CLAUDE.md — JuTai BLE Lights (Home Assistant Custom Integration)

## Project Overview

Home Assistant **custom integration** for controlling JuTai / Lumineo BLE LED light strings directly via Bluetooth Low Energy — no MQTT broker, no cloud, no app required. The project reverse-engineers the proprietary BLE protocol from the Lumineo Twinkle Lights app.

> **Note:** This is a native HA custom integration with direct BLE control — no MQTT involved. The legacy add-on approach (with MQTT bridge) is archived in the `legacy/addon` branch.

## Repository Structure

```
custom_components/jutai_ble_lights/   # Main integration package
├── __init__.py            # Integration setup & config entry lifecycle
├── const.py               # Constants (DOMAIN = "jutai_ble_lights")
├── config_flow.py         # Config UI: user enters device name + MAC address
├── light.py               # LightEntity: BLE communication & state management
├── jutai_protocol.py      # Command builders for the proprietary BLE protocol
├── manifest.json          # Integration metadata, requirements, version
├── strings.json           # English UI strings
└── translations/de.json   # German UI strings
tests/                      # Smoke test suite (does not ship, see "Testing locally")
scripts/ha_test_deps.py      # Installs the test harness's Home Assistant's own requirements
pytest.ini                  # Test config (does not ship)
requirements-test.txt        # Test dependencies (does not ship)
README.md                  # End-user documentation
```

## BLE Protocol

- **GATT Write Characteristic UUID:** `0000fff1-0000-1000-8000-00805f9b34fb`
- Commands are ASCII-encoded hex strings sent as raw bytes:

| Action     | Command (hex)          |
|------------|------------------------|
| Turn ON    | `574C54021101`         |
| Turn OFF   | `574C54021102`         |
| Brightness | `574C540209{HH}00`     |

`{HH}` = brightness percentage 0–100 formatted as zero-padded hex (e.g., 50% → `32`).

HA brightness (0–255) is mapped to JuTai percentage (0–100) and vice versa.

## Key Implementation Details

- **Connection:** Uses `bleak-retry-connector` for reliable BLE reconnection (connect → send → disconnect per command)
- **Concurrency:** Asyncio lock (`self._lock`) prevents overlapping BLE operations
- **No polling:** `_attr_should_poll = False` — state is tracked locally
- **Device lookup:** HA's Bluetooth registry (`async_ble_device_from_address`) used to get the BLEDevice object from MAC
- **Current features:** On/Off + Brightness (0–100%)
- **Missing:** Color modes, effects/patterns, HACS listing

## Dependencies

```json
"requirements": [],
"dependencies": ["bluetooth"]
```

- `bluetooth` — HA's built-in Bluetooth integration (must be set up in HA)
- `bleak` / `bleak-retry-connector` — provided by the `bluetooth` dependency, **never declared in `requirements`**

**Do not add `bleak` or `bleak-retry-connector` to `requirements`.** HA installs
integration requirements with `--constraint package_constraints.txt`, which pins
both libraries to one exact version. A version range there cannot select a
version — it can only fail to resolve and take the integration offline, which is
what broke setup in #2 (bleak 2.x) and #9 (bleak 3.x). Compatibility with HA's
current pin is verified by CI instead, via `tests/test_bleak_api.py`, run by the
`tests` CI job.

## Integration Metadata

- **Domain:** `jutai_ble_lights`
- **Version:** 0.6.0
- **IoT Class:** `local_push`
- **Integration type:** `device`
- **Config flow:** enabled
- **Min HA version:** 2023.1 (effectively; requires native BT integration)

## Branch Strategy

| Branch                         | Purpose                                   |
|--------------------------------|-------------------------------------------|
| `main`                         | Stable / production                       |
| `legacy/addon`                 | Archived old MQTT add-on approach         |

## Common Tasks

### Adding a new BLE command
1. Add the command builder to [custom_components/jutai_ble_lights/jutai_protocol.py](custom_components/jutai_ble_lights/jutai_protocol.py)
2. Call it from [custom_components/jutai_ble_lights/light.py](custom_components/jutai_ble_lights/light.py) inside the asyncio lock

### Testing locally

```bash
pip install -r requirements-test.txt
python scripts/ha_test_deps.py
pytest tests/ -v
```

Requires Python 3.14 or newer **on Linux** — Home Assistant's bluetooth stack
(`habluetooth`, `dbus-fast`, etc., installed by `scripts/ha_test_deps.py`)
does not support Windows or macOS. On another OS, or to avoid touching your
local Python at all, run it in Docker instead:

```bash
docker run --rm -v "<repo path>:/w" -w /w python:3.14-slim bash -c \
  "pip install -q -r requirements-test.txt && python scripts/ha_test_deps.py && pytest tests/ -v"
```

`pytest-homeassistant-custom-component` is deliberately unpinned: each of its
releases pins one exact Home Assistant version, so installing the newest
release tracks Home Assistant automatically. The suite is a smoke test — it
proves the integration still loads, its config flow creates a working entry,
and it responds to a service call against current Home Assistant. It does not
cover reconnect logic, the asyncio lock, BLE error paths, options-flow reload,
or state restore.

Manual verification against real hardware is still worthwhile before a release:
copy `custom_components/jutai_ble_lights/` into `<HA config>/custom_components/`,
restart Home Assistant, and test the toggle and brightness slider.

### Enabling debug logs in HA
```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.jutai_ble_lights: debug
```

## Known Issues / Context

- **bleak requirement removed (#9):** declaring `bleak` in `requirements` broke setup on every HA
  major bleak bump (#2 for 2026.1/bleak 2.x, #9 for 2026.6/bleak 3.x). Both libraries now come
  from the `bluetooth` dependency. See the Dependencies section before touching `requirements`.
- CI runs Hassfest, HACS validation, and the test suite (on push, on PRs, and weekly)
- GitHub disables scheduled workflows after 60 days without repository activity.
  The weekly run is how the unpinned test harness keeps tracking Home
  Assistant (see "Testing locally"), so after a quiet stretch it needs
  re-enabling under Actions before it can be relied on again
- `bluetooth.py` was removed in 0.6.0: it was never called, and automatic
  discovery needs a `bluetooth` matcher in `manifest.json` plus an
  `async_step_bluetooth` config-flow step, neither of which exists yet
- HACS submission is planned but not yet done
