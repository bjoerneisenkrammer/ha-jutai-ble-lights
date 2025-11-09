#!/usr/bin/with-contenv bashio
# Load MQTT credentials from add-on config
export MQTT_HOST=$(bashio::config 'mqtt_host')
export MQTT_PORT=$(bashio::config 'mqtt_port')
export MQTT_USER=$(bashio::config 'mqtt_user')
export MQTT_PASS=$(bashio::config 'mqtt_pass')

# Pass devices list as JSON
export JUTAI_DEVICES_JSON="$(bashio::config 'devices')"

# Set DBUS system bus address
export DBUS_SYSTEM_BUS_ADDRESS="unix:path=/var/run/dbus/system_bus_socket"

# Activate virtual environment
source /opt/venv/bin/activate

# Run the bridge script
echo "Starting JuTai BLE MQTT Bridge with devices from Add-on config..."
python3 /usr/src/app/jutai_ble_mqtt_bridge.py
