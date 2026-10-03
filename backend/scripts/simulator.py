"""
backend/scripts/simulator.py
============================
Phase-5 Virtual IoT Monitoring Simulator for TraceWatt (Deliverable D6).

Reads synthetic anomaly scenarios from Phase 3 and streams them as live
`POST /readings` requests to the FastAPI backend, simulating real-time smart meters.

HOW TO RUN:
===========
1. Start the FastAPI backend server first (in a separate terminal):
     uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

2. Run this simulator script:
     python scripts/simulator.py --api-url http://localhost:8000/readings --num-consumers 50 --delay-ms 50

3. To test the streaming logic without an active backend server, use --dry-run:
     python scripts/simulator.py --num-consumers 10 --delay-ms 10 --dry-run --max-readings 100
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import requests

# ---------------------------------------------------------------------------
# Assumptions (printed at runtime)
# ---------------------------------------------------------------------------

ASSUMPTIONS = [
    "A1. Voltage: Simulated as nominal 230V +/- 5% Gaussian noise, bounded within grid tolerance [207V, 253V].",
    "A2. Current & Power: Derived from active daily usage: power_kw = (kwh / 24) * 2.5, current = (power_kw * 1000) / (voltage * 0.9). Set to 0.0 if kwh is null/zero.",
    "A3. Comm Failure Nulls: When comm_status == 'FAILED', kwh is sent as null (None in JSON) to test backend gap detection per PRD Section 7.",
    "A4. Global Chronological Interleaving: Readings sorted by (ts, consumer_id) to simulate a real-time AMI collector feed.",
    "A5. Deterministic Telemetry: Fixed SeedSequence generates reproducible electrical telemetry across simulation runs.",
]


def select_diverse_consumers(
    labels_path: Path,
    num_consumers: int,
    seed: int,
) -> tuple[list[str], dict[str, int]]:
    """
    Selects a balanced subset of consumers across all 6 scenarios.
    """
    labels_df = pd.read_csv(labels_path)
    rng = np.random.default_rng(seed)

    scenarios = [
        "Theft/Tampering",
        "Meter Malfunction",
        "Communication Failure",
        "Legitimate Abnormal",
        "Seasonal Variation",
        "Normal",
    ]

    selected_cids = []
    scenario_counts: dict[str, int] = {}

    # Target allocation: up to 10% each for anomaly scenarios, remainder Normal
    n_anom = max(1, int(round(num_consumers * 0.10))) if num_consumers >= 10 else 1

    for sc in scenarios[:-1]:
        avail = labels_df[labels_df["true_cause"] == sc]["consumer_id"].tolist()
        rng.shuffle(avail)
        pick = avail[:n_anom]
        selected_cids.extend(pick)
        scenario_counts[sc] = len(pick)

    # Fill remainder with Normal consumers
    remaining = num_consumers - len(selected_cids)
    avail_normal = labels_df[labels_df["true_cause"] == "Normal"]["consumer_id"].tolist()
    rng.shuffle(avail_normal)
    normal_pick = avail_normal[: max(1, remaining)]
    selected_cids.extend(normal_pick)
    scenario_counts["Normal"] = len(normal_pick)

    # Trim to exact num_consumers if needed
    selected_cids = selected_cids[:num_consumers]
    return selected_cids, scenario_counts


def build_reading_payload(
    row: pd.Series,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """
    Constructs the ReadingIn payload for the FastAPI endpoint.
    """
    cid = str(row["consumer_id"])
    ts = str(row["ts"])
    comm_status = str(row["comm_status"])
    meter_status = str(row["meter_status"])

    # Determine kwh value
    raw_kwh = row["generated_kwh"]
    if pd.isna(raw_kwh) or comm_status == "FAILED":
        kwh: float | None = None
    else:
        kwh = round(float(raw_kwh), 4)

    # Simulate realistic electrical parameters
    voltage = round(float(np.clip(rng.normal(230.0, 4.0), 207.0, 253.0)), 1)

    if kwh is not None and kwh > 0.0:
        power_kw = round(float((kwh / 24.0) * 2.5), 2)
        current = round(float((power_kw * 1000.0) / (voltage * 0.9)), 2)
    else:
        power_kw = 0.0
        current = 0.0

    return {
        "consumer_id": cid,
        "ts": ts,
        "kwh": kwh,
        "voltage": voltage,
        "current": current,
        "power_kw": power_kw,
        "meter_status": meter_status,
        "comm_status": comm_status,
    }


def run_simulator(
    api_url: str = "http://localhost:8000/readings",
    num_consumers: int = 50,
    delay_ms: int = 100,
    seed: int = 42,
    data_dir: str = "data/processed",
    dry_run: bool = False,
    max_readings: int | None = None,
) -> dict[str, Any]:
    """
    Runs the IoT smart meter stream simulation.
    """
    p_data = Path(data_dir)
    readings_parquet = p_data / "synthetic_readings.parquet"
    labels_csv = p_data / "labels.csv"

    if not readings_parquet.exists() or not labels_csv.exists():
        raise FileNotFoundError(
            f"Required files not found in {data_dir}. Run generate_synthetic.py first."
        )

    # 1. Select diverse cohort of consumers
    selected_cids, scenario_counts = select_diverse_consumers(
        labels_path=labels_csv,
        num_consumers=num_consumers,
        seed=seed,
    )

    print("\n[Scenario Cohort Distribution]")
    for sc, count in scenario_counts.items():
        print(f"  {sc:25s} : {count:3d} consumers")

    # 2. Filter readings via PyArrow
    print(f"\n[Loading readings for {len(selected_cids)} selected consumers ...]")
    table = pq.read_table(readings_parquet, filters=[("consumer_id", "in", selected_cids)])
    df = table.to_pandas()

    # 3. Interleave readings chronologically by date
    df = df.sort_values(["ts", "consumer_id"], kind="mergesort").reset_index(drop=True)
    if max_readings is not None:
        df = df.iloc[:max_readings].copy()

    total_readings = len(df)
    print(f"Total readings to stream : {total_readings:,}")
    print(f"Target API endpoint      : {api_url}")
    print(f"Per-reading delay        : {delay_ms} ms")
    if dry_run:
        print("Mode                     : DRY RUN (no network HTTP requests)\n")
    else:
        print("Mode                     : LIVE STREAM\n")

    # 4. Stream readings
    rng = np.random.default_rng(np.random.SeedSequence([seed, 777]))
    http_session = requests.Session()

    success_count = 0
    fail_count = 0
    t_start = time.time()
    delay_sec = delay_ms / 1000.0

    print("=" * 65)
    print("STREAMING STARTED")
    print("=" * 65)

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        payload = build_reading_payload(row, rng)

        if dry_run:
            success_count += 1
        else:
            try:
                resp = http_session.post(api_url, json=payload, timeout=2.0)
                if resp.status_code in (200, 201, 202):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception:
                fail_count += 1

        if delay_sec > 0:
            time.sleep(delay_sec)

        # Progress reporting
        if i % 100 == 0 or i == total_readings or (total_readings <= 100 and i % 10 == 0):
            elapsed = time.time() - t_start
            rate = i / elapsed if elapsed > 0 else 0
            ts_val = payload["ts"]
            print(
                f"Posted {i:6d}/{total_readings} | Success: {success_count:6d} | Fail: {fail_count:3d} | "
                f"Date: {ts_val} | Speed: {rate:.1f} rec/s"
            )

    t_total = time.time() - t_start
    print("\n" + "=" * 65)
    print("STREAMING COMPLETED")
    print("=" * 65)
    print(f"Total streamed    : {total_readings:,} readings")
    print(f"Successful POSTs  : {success_count:,}")
    print(f"Failed POSTs      : {fail_count:,}")
    print(f"Total Time        : {t_total:.2f} s")
    print(f"Average Rate      : {total_readings / t_total:.1f} readings/sec" if t_total > 0 else "N/A")

    return {
        "total_readings": total_readings,
        "success_count": success_count,
        "fail_count": fail_count,
        "elapsed_sec": t_total,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TraceWatt Virtual IoT Smart Meter Stream Simulator")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000/readings", help="Target API URL")
    parser.add_argument("--num-consumers", type=int, default=50, help="Number of consumers to stream")
    parser.add_argument("--delay-ms", type=int, default=100, help="Delay between POSTs in milliseconds")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--data-dir", type=str, default="data/processed", help="Data processed directory")
    parser.add_argument("--dry-run", action="store_true", help="Simulate locally without sending HTTP requests")
    parser.add_argument("--max-readings", type=int, default=None, help="Optional maximum number of readings to stream")
    args = parser.parse_args()

    print("=" * 65)
    print("TraceWatt - Phase 5: Virtual IoT Monitoring Simulator")
    print("=" * 65)

    print("\n[Assumptions]")
    for a in ASSUMPTIONS:
        print(f"  {a}")

    run_simulator(
        api_url=args.api_url,
        num_consumers=args.num_consumers,
        delay_ms=args.delay_ms,
        seed=args.seed,
        data_dir=args.data_dir,
        dry_run=args.dry_run,
        max_readings=args.max_readings,
    )
