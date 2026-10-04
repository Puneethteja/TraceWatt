import os

def _get_database_url():
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    root_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tracewatt.db"))
    return f"sqlite:///{root_db}"

DATABASE_URL = _get_database_url()
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
SEED_ON_START = os.getenv("SEED_ON_START", "false").lower() in ("true", "1", "yes")
DATA_DIR = os.getenv("DATA_DIR", "./data")
MODEL_DIR = os.getenv("MODEL_DIR", "./models")
WINDOW_ROWS = int(os.getenv("WINDOW_ROWS", "100"))
EXPECTED_INTERVAL_SECONDS = int(os.getenv("EXPECTED_INTERVAL_SECONDS", "3600"))

# MQTT Protocol Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "test.mosquitto.org")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
MQTT_TOPIC_TELEMETRY = os.getenv("MQTT_TOPIC_TELEMETRY", "tracewatt/telemetry/+/reading")
MQTT_TOPIC_ALERTS = os.getenv("MQTT_TOPIC_ALERTS", "tracewatt/alerts/#")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "tracewatt_backend_server")
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "true").lower() in ("true", "1", "yes")

