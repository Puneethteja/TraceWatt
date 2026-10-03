import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import paho.mqtt.client as mqtt

from ..db import insert_reading
from ..schemas import ReadingIn

logger = logging.getLogger("TraceWattMQTT")
logger.setLevel(logging.INFO)

DEFAULT_MQTT_BROKER = "test.mosquitto.org"
DEFAULT_MQTT_PORT = 1883
TOPIC_TELEMETRY = "tracewatt/telemetry/+/reading"
TOPIC_ALERTS = "tracewatt/alerts/{consumer_id}"

class MQTTService:
    """
    MQTT Telemetry Protocol Manager for TraceWatt Smart Grid Platform.
    Subscribes to smart meter readings stream and publishes risk alerts over MQTT.
    """

    def __init__(self, broker: str = DEFAULT_MQTT_BROKER, port: int = DEFAULT_MQTT_PORT):
        self.broker = broker
        self.port = port
        self.client_id = f"tracewatt_backend_{int(time.time())}"
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        self.is_connected = False
        self.ingest_callback: Optional[Callable[[Dict[str, Any]], None]] = None

        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def set_ingest_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.ingest_callback = callback

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            logger.info(f"[MQTT] Successfully connected to broker {self.broker}:{self.port}")
            self.client.subscribe(TOPIC_TELEMETRY)
            logger.info(f"[MQTT] Subscribed to telemetry topic pattern: {TOPIC_TELEMETRY}")
        else:
            logger.warning(f"[MQTT] Connection returned code {rc}")
            self.is_connected = False

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        logger.info(f"[MQTT] Disconnected from broker (code {rc})")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.info(f"[MQTT Recv] Topic: {msg.topic} | Payload: {payload}")
            
            # Store in database
            if "consumer_id" in payload and "ts" in payload:
                reading_in = ReadingIn(
                    consumer_id=payload["consumer_id"],
                    ts=datetime.fromisoformat(payload["ts"]) if isinstance(payload["ts"], str) else payload["ts"],
                    kwh=payload.get("kwh"),
                    voltage=payload.get("voltage"),
                    current=payload.get("current"),
                    power_kw=payload.get("power_kw"),
                    meter_status=payload.get("meter_status", "OK"),
                    comm_status=payload.get("comm_status", "OK")
                )
                insert_reading(reading_in)

                if self.ingest_callback:
                    self.ingest_callback(payload)
        except Exception as e:
            logger.error(f"[MQTT Error] Failed to parse message: {e}")

    def start(self):
        """Start MQTT loop in background thread."""
        try:
            self.client.connect_async(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info(f"[MQTT] Service loop started in background.")
        except Exception as e:
            logger.warning(f"[MQTT] Network connection to {self.broker} deferred/failed: {e}")

    def stop(self):
        """Stop MQTT client loop."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("[MQTT] Service stopped.")
        except Exception as e:
            logger.error(f"[MQTT Error] Stop failed: {e}")

    def publish_telemetry(self, consumer_id: str, reading_data: Dict[str, Any]) -> bool:
        """Publish smart meter reading payload over MQTT."""
        topic = f"tracewatt/telemetry/{consumer_id}/reading"
        payload = json.dumps(reading_data)
        try:
            info = self.client.publish(topic, payload, qos=0)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"[MQTT Publish Error] {e}")
            return False

    def publish_alert(self, consumer_id: str, alert_data: Dict[str, Any]) -> bool:
        """Publish fuzzy anomaly alert over MQTT."""
        topic = f"tracewatt/alerts/{consumer_id}"
        payload = json.dumps(alert_data)
        try:
            info = self.client.publish(topic, payload, qos=1)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"[MQTT Alert Error] {e}")
            return False

# Global singleton instance
mqtt_service = MQTTService()
