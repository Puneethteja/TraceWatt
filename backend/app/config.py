import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tracewatt.db")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
SEED_ON_START = os.getenv("SEED_ON_START", "false").lower() in ("true", "1", "yes")
DATA_DIR = os.getenv("DATA_DIR", "./data")
MODEL_DIR = os.getenv("MODEL_DIR", "./models")
WINDOW_ROWS = int(os.getenv("WINDOW_ROWS", "100"))
EXPECTED_INTERVAL_SECONDS = int(os.getenv("EXPECTED_INTERVAL_SECONDS", "3600"))
