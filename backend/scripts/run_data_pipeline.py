"""
backend/scripts/run_data_pipeline.py
====================================
Unified Data Pipeline for TraceWatt.

This script chains Vardhan's Phase 1, 2, and 3 data processing steps.
Puneet (or any team member) can run this to generate all required 
`data/processed/` files from the raw Kaggle datasets.

HOW TO RUN:
===========
1. Ensure raw files exist at:
   - backend/data/raw/data.csv
   - backend/data/raw/Electricity_Theft_Data.csv
2. Run from the `backend/` directory:
   python scripts/run_data_pipeline.py
"""

import sys
from pathlib import Path

# Ensure backend is in path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from datapipe.clean import clean_raw_data
from datapipe.features import build_features
from scripts.generate_synthetic import generate_synthetic_data


def main():
    print("=" * 70)
    print("TraceWatt: Unified Data Processing Pipeline")
    print("=" * 70)

    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    file_a = raw_dir / "data.csv"
    file_b = raw_dir / "Electricity_Theft_Data.csv"

    if not file_a.exists() or not file_b.exists():
        print("❌ ERROR: Raw data files not found!")
        print(f"Expected: {file_a} and {file_b}")
        print("Please ensure the Kaggle datasets are placed in the data/raw/ directory.")
        sys.exit(1)

    print("\n[Phase 1] Cleaning raw data and melting to long format...")
    clean_raw_data(
        file_a_path=str(file_a),
        file_b_path=str(file_b),
        out_dir=str(processed_dir)
    )
    print("✅ Phase 1 Complete: consumers.csv, readings.parquet, readings_demo.csv created.")

    print("\n[Phase 2] Engineering features and computing baselines...")
    build_features(
        readings_path=str(processed_dir / "readings.parquet"),
        consumers_path=str(processed_dir / "consumers.csv"),
        out_dir=str(processed_dir)
    )
    print("✅ Phase 2 Complete: features.parquet, baselines.csv created.")

    print("\n[Phase 3] Generating synthetic topology and anomaly scenarios...")
    generate_synthetic_data(
        consumers_path=str(processed_dir / "consumers.csv"),
        readings_path=str(processed_dir / "readings.parquet"),
        out_dir=str(processed_dir),
        seed=42,
        n_per_scenario=20,
        seasonal_transformers=4
    )
    print("✅ Phase 3 Complete: consumers_synthetic.csv, transformers.csv, labels.csv, synthetic_readings.parquet created.")

    print("\n" + "=" * 70)
    print("🎉 Pipeline Complete! All data/processed/ files are ready for ML training.")
    print("=" * 70)


if __name__ == "__main__":
    main()