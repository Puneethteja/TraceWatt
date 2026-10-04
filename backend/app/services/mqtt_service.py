import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import paho.mqtt.client as mqtt

from ..config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_KEEPALIVE,
    MQTT_TOPIC_TELEMETRY,
    MQTT_TOPIC_ALERTS,
    MQTT_CLIENT_ID,
    MQTT_ENABLED,
)
from ..db import insert_reading
from ..schemas import ReadingIn

logger = logging.getLogger("TraceWattMQTT")
logger.setLevel(logging.INFO)


class MQTTService:
    """
    MQTT Telemetry Protocol Engine for TraceWatt Smart Grid Platform.
    
    Subscribes to smart meter telemetry feeds across the AMI network and
    publishes real-time anomaly alerts and control messages over standard MQTT topics.
    """

    def __init__(
        self,
        broker: str = MQTT_BROKER,
        port: int = MQTT_PORT,
        keepalive: int = MQTT_KEEPALIVE,
        client_id: Optional[str] = None,
    ):
        self.broker = broker
        self.port = port
        self.keepalive = keepalive
        self.client_id = client_id or f"{MQTT_CLIENT_ID}_{int(time.time())}"
        self.enabled = MQTT_ENABLED

        # Compatibility with paho-mqtt v1.x and v2.x
        try:
            # paho-mqtt v2.0+
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id,
                protocol=mqtt.MQTTv311,
            )
        except AttributeError:
            # paho-mqtt v1.x fallback
            self.client = mqtt.Client(
                client_id=self.client_id,
                protocol=mqtt.MQTTv311,
            )

        self.is_connected = False
        self.queue_callback: Optional[Callable[[ReadingIn], None]] = None

        # Setup MQTT event callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

    def set_queue_callback(self, callback: Callable[[ReadingIn], None]):
        """Register callback to push incoming MQTT readings directly into the ML detection queue."""
        self.queue_callback = callback

    def _on_connect(self, client, userdata, flags, rc, *args):
        if rc == 0:
            self.is_connected = True
            logger.info(f"[MQTT] Connected successfully to broker {self.broker}:{self.port}")
            self.client.subscribe(MQTT_TOPIC_TELEMETRY, qos=1)
            logger.info(f"[MQTT] Subscribed to telemetry topic: {MQTT_TOPIC_TELEMETRY}")
        else:
            self.is_connected = False
            logger.warning(f"[MQTT] Connection returned error code: {rc}")

    def _on_disconnect(self, client, userdata, rc, *args):
        self.is_connected = False
        logger.info(f"[MQTT] Disconnected from broker (rc={rc})")

    def _on_publish(self, client, userdata, mid, *args):
        logger.debug(f"[MQTT] Message ID {mid} published successfully")

    def _on_message(self, client, userdata, msg):
        """Processes incoming smart meter telemetry published over MQTT."""
        try:
            payload_str = msg.payload.decode("utf-8")
            payload = json.loads(payload_str)
            logger.info(f"[MQTT Ingest] Topic: {msg.topic} | Payload: {payload_str}")

            if "consumer_id" in payload and "ts" in payload:
                # Normalize timestamp
                ts_val = payload["ts"]
                if isinstance(ts_val, str):
                    try:
                        ts_dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                    except Exception:
                        ts_dt = datetime.utcnow()
                elif isinstance(ts_val, (int, float)):
                    ts_dt = datetime.utcfromtimestamp(ts_val)
                else:
                    ts_dt = datetime.utcnow()

                reading_in = ReadingIn(
                    consumer_id=str(payload["consumer_id"]),
                    ts=ts_dt,
                    kwh=float(payload["kwh"]) if payload.get("kwh") is not None else None,
                    voltage=float(payload["voltage"]) if payload.get("voltage") is not None else 230.0,
                    current=float(payload["current"]) if payload.get("current") is not None else 0.0,
                    power_kw=float(payload["power_kw"]) if payload.get("power_kw") is not None else 0.0,
                    meter_status=str(payload.get("meter_status", "OK")),
                    comm_status=str(payload.get("comm_status", "OK")),
                )

                # Persist in storage
                insert_reading(reading_in)

                # Forward to asynchronous ML anomaly detection queue worker
                if self.queue_callback:
                    self.queue_callback(reading_in)

        except Exception as e:
            logger.error(f"[MQTT Error] Failed to parse message on {msg.topic}: {e}", exc_info=True)

    def start(self):
        """Start asynchronous MQTT network loop in background."""
        if not self.enabled:
            logger.info("[MQTT] Service is disabled by configuration (MQTT_ENABLED=false).")
            return

        try:
            self.client.connect_async(self.broker, self.port, keepalive=self.keepalive)
            self.client.loop_start()
            logger.info(f"[MQTT] Client loop started for {self.broker}:{self.port}")
        except Exception as e:
            logger.warning(f"[MQTT] Connection deferred/failed to {self.broker}:{self.port} ({e})")

    def stop(self):
        """Stop MQTT client loop gracefully."""
        if self.enabled:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("[MQTT] Client loop stopped.")
            except Exception as e:
                logger.error(f"[MQTT Error] Stop failed: {e}")

    def publish_telemetry(self, consumer_id: str, reading_data: Dict[str, Any], qos: int = 1) -> bool:
        """Publish smart meter reading payload to telemetry topic."""
        topic = f"tracewatt/telemetry/{consumer_id}/reading"
        payload = json.dumps(reading_data)
        try:
            info = self.client.publish(topic, payload, qos=qos)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"[MQTT Publish Error] Failed to publish to {topic}: {e}")
            return False

    def publish_alert(self, consumer_id: str, alert_data: Dict[str, Any], qos: int = 1) -> bool:
        """Publish real-time NTL anomaly alert to MQTT broker."""
        topic = f"tracewatt/alerts/{consumer_id}"
        payload = json.dumps(alert_data)
        try:
            info = self.client.publish(topic, payload, qos=qos)
            # Also broadcast on general alerts channel
            self.client.publish("tracewatt/alerts/broadcast", payload, qos=qos)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"[MQTT Alert Error] Failed to publish alert: {e}")
            return False


# Global singleton instance
mqtt_service = MQTTService()
