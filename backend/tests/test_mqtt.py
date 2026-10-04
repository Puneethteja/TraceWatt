import json
from datetime import datetime, timezone
from unittest.mock import MagicMock
from app.db import init_db
from app.services.mqtt_service import MQTTService
from app.schemas import ReadingIn


def test_mqtt_service_initialization():
    service = MQTTService(broker="test.mosquitto.org", port=1883)
    assert service.broker == "test.mosquitto.org"
    assert service.port == 1883
    assert service.is_connected is False


def test_mqtt_message_parsing_and_queue():
    init_db()
    service = MQTTService()
    callback_mock = MagicMock()
    service.set_queue_callback(callback_mock)

    class MockMsg:
        topic = "tracewatt/telemetry/C100/reading"
        payload = json.dumps({
            "consumer_id": "C100",
            "ts": datetime.now(timezone.utc).isoformat(),
            "kwh": 1.45,
            "voltage": 231.2,
            "current": 6.9,
            "power_kw": 1.45,
            "meter_status": "OK",
            "comm_status": "OK"
        }).encode("utf-8")

    service._on_message(None, None, MockMsg())
    
    assert callback_mock.called
    reading_arg = callback_mock.call_args[0][0]
    assert isinstance(reading_arg, ReadingIn)
    assert reading_arg.consumer_id == "C100"
    assert reading_arg.kwh == 1.45
    assert reading_arg.voltage == 231.2
