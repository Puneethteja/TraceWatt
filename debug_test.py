import os, sys
sys.path.insert(0, os.path.abspath('backend'))
from engine.fuzzy_logic import fuzzy_engine

print(fuzzy_engine.evaluate(drop_ratio=0.64, comm_error=0.0, meter_fault=0.0, peer_deviation=1.0))
