# CLAUDE.md — JuTai BLE Lights (Home Assistant Custom Integration)

## Project Overview

Home Assistant **custom integration** for controlling JuTai / Lumineo BLE LED light strings directly via Bluetooth Low Energy — no MQTT broker, no cloud, no app required. The project reverse-engineers the proprietary BLE protocol from the Lumineo Twinkle Lights app.

> **Note:** This is a native HA custom integration with direct BLE control — no MQTT involved. The legacy add-on approach (with MQTT bridge) is archived in the `legacy/addon` branch.

## Repository Structure

```
jutai_ble_lights/          # Main integration package (installed into HA custom_components)
├── __init__.py            # Integration setup & config entry lifecycle
├── const.py               # Constants (DOMAIN = "jutai_ble_lights")
├── config_flow.py         # Config UI: user enters device name + MAC address
├── light.py               # LightEntity: BLE communication & state management
├── bluetooth.py           # BLE discovery callback (manufacturer data prefix 574C54)
├── jutai_protocol.py      # Command builders for the proprietary BLE protocol
├── manifest.json          # Integration metadata, requirements, version
├── strings.json           # English UI strings
└── translations/de.json   # German UI strings
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
"requirements": ["bleak>=0.22.0,<3.0.0", "bleak-retry-connector>=3.0.0"],
"dependencies": ["bluetooth"]
```

- `bleak` — Python BLE library
- `bleak-retry-connector` — Resilient connection wrapper
- `bluetooth` — HA's built-in Bluetooth integration (must be set up in HA)

## Integration Metadata

- **Domain:** `jutai_ble_lights`
- **Version:** 0.2.0
- **IoT Class:** `local_push`
- **Integration type:** `device`
- **Config flow:** enabled
- **Min HA version:** 2023.1 (effectively; requires native BT integration)

## Branch Strategy

| Branch                         | Purpose                                   |
|--------------------------------|-------------------------------------------|
| `main`                         | Stable / production                       |
| `fix/bleak-requirements-ha-2026` | Current: bleak version fix for HA 2026.4 |
| `legacy/addon`                 | Archived old MQTT add-on approach         |

## Common Tasks

### Adding a new BLE command
1. Add the command builder to [jutai_ble_lights/jutai_protocol.py](jutai_ble_lights/jutai_protocol.py)
2. Call it from [jutai_ble_lights/light.py](jutai_ble_lights/light.py) inside the asyncio lock

### Testing locally
No automated tests exist. Manual testing steps:
1. Copy `jutai_ble_lights/` into `<HA config>/custom_components/`
2. Restart Home Assistant
3. Add integration via Settings → Devices & Services → Add Integration → JuTai BLE Lights
4. Test via HA UI: toggle, brightness slider

### Enabling debug logs in HA
```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.jutai_ble_lights: debug
```

## Known Issues / Context

- **HA 2026.4.0 compatibility:** bleak constraint was `<2.0.0`, bumped to `<3.0.0` in current branch (`fix/bleak-requirements-ha-2026`)
- No automated tests or CI/CD
- HACS submission is planned but not yet done
