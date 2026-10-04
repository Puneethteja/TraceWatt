import os
import sys
from pathlib import Path

# Use isolated test database for pytest fixtures so tracewatt.db is preserved
os.environ["DATABASE_URL"] = "sqlite:///./test_tracewatt.db"

# Ensure the backend directory is on sys.path for all test modules
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
