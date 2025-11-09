ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.3.1
FROM ${BUILD_FROM}

# Labels
LABEL \
  io.hass.name="JuTai BLE MQTT Bridge" \
  io.hass.description="Bridge between Lumineo/JuTai BLE Christmas lights and MQTT" \
  io.hass.version="0.1.0" \
  maintainer="Björn Eisenkrammer"

# Install dependencies
RUN apk add --no-cache python3 py3-pip bluez && \
    pip install bleak paho-mqtt pyyaml

# Copy script and run file
COPY jutai_ble_mqtt_bridge.py /usr/src/app/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

WORKDIR /usr/src/app

# Environment variables
ENV PYTHONUNBUFFERED=1

CMD ["/run.sh"]
