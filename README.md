# JuTai BLE Lights - Home Assistant Custom Integration

Home Assistant custom integration for controlling JuTai / Lumineo BLE LED light strings directly via Bluetooth.

This integration implements the BLE protocol used by the [Lumineo Twinkle Lights App](https://apps.apple.com/de/app/lumineo-twinkle-lights/id1621681360) to provide native Home Assistant support with UI configuration — no MQTT broker or mobile app required!

## Features

- ✨ **UI Configuration** — Add devices through Home Assistant's integration UI
- 🔌 **Direct BLE Control** — Communicates directly with JuTai devices via Bluetooth
- 💡 **Full Light Entity Support** — Power ON/OFF and brightness control (0-100%)
- 🚀 **Fast & Reliable** — Uses `bleak-retry-connector` for stable connections
- 📱 **Home Assistant Native** — No external dependencies or bridges needed

## Requirements

- Home Assistant 2023.1 or newer
- Bluetooth adapter accessible to Home Assistant
- JuTai / Lumineo BLE LED light string devices

## Installation

### HACS (Recommended - Coming Soon)

This integration will be available through HACS in the future.

### Manual Installation

1. Copy the `jutai_ble_lights` folder to your Home Assistant `custom_components` directory:
   ```bash
   # On your Home Assistant host
   cd /config
   mkdir -p custom_components
   cp -r jutai_ble_lights custom_components/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "JuTai BLE Lights" and click to add

5. Enter the device details:
   - **Name**: Friendly name for your light (e.g., "Living Room Lights")
   - **MAC Address**: Bluetooth MAC address of your JuTai device (e.g., `57:4C:54:2C:8F:93`)

6. Click Submit — your light should now appear as a device!

## Finding Your Device MAC Address

Use the Bluetooth integration in Home Assistant or scan with tools like:

```bash
# Linux/Raspberry Pi
sudo hcitool lescan

# Or use bluetoothctl
bluetoothctl
scan on
# Wait for "JuTai" or similar device name, note the MAC address
```

## Usage

Once configured, your JuTai lights appear as standard Home Assistant light entities with:

- **Turn On/Off** — Toggle power state
- **Brightness** — Adjust from 0-100% via the UI slider

## Troubleshooting

### Integration not appearing in UI
- Ensure `config_flow: true` is in `manifest.json`
- Check Home Assistant logs for errors during integration load

### "Device not found" errors
- Verify the MAC address is correct
- Ensure the device is powered on and in range
- Check that Home Assistant has Bluetooth access:
  ```bash
  # In HA container or host
  hciconfig
  ```

### Slow response times
- Move the Bluetooth adapter closer to the device (improve RSSI)
- Check logs for connection timing details
- Ensure no other apps are connected to the device

### Enable Debug Logging

Add to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.jutai_ble_lights: debug
```

Then check **Settings** → **System** → **Logs** for detailed debug output.

## Development

Want to contribute or modify the integration? See the code structure:

```
jutai_ble_lights/
├── __init__.py          # Integration setup
├── config_flow.py       # UI configuration flow
├── const.py             # Constants (domain name)
├── light.py             # Light entity implementation
├── jutai_protocol.py    # JuTai BLE protocol commands
├── manifest.json        # Integration metadata
└── strings.json         # UI translations
```

### Running in Dev Container

See the repository for VSCode Dev Container configuration for local development with Home Assistant Core.

## Protocol Details

This integration uses the BLE protocol from the **Lumineo Twinkle Lights** mobile app ([iOS App Store](https://apps.apple.com/de/app/lumineo-twinkle-lights/id1621681360)).

Commands are sent as ASCII-encoded hex strings to GATT characteristic `0000fff1-0000-1000-8000-00805f9b34fb`:

- **Power ON**: `574C54021101`
- **Power OFF**: `574C54021102`
- **Brightness**: `574C540209[HEX]00` where `[HEX]` is brightness 0-100 (0x00-0x64 in hexadecimal)

Example: 50% brightness = `574C54020932` (0x32 = 50 decimal)

## License

See [LICENSE](LICENSE) file.

## Credits

Protocol reverse-engineered from the [Lumineo Twinkle Lights App](https://apps.apple.com/de/app/lumineo-twinkle-lights/id1621681360) BLE communication with JuTai LED controllers. 

Thanks to the Home Assistant community for integration development guidance!
