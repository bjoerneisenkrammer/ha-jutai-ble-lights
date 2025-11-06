# JuTai BLE MQTT Bridge

A lightweight Python bridge that connects **JuTai BLE-based LED light strings** (and similar devices)  
to **Home Assistant** or any other MQTT-compatible smart home system.

This project allows you to control these lights (power, brightness, and mode)  
via MQTT topics — ideal for automation or smart integrations.

---

## ✨ Features

- 🧠 BLE communication via [Bleak](https://github.com/hbldh/bleak)
- 📡 MQTT integration via [paho-mqtt](https://github.com/eclipse/paho.mqtt.python)
- 💡 Supports:
  - Power ON/OFF
  - Brightness (0–100%)
  - 8 lighting modes
- ⚙️ Works with any JuTai Bluetooth light (e.g. Christmas lights, LED strings)
- 🔌 Tested with Home Assistant (MQTT integration)

---

## 🧰 Requirements

- Python **3.9+**
- A Bluetooth adapter compatible with your system
- An MQTT broker (e.g. Mosquitto, Home Assistant MQTT)
- The following Python packages:

```bash
pip install bleak paho-mqtt pyyaml
