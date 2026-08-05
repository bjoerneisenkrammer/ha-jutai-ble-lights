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
current pin is verified by CI instead, via `scripts/check_bleak_api.py`.

## Integration Metadata

- **Domain:** `jutai_ble_lights`
- **Version:** 0.5.1
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
No automated tests exist. Manual testing steps:
1. Copy `custom_components/jutai_ble_lights/` into `<HA config>/custom_components/`
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

- **bleak requirement removed (#9):** declaring `bleak` in `requirements` broke setup on every HA
  major bleak bump (#2 for 2026.1/bleak 2.x, #9 for 2026.6/bleak 3.x). Both libraries now come
  from the `bluetooth` dependency. See the Dependencies section before touching `requirements`.
- CI runs Hassfest, HACS validation, and a weekly `bleak` API compatibility check
- No unit tests for the entity logic yet
- HACS submission is planned but not yet done
