#!/usr/bin/env python3
"""
Jutai BLE MQTT Bridge
---------------------
A BLE → MQTT bridge for Jutai (and compatible) Bluetooth light controllers.

Features:
- Dynamic MAC address (passed as argument)
- Manufacturer prefix derived from MAC
- Clear command dictionary for easy customization
- Human-readable lighting modes
- Works seamlessly with Home Assistant MQTT Light integration

Author: (your GitHub name)
"""

import asyncio
import argparse
import os
from bleak import BleakClient
import paho.mqtt.client as mqtt

# ==========================================================
# 🧩 CONFIGURATION
# ==========================================================
MQTT_BROKER = os.getenv("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_PREFIX = "blelights"

DEFAULT_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
DEFAULT_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# ==========================================================
# 💡 COMMAND DICTIONARIES
# ==========================================================

# --- Power Commands ---
COMMANDS = {
    "on":  "54021101",
    "off": "54021102",
}

# --- Lighting Modes (1–8) ---
MODES = {
    1: {"name": "Combination",     "hex": "54020100"},
    2: {"name": "In Waves",        "hex": "54020200"},
    3: {"name": "Sequential",      "hex": "54020300"},
    4: {"name": "Slo-Glo",         "hex": "54020400"},
    5: {"name": "Chasing/Flash",   "hex": "54020500"},
    6: {"name": "Slow Fade",       "hex": "54020600"},
    7: {"name": "Twinkle/Flash",   "hex": "54020700"},
    8: {"name": "Steady On",       "hex": "54020800"},
}

# ==========================================================
# ⚙️ COMMAND BUILDERS
# ==========================================================

def build_command(mac: str, payload_hex: str) -> bytes:
    """Combine manufacturer prefix (from MAC) with command payload."""
    prefix = mac.replace(":", "")[:6].upper()
    return bytes.fromhex(prefix + payload_hex)

def build_power_command(mac: str, on: bool) -> bytes:
    """Build ON/OFF command."""
    payload = COMMANDS["on"] if on else COMMANDS["off"]
    return build_command(mac, payload)

def build_mode_command(mac: str, mode_number: int) -> bytes:
    """Build lighting mode command."""
    mode_info = MODES.get(mode_number)
    if not mode_info:
        raise ValueError(f"Invalid mode number: {mode_number}")
    return build_command(mac, mode_info["hex"])

def build_brightness_command(mac: str, brightness: int) -> bytes:
    """Build brightness command (0–100%)."""
    brightness = max(0, min(100, brightness))
    level = int((brightness / 100) * 255)
    payload = f"540209{level:02X}00"
    return build_command(mac, payload)

# ==========================================================
# 📡 MQTT HANDLER
# ==========================================================

async def handle_mqtt_message(client, ble_client, mac, topic, payload):
    """Handle incoming MQTT commands."""
    payload = payload.decode().strip().lower()
    print(f"[MQTT] Received: {payload}")

    if payload == "on":
        cmd = build_power_command(mac, True)
    elif payload == "off":
        cmd = build_power_command(mac, False)
    elif payload.startswith("brightness:"):
        brightness = int(payload.split(":")[1])
        cmd = build_brightness_command(mac, brightness)
    elif payload.startswith("mode:"):
        mode_number = int(payload.split(":")[1])
        cmd = build_mode_command(mac, mode_number)
    else:
        print(f"[WARN] Unknown command: {payload}")
        return

    print(f"[BLE] Sending: {cmd.hex()}")
    await ble_client.write_gatt_char(DEFAULT_CHAR_UUID, cmd, response=True)
    client.publish(f"{MQTT_TOPIC_PREFIX}/{mac}/state", payload)

# ==========================================================
# 🚀 MAIN LOOP
# ==========================================================

async def main(args):
    mac = args.mac.upper()
    print(f"🔗 Connecting to {mac} via BLE...")

    async with BleakClient(mac) as ble_client:
        print("✅ Connected to BLE device")

        mqtt_client = mqtt.Client()
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()

        command_topic = f"{MQTT_TOPIC_PREFIX}/{mac}/set"
        mqtt_client.subscribe(command_topic)

        def on_message(_, __, msg):
            asyncio.run_coroutine_threadsafe(
                handle_mqtt_message(mqtt_client, ble_client, mac, msg.topic, msg.payload),
                asyncio.get_event_loop()
            )

        mqtt_client.on_message = on_message
        print(f"📡 Subscribed to: {command_topic}")
        print("💡 Ready to receive MQTT commands")

        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jutai BLE → MQTT Bridge")
    parser.add_argument("--mac", required=True, help="BLE device MAC address")
    args = parser.parse_args()

    asyncio.run(main(args))
