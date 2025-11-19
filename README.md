# JuTai BLE MQTT Bridge (Home Assistant Add‑on)

Lightweight Python bridge that connects JuTai / Lumineo BLE LED light strings to MQTT so Home Assistant (or any MQTT consumer) can control power, brightness and lighting modes.

This repository contains both the bridge script and an Add‑on manifest to run it as a Home Assistant Add‑on.

## Features

- BLE communication via Bleak
- MQTT integration via paho-mqtt
- Power ON/OFF, brightness (0–100), 8 lighting modes
- Home Assistant MQTT discovery support (publishes light configs)

## Important compatibility note

This Add‑on requires access to the host BlueZ D‑Bus socket (system dbus) and a working Bluetooth adapter on the host. It will **NOT** work in environments where the container cannot access the host DBus/BlueZ (for example many pure Home Assistant OS (HAOS) installations or virtualized HAOS instances that do not expose the host Bluetooth/DBus socket). If you run Home Assistant in an environment without host Bluetooth/DBus access, the bridge cannot control BLE devices.

Recommended platforms:
- Home Assistant Supervised on a Linux host with Bluetooth/BlueZ available
- Home Assistant Container (Docker) on Linux where you can mount /run/dbus and expose Bluetooth
- A separate Linux host (or VM) with Bluetooth where you run this repository as a container or service and point Home Assistant at the MQTT broker

## Requirements

- Linux host with Bluetooth adapter and BlueZ running
- Host must expose system DBus socket (common paths: /run/dbus/system_bus_socket or /var/run/dbus/system_bus_socket)
- MQTT broker (e.g. Mosquitto, Home Assistant MQTT)
- Python packages (if running outside the Add‑on): bleak, paho-mqtt, pyyaml

## Install as Home Assistant Add‑on

1. Copy this repository into your `custom_addons/jutai_ble_bridge` directory.
2. In Supervisor → Add‑on store, click the three dots → "Reload" and open the JuTai BLE MQTT Bridge add‑on.
3. Edit Add‑on options (MQTT host, credentials, devices).
4. Important: ensure the Add‑on manifest maps the DBus/socket and allows access to Bluetooth. Example entries in `config.yaml` (manifest):
   - privileged: true
   - devices:
     - /run/dbus/system_bus_socket
     - /var/run/dbus/system_bus_socket
     - /run/dbus
     - /var/run/dbus
   Rebuild the add‑on after changes to the manifest.
5. Start the add‑on and check the logs.

## Troubleshooting

- If you see "[Errno 2] No such file or directory" when the script tries to connect, the container cannot access the host DBus socket or BlueZ.
- Check on the host (SSH / terminal):
  - ls -la /run/dbus/system_bus_socket
  - ls -la /var/run/dbus/system_bus_socket
  - bluetoothctl show
  - hciconfig -a
- Add‑on logs include a DBus detection message — confirm it finds and uses a socket path (e.g. "Using DBus socket: /run/dbus/system_bus_socket").
- If the socket is present on the host but not in the container, ensure you rebuilt the add‑on after changing `config.yaml` and that Supervisor allowed mounting the socket.

## Running outside Home Assistant

If Add‑on deployment is not possible on your HA installation, you can run the Python script on a regular Linux machine with BlueZ and Python 3.9+:

```bash
python3 -m venv venv
source venv/bin/activate
pip install bleak paho-mqtt pyyaml
python jutai_ble_mqtt_bridge.py --config /path/to/jutai_devices.yaml
```
