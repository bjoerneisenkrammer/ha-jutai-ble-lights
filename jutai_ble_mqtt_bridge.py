#!/usr/bin/env python3
import asyncio
import os
import yaml
import argparse
import logging
from bleak import BleakClient
import paho.mqtt.client as mqtt

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
MQTT_BROKER = os.getenv("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_PREFIX = "blelights"

# BLE characteristic UUID for Jutai devices
WRITE_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# Map all available lighting modes (mode number -> description)
MODES = {
    1: "Combination",
    2: "In Waves",
    3: "Sequential",
    4: "Slo-Glo",
    5: "Chasing/Flash",
    6: "Slow Fade",
    7: "Twinkle/Flash",
    8: "Steady On",
}

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def load_devices_config(path="/config/jutai_devices.yaml"):
    """Load device mapping (name -> MAC) from YAML file."""
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        devices = {dev["name"]: dev["mac"] for dev in data.get("lights", [])}
        return devices
    except Exception as e:
        raise RuntimeError(f"Failed to load devices config: {e}")

def build_command(mac_prefix: str, command_bytes: bytes) -> bytes:
    """Build full BLE command including Jutai header (574C + data)."""
    return bytes.fromhex(mac_prefix) + command_bytes

def get_mac_prefix():
    """Return static manufacturer prefix (always 574C54 for Jutai)."""
    return "574C54"

def brightness_to_hex(value: int) -> str:
    """Convert brightness (0–100) into Jutai-compatible hex string."""
    value = max(0, min(value, 100))
    hex_val = f"{int(value * 255 / 100):02X}"
    return f"540209{hex_val}00"

async def send_ble_command(mac: str, hex_command: str):
    """Connect to device and send BLE command."""
    try:
        async with BleakClient(mac) as client:
            if not client.is_connected:
                logging.error(f"Failed to connect to {mac}")
                return False
            await client.write_gatt_char(WRITE_CHAR_UUID, bytes.fromhex(hex_command))
            logging.info(f"Sent command to {mac}: {hex_command}")
            return True
    except Exception as e:
        logging.error(f"BLE command failed for {mac}: {e}")
        return False

# -------------------------------------------------------------------
# MQTT logic
# -------------------------------------------------------------------

def on_message(client, userdata, msg):
    """Handle MQTT command messages."""
    try:
        payload = msg.payload.decode().strip()
        topic_parts = msg.topic.split("/")
        device_name = topic_parts[1]
        devices = userdata["devices"]

        if device_name not in devices:
            logging.warning(f"Unknown device '{device_name}' in topic {msg.topic}")
            return

        mac = devices[device_name]
        mac_prefix = get_mac_prefix()

        if payload == "on":
            cmd = f"{mac_prefix}54021101"
        elif payload == "off":
            cmd = f"{mac_prefix}54021102"
        elif payload.startswith("brightness:"):
            brightness = int(payload.split(":")[1])
            cmd = mac_prefix + brightness_to_hex(brightness)
        elif payload.startswith("mode:"):
            mode_num = int(payload.split(":")[1])
            if mode_num not in MODES:
                logging.warning(f"Invalid mode {mode_num}")
                return
            cmd = f"{mac_prefix}54020{mode_num:02X}00"
        else:
            logging.warning(f"Unsupported payload: {payload}")
            return

        asyncio.run(send_ble_command(mac, cmd))

    except Exception as e:
        logging.error(f"Error handling MQTT message: {e}")

# -------------------------------------------------------------------
# Main entrypoint
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Jutai BLE MQTT Bridge")
    parser.add_argument("--config", default="/config/jutai_devices.yaml", help="Path to device config file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    devices = load_devices_config(args.config)
    logging.info(f"Loaded devices: {devices}")

    client = mqtt.Client(userdata={"devices": devices})
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/+/set")

    logging.info("Jutai BLE MQTT bridge running. Waiting for commands...")
    client.loop_forever()

if __name__ == "__main__":
    main()
