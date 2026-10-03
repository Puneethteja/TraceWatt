"""
backend/tests/conftest.py
==========================
Shared pytest configuration and path setup for TraceWatt tests.
"""

import sys
from pathlib import Path

# Ensure the backend directory is on sys.path for all test modules
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
