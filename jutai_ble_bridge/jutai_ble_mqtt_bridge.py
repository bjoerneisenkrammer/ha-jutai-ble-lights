#!/usr/bin/env python3
import asyncio
import json
import os
import importlib
import yaml
import argparse
import logging
import traceback
from bleak import BleakClient
import paho.mqtt.client as mqtt

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
MQTT_BROKER = os.getenv("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_PREFIX = "blelights"

# Optional authentication (can be empty)
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")

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
    """Load device mapping (name -> MAC) either from file or env JSON."""
    # Try to read devices from environment variable first
    env_json = os.getenv("JUTAI_DEVICES_JSON")
    if env_json:
        try:
            data = json.loads(env_json)
            devices = {dev["name"]: dev["mac"] for dev in data}
            logging.info(f"✅ Loaded {len(devices)} devices from Add-on config (env).")
            return devices
        except Exception as e:
            logging.error(f"❌ Failed to parse device JSON: {e}")
            raise

    # Fallback: YAML file (for manual testing)
    if not path:
        path = "/config/jutai_devices.yaml"
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        devices = {dev["name"]: dev["mac"] for dev in data.get("lights", [])}
        logging.info(f"✅ Loaded {len(devices)} devices from {path}.")
        return devices
    except Exception as e:
        logging.error(f"❌ Failed to load device config: {e}")
        raise

def build_command(mac_prefix: str, command_bytes: bytes) -> bytes:
    """Build full BLE command including Jutai header (574C + data)."""
    return bytes.fromhex(mac_prefix) + command_bytes

def get_mac_prefix():
    """Return static manufacturer prefix (always 574C54 for Jutai)."""
    return "574C54"

def brightness_to_hex(value: int) -> str:
    """Convert brightness (0–100) into Jutai-compatible hex string."""
    value = max(0, min(value, 100))
    hex_val = f"{int(value):02X}"
    return f"0209{hex_val}00"

async def send_ble_command(mac: str, hex_command: str):
    """Connect to device and send BLE command."""
    try:
        logging.info(f"🔗 Connecting to {mac} ...")
        async with BleakClient(mac) as client:
            if not client.is_connected:
                await client.connect()
                # await asyncio.sleep(0.01)           # small delay after connect
            if not client.is_connected:
                logging.error(f"❌ Failed to connect to {mac}")
                return False
            
            logging.info(f"✅ Connected to {mac}, sending command {hex_command}")

            payload = hex_command.encode("ascii")  # ASCII text, not binary hex
            await client.write_gatt_char(WRITE_CHAR_UUID, payload, response=False)
            logging.info(f"📡 ASCII Command {payload} sent successfully to {mac}")
            return True
    except Exception as e:
        logging.error(f"⚠️ BLE command failed for {mac}: {e}")
        return False

# -------------------------------------------------------------------
# MQTT logic
# -------------------------------------------------------------------

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.debug(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        logging.error(f"❌ MQTT connection failed (code {rc})")

def on_disconnect(client, userdata, rc):
    logging.warning("⚠️ Disconnected from MQTT broker.")

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
            cmd = f"{mac_prefix}021101"
            state = "on"
        elif payload == "off":
            cmd = f"{mac_prefix}021102"
            state = "off"
        elif payload.startswith("brightness:"):
            brightness = int(payload.split(":")[1])
            cmd = mac_prefix + brightness_to_hex(brightness)
            state = f"brightness:{brightness}"
        elif payload.startswith("mode:"):
            mode_num = int(payload.split(":")[1])
            if mode_num not in MODES:
                logging.warning(f"Invalid mode {mode_num}")
                return
            cmd = f"{mac_prefix}02{mode_num:02X}00"
        else:
            logging.warning(f"Unsupported payload: {payload}")
            return

        asyncio.run(send_ble_command(mac, cmd))
        client.publish(f"{MQTT_TOPIC_PREFIX}/{device_name}/state", state, retain=True)

    except Exception as e:
        logging.error(f"Error handling MQTT message: {e}")

# -------------------------------------------------------------------
# Heartbeat loop
# -------------------------------------------------------------------

def heartbeat():
    """Regular log to confirm the bridge is alive."""
    while True:
        logging.info("💓 Bridge is still running ...")
        time = importlib.import_module("time")
        time.sleep(60)

# -------------------------------------------------------------------
# Main entrypoint
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Jutai BLE MQTT Bridge")
    parser.add_argument("--config", default="/config/jutai_devices.yaml", help="Path to device config file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    socket = importlib.import_module("socket")
    try:
        host = socket.gethostname()
    except Exception as e:
        host = "unknown"
        logging.warning(f"⚠️ Could not determine hostname: {e}")

    logging.info(f"🚀 Starting Jutai BLE MQTT Bridge on host: {host}")
    logging.debug(f"Using MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    logging.debug(f"Device config path: {args.config}")

    devices = load_devices_config(args.config)
    logging.info(f"Loaded devices: {devices}")

    client = mqtt.Client(userdata={"devices": devices})
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/+/set")

    # Start heartbeat in background
    import threading
    threading.Thread(target=heartbeat, daemon=True).start()
    
    logging.info("🟢 Jutai BLE MQTT Bridge is running and waiting for commands ...")
    client.loop_forever()

if __name__ == "__main__":
    main()
