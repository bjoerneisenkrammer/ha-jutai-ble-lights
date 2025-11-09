#!/usr/bin/with-contenv bashio
# Load MQTT credentials from add-on config
export MQTT_HOST=$(bashio::config 'mqtt_host')
export MQTT_PORT=$(bashio::config 'mqtt_port')
export MQTT_USER=$(bashio::config 'mqtt_user')
export MQTT_PASS=$(bashio::config 'mqtt_pass')

echo "Starting JuTai BLE MQTT Bridge..."
python3 /usr/src/app/jutai_ble_mqtt_bridge.py --config /config/jutai_devices.yaml
