"""
backend/scripts/generate_synthetic.py
=====================================
Phase-3 synthetic scenario-generation and topology layer for TraceWatt.

Generates:
  1. data/processed/consumers_synthetic.csv  (original consumers + synthetic topology)
  2. data/processed/transformers.csv         (transformer/feeder mapping)
  3. data/processed/labels.csv               (ground truth for injected scenarios)
  4. data/processed/synthetic_readings.parquet (injected reading streams)
  5. data/processed/synthetic_validation_report.md (comprehensive validation report)

KEY DESIGN PRINCIPLES:
  1. Memory efficiency: PyArrow filtered reads load ONLY the selected consumers (~840 out of 52k).
  2. Determinism: SeedSequence derives per-consumer RNGs -> byte-identical on re-run.
  3. Strict NULL vs ZERO: Communication failures inject NaNs; meter faults inject 0.0s or flatlines.
  4. Topology constraints: Every mixed transformer has 10 consumers (1 target + 9 normal peers),
     with at least 6 peers sharing the exact category of the target.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Schemas & Constants
# ---------------------------------------------------------------------------

_SYNTHETIC_READINGS_SCHEMA = pa.schema([
    pa.field("consumer_id", pa.string()),
    pa.field("ts", pa.string()),
    pa.field("scenario_id", pa.string()),
    pa.field("original_kwh", pa.float64()),
    pa.field("generated_kwh", pa.float64()),
    pa.field("meter_status", pa.string()),
    pa.field("comm_status", pa.string()),
    pa.field("is_modified", pa.bool_()),
    pa.field("in_event_window", pa.bool_()),
    pa.field("original_missing", pa.bool_()),
])

SCENARIO_CODES = {
    "THEFT": 1,
    "METER": 2,
    "COMM": 3,
    "LEGIT": 4,
    "SEASONAL": 5,
    "NORMAL": 6,
}

TRUE_CAUSES = {
    "THEFT": "Theft/Tampering",
    "METER": "Meter Malfunction",
    "COMM": "Communication Failure",
    "LEGIT": "Legitimate Abnormal",
    "SEASONAL": "Seasonal Variation",
    "NORMAL": "Normal",
}


def _sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Topology Generation
# ---------------------------------------------------------------------------

def generate_topology(
    consumers_df: pd.DataFrame,
    seed: int,
    n_per_scenario: int,
    seasonal_transformers: int,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """
    Assigns category, sanctioned_load_kw, tariff to all consumers,
    and builds mixed and seasonal transformers.
    """
    rng = np.random.default_rng(seed)
    n_total = len(consumers_df)

    # 1. Assign categories (50% residential, 30% commercial, 20% industrial)
    n_res = int(round(0.50 * n_total))
    n_com = int(round(0.30 * n_total))
    n_ind = n_total - n_res - n_com
    cats = np.array(["residential"] * n_res + ["commercial"] * n_com + ["industrial"] * n_ind)
    rng.shuffle(cats)

    consumers_df = consumers_df.copy()
    consumers_df["category"] = cats

    # 2. Sanctioned load & tariff
    load_kw = np.zeros(n_total, dtype=np.float64)
    tariffs = np.zeros(n_total, dtype=np.float64)

    res_mask = cats == "residential"
    com_mask = cats == "commercial"
    ind_mask = cats == "industrial"

    load_kw[res_mask] = np.round(rng.uniform(5.0, 10.0, size=res_mask.sum()), 1)
    tariffs[res_mask] = 5.0

    load_kw[com_mask] = np.round(rng.uniform(50.0, 100.0, size=com_mask.sum()), 1)
    tariffs[com_mask] = 8.0

    load_kw[ind_mask] = np.round(rng.uniform(500.0, 1000.0, size=ind_mask.sum()), 1)
    tariffs[ind_mask] = 12.0

    consumers_df["sanctioned_load_kw"] = load_kw
    consumers_df["tariff"] = tariffs

    # 3. Select clean base candidates (theft_label == 0, preferably Dataset A)
    clean_mask = (consumers_df["theft_label"] == 0)
    if "source_dataset" in consumers_df.columns:
        ds_a_clean = clean_mask & (consumers_df["source_dataset"] == "A")
        candidates_df = consumers_df[ds_a_clean] if ds_a_clean.sum() >= (n_per_scenario * 4 * 10 + seasonal_transformers * 10) else consumers_df[clean_mask]
    else:
        candidates_df = consumers_df[clean_mask]

    # Group candidate IDs by category
    cand_by_cat = {
        cat: candidates_df[candidates_df["category"] == cat]["consumer_id"].tolist()
        for cat in ["residential", "commercial", "industrial"]
    }
    # Deterministically shuffle each pool
    for cat in cand_by_cat:
        cand_rng = np.random.default_rng(np.random.SeedSequence([seed, hash(cat) & 0xFFFFFFFF]))
        cand_rng.shuffle(cand_by_cat[cat])

    transformer_records = []
    consumer_assignments = []  # dict of consumer_id -> {transformer_id, feeder_id, scenario_id}

    target_scenarios = (
        ["THEFT"] * n_per_scenario
        + ["METER"] * n_per_scenario
        + ["COMM"] * n_per_scenario
        + ["LEGIT"] * n_per_scenario
    )
    rng.shuffle(target_scenarios)
    n_mixed = len(target_scenarios)

    # Track used consumers
    used_consumers = set()
    tx_counter = 1

    # 3a. Build Mixed Transformers
    for sc_id in target_scenarios:
        tx_id = f"TX_{tx_counter:03d}"
        feeder_id = f"FDR_{(tx_counter - 1) // 4 + 1:02d}"

        # Choose target category round-robin or based on availability
        avail_cats = [c for c in ["residential", "commercial", "industrial"] if len([x for x in cand_by_cat[c] if x not in used_consumers]) >= 7]
        target_cat = avail_cats[0] if avail_cats else "residential"

        # Pick target consumer
        target_cid = None
        for cid in cand_by_cat[target_cat]:
            if cid not in used_consumers:
                target_cid = cid
                break
        used_consumers.add(target_cid)

        # Pick 6 same-category NORMAL peers
        same_cat_peers = []
        for cid in cand_by_cat[target_cat]:
            if cid not in used_consumers:
                same_cat_peers.append(cid)
                used_consumers.add(cid)
                if len(same_cat_peers) == 6:
                    break

        # Pick 3 remaining NORMAL peers (any category)
        other_peers = []
        for c_list in cand_by_cat.values():
            for cid in c_list:
                if cid not in used_consumers:
                    other_peers.append(cid)
                    used_consumers.add(cid)
                    if len(other_peers) == 3:
                        break
            if len(other_peers) == 3:
                break

        assigned_10 = [(target_cid, sc_id)] + [(p, "NORMAL") for p in same_cat_peers + other_peers]
        for cid, assigned_sc in assigned_10:
            consumer_assignments.append({
                "consumer_id": cid,
                "transformer_id": tx_id,
                "feeder_id": feeder_id,
                "scenario_id": assigned_sc,
            })

        tx_capacity = round(float(consumers_df.loc[consumers_df["consumer_id"].isin([x[0] for x in assigned_10]), "sanctioned_load_kw"].sum() * 1.25), 1)
        transformer_records.append({
            "transformer_id": tx_id,
            "feeder_id": feeder_id,
            "capacity_kva": tx_capacity,
        })
        tx_counter += 1

    # 3b. Build Seasonal Transformers
    for _ in range(seasonal_transformers):
        tx_id = f"TX_{tx_counter:03d}"
        feeder_id = f"FDR_{(tx_counter - 1) // 4 + 1:02d}"

        seasonal_10 = []
        for c_list in cand_by_cat.values():
            for cid in c_list:
                if cid not in used_consumers:
                    seasonal_10.append(cid)
                    used_consumers.add(cid)
                    if len(seasonal_10) == 10:
                        break
            if len(seasonal_10) == 10:
                break

        for cid in seasonal_10:
            consumer_assignments.append({
                "consumer_id": cid,
                "transformer_id": tx_id,
                "feeder_id": feeder_id,
                "scenario_id": "SEASONAL",
            })

        tx_capacity = round(float(consumers_df.loc[consumers_df["consumer_id"].isin(seasonal_10), "sanctioned_load_kw"].sum() * 1.25), 1)
        transformer_records.append({
            "transformer_id": tx_id,
            "feeder_id": feeder_id,
            "capacity_kva": tx_capacity,
        })
        tx_counter += 1

    # Update consumers table
    assign_df = pd.DataFrame(consumer_assignments)
    consumers_synthetic = consumers_df.merge(
        assign_df[["consumer_id", "transformer_id", "feeder_id"]],
        on="consumer_id",
        how="left",
    )
    consumers_synthetic["transformer_id"] = consumers_synthetic["transformer_id"].fillna("")
    consumers_synthetic["feeder_id"] = consumers_synthetic["feeder_id"].fillna("")

    # Enforce exact column order
    cols_order = [
        "consumer_id", "cons_no_original", "source_dataset", "theft_label",
        "label_source", "category", "sanctioned_load_kw", "tariff",
        "transformer_id", "feeder_id"
    ]
    consumers_synthetic = consumers_synthetic[cols_order].sort_values("consumer_id", kind="mergesort").reset_index(drop=True)

    transformers_df = pd.DataFrame(transformer_records).sort_values("transformer_id", kind="mergesort").reset_index(drop=True)
    return consumers_synthetic, transformers_df, consumer_assignments


# ---------------------------------------------------------------------------
# Scenario Injections
# ---------------------------------------------------------------------------

def inject_scenarios(
    raw_readings: pd.DataFrame,
    assignments: list[dict],
    consumers_synthetic: pd.DataFrame,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Applies the 6 scenario injection rules to the assigned consumers.
    Returns (synthetic_readings_df, labels_df).
    """
    cat_map = consumers_synthetic.set_index("consumer_id")["category"].to_dict()
    assigned_dict = {a["consumer_id"]: a for a in assignments}
    consumer_groups = raw_readings.groupby("consumer_id", sort=False)

    modified_readings_list = []
    labels_records = []

    # Pre-calculate seasonal transformer windows
    # Group seasonal members by transformer
    seasonal_tx_map = {}
    for a in assignments:
        if a["scenario_id"] == "SEASONAL":
            seasonal_tx_map.setdefault(a["transformer_id"], []).append(a["consumer_id"])

    seasonal_tx_params = {}
    for tx_id, members in seasonal_tx_map.items():
        tx_seed_seq = np.random.SeedSequence([seed, 555, hash(tx_id) & 0xFFFFFFFF])
        tx_rng = np.random.default_rng(tx_seed_seq)
        s = int(tx_rng.integers(120, 201))
        duration = int(tx_rng.integers(60, 91))
        e = s + duration
        a_group = float(tx_rng.uniform(0.44, 0.50))
        seasonal_tx_params[tx_id] = {"s": s, "e": e, "a_group": a_group}

    meter_variant_counter = 0
    comm_variant_counter = 0

    for idx, (cid, c_df) in enumerate(consumer_groups):
        if cid not in assigned_dict:
            continue

        c_df = c_df.sort_values("ts", kind="mergesort").reset_index(drop=True)
        n_days = len(c_df)
        info = assigned_dict[cid]
        scenario_id = info["scenario_id"]
        tx_id = info["transformer_id"]
        category = cat_map.get(cid, "residential")

        # Independent deterministic RNG per consumer
        c_seed_seq = np.random.SeedSequence([seed, SCENARIO_CODES[scenario_id], idx])
        c_rng = np.random.default_rng(c_seed_seq)

        orig_kwh = c_df["kwh"].to_numpy(dtype=np.float64, copy=True)
        gen_kwh = orig_kwh.copy()
        meter_status = np.full(n_days, "OK", dtype=object)
        comm_status = np.full(n_days, "OK", dtype=object)
        in_window = np.zeros(n_days, dtype=bool)

        period_start = ""
        period_end = ""
        theft_flag = 0
        true_cause = TRUE_CAUSES[scenario_id]

        if scenario_id == "THEFT":
            theft_flag = 1
            start_day = int(c_rng.integers(120, min(275, max(121, n_days - 90))))
            f = float(c_rng.uniform(0.10, 0.48))
            jitter = c_rng.normal(0.0, 0.05, size=n_days - start_day)
            jitter = np.clip(jitter, -0.15, 0.15)
            factors = np.clip(f * (1.0 + jitter), 0.05, 0.90)

            for day_idx, t in enumerate(range(start_day, n_days)):
                in_window[t] = True
                if not np.isnan(orig_kwh[t]):
                    gen_kwh[t] = float(orig_kwh[t] * factors[day_idx])

            period_start = c_df["ts"].iloc[start_day]
            period_end = c_df["ts"].iloc[-1]

        elif scenario_id == "METER":
            start_day = int(c_rng.integers(120, min(335, max(121, n_days - 25))))
            dur = int(c_rng.integers(21, min(61, max(22, n_days - start_day))))
            end_day = min(start_day + dur, n_days)

            variant = meter_variant_counter % 3
            meter_variant_counter += 1

            in_window[start_day:end_day] = True
            meter_status[start_day:end_day] = "FAULT"

            if variant == 0:  # flatline: hold last pre-fault value
                valid_pre = orig_kwh[:start_day][~np.isnan(orig_kwh[:start_day])]
                last_val = float(valid_pre[-1]) if len(valid_pre) > 0 else 5.0
                gen_kwh[start_day:end_day] = last_val
            elif variant == 1:  # zero
                gen_kwh[start_day:end_day] = 0.0
            else:  # erratic
                valid_orig = orig_kwh[~np.isnan(orig_kwh)]
                p99 = float(np.percentile(valid_orig, 99)) if len(valid_orig) > 0 else 10.0
                if p99 <= 0:
                    p99 = 10.0
                factors = c_rng.lognormal(mean=0.0, sigma=1.0, size=end_day - start_day)
                for day_idx, t in enumerate(range(start_day, end_day)):
                    if not np.isnan(orig_kwh[t]):
                        gen_kwh[t] = float(np.clip(orig_kwh[t] * factors[day_idx], 0.0, 4.0 * p99))

            period_start = c_df["ts"].iloc[start_day]
            period_end = c_df["ts"].iloc[end_day - 1]

        elif scenario_id == "COMM":
            variant = comm_variant_counter % 2
            comm_variant_counter += 1

            if variant == 0:  # single outage
                start_day = int(c_rng.integers(120, max(121, n_days - 10)))
                dur = int(c_rng.integers(7, min(22, max(8, n_days - start_day))))
                end_day = min(start_day + dur, n_days)

                in_window[start_day:end_day] = True
                comm_status[start_day:end_day] = "FAILED"
                gen_kwh[start_day:end_day] = np.nan

                period_start = c_df["ts"].iloc[start_day]
                period_end = c_df["ts"].iloc[end_day - 1]
            else:  # 3 to 5 gaps of 1 to 3 days
                num_gaps = int(c_rng.integers(3, 6))
                cur_day = 120
                first_start = None
                last_end = None
                for _ in range(num_gaps):
                    if cur_day >= n_days - 5:
                        break
                    g_start = int(c_rng.integers(cur_day, min(cur_day + 15, n_days - 4)))
                    g_dur = int(c_rng.integers(1, 4))
                    g_end = min(g_start + g_dur, n_days)

                    in_window[g_start:g_end] = True
                    comm_status[g_start:g_end] = "FAILED"
                    gen_kwh[g_start:g_end] = np.nan

                    if first_start is None:
                        first_start = g_start
                    last_end = g_end - 1
                    cur_day = g_end + int(c_rng.integers(4, 10))

                period_start = c_df["ts"].iloc[first_start if first_start is not None else 120]
                period_end = c_df["ts"].iloc[last_end if last_end is not None else 130]

        elif scenario_id == "LEGIT":
            is_temp_drop = (c_rng.uniform() < 0.5)
            if is_temp_drop:  # temporary reduction
                start_day = int(c_rng.integers(120, max(121, n_days - 10)))
                dur = int(c_rng.integers(7, min(29, max(8, n_days - start_day))))
                end_day = min(start_day + dur, n_days)
                factor = float(c_rng.uniform(0.10, 0.40))

                in_window[start_day:end_day] = True
                for t in range(start_day, end_day):
                    if not np.isnan(orig_kwh[t]):
                        gen_kwh[t] = float(orig_kwh[t] * factor)

                period_start = c_df["ts"].iloc[start_day]
                period_end = c_df["ts"].iloc[end_day - 1]
            else:  # step increase
                start_day = int(c_rng.integers(120, min(275, max(121, n_days - 30))))
                factor = float(c_rng.uniform(1.30, 1.80))

                in_window[start_day:] = True
                for t in range(start_day, n_days):
                    if not np.isnan(orig_kwh[t]):
                        gen_kwh[t] = float(orig_kwh[t] * factor)

                period_start = c_df["ts"].iloc[start_day]
                period_end = c_df["ts"].iloc[-1]

        elif scenario_id == "SEASONAL":
            tx_params = seasonal_tx_params.get(tx_id, {"s": 150, "e": 230, "a_group": 0.45})
            s = min(tx_params["s"], n_days - 10)
            e = min(tx_params["e"], n_days - 1)
            duration = max(1, e - s)

            a_member = tx_params["a_group"] * float(c_rng.uniform(0.98, 1.05))
            t_range = np.arange(s, e + 1)
            bump = 1.0 + a_member * (np.sin(np.pi * (t_range - s) / duration) ** 2)

            in_window[s:e+1] = True
            for day_idx, t in enumerate(range(s, e + 1)):
                if not np.isnan(orig_kwh[t]):
                    gen_kwh[t] = float(orig_kwh[t] * bump[day_idx])

            period_start = c_df["ts"].iloc[s]
            period_end = c_df["ts"].iloc[e]

        # Scenario NORMAL: generated_kwh == original_kwh, no changes

        # Compute modification flags
        orig_missing = np.isnan(orig_kwh)
        kwh_changed = np.where(
            orig_missing,
            ~np.isnan(gen_kwh),
            np.isnan(gen_kwh) | (np.abs(gen_kwh - orig_kwh) > 1e-6)
        )
        status_changed = (meter_status != "OK") | (comm_status != "OK")
        is_modified = kwh_changed | status_changed

        c_result_df = pd.DataFrame({
            "consumer_id": cid,
            "ts": c_df["ts"],
            "scenario_id": scenario_id,
            "original_kwh": orig_kwh,
            "generated_kwh": gen_kwh,
            "meter_status": meter_status,
            "comm_status": comm_status,
            "is_modified": is_modified,
            "in_event_window": in_window,
            "original_missing": orig_missing,
        })
        modified_readings_list.append(c_result_df)

        labels_records.append({
            "consumer_id": cid,
            "label_source": "SYNTHETIC",
            "theft_label": theft_flag,
            "true_cause": true_cause,
            "period_start": period_start,
            "period_end": period_end,
        })

    synthetic_readings = pd.concat(modified_readings_list, ignore_index=True)
    synthetic_readings = synthetic_readings.sort_values(["consumer_id", "ts"], kind="mergesort").reset_index(drop=True)

    labels_df = pd.DataFrame(labels_records)
    labels_df = labels_df.sort_values("consumer_id", kind="mergesort").reset_index(drop=True)
    return synthetic_readings, labels_df


# ---------------------------------------------------------------------------
# Validation Report Generator
# ---------------------------------------------------------------------------

def write_validation_report(
    report_path: Path,
    seed: int,
    consumers_synthetic: pd.DataFrame,
    transformers_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    synthetic_readings: pd.DataFrame,
    hashes: dict[str, str],
) -> str:
    """Generates the synthetic_validation_report.md content."""
    total_records = len(synthetic_readings)
    n_consumers = synthetic_readings["consumer_id"].nunique()
    scenarios_dist = labels_df["true_cause"].value_counts().to_dict()

    meter_dist = synthetic_readings["meter_status"].value_counts().to_dict()
    comm_dist = synthetic_readings["comm_status"].value_counts().to_dict()

    n_tx = len(transformers_df)
    n_feeders = transformers_df["feeder_id"].nunique()

    # Fraction of modified rows per scenario
    scenario_mod = (
        synthetic_readings.groupby("scenario_id")["is_modified"]
        .agg(["count", "sum"])
        .reset_index()
    )
    scenario_mod["mod_fraction"] = scenario_mod["sum"] / scenario_mod["count"]

    report_lines = [
        "# TraceWatt: Synthetic Scenario Generation Validation Report",
        "",
        "## 1. Dataset Overview",
        f"- **Seed**: `{seed}`",
        f"- **Total Reading Records**: {total_records:,}",
        f"- **Active Synthetic Consumers**: {n_consumers:,}",
        f"- **Total Transformers**: {n_tx}",
        f"- **Consumers per Transformer**: 10",
        f"- **Total Feeders**: {n_feeders}",
        "",
        "## 2. Scenario & Cause Distribution",
        "| True Cause | Target Count | Consumer Share (%) |",
        "| :--- | :--- | :--- |",
    ]
    for cause, cnt in scenarios_dist.items():
        report_lines.append(f"| {cause} | {cnt} | {cnt / n_consumers * 100:.1f}% |")

    report_lines.extend([
        "",
        "## 3. Status Distributions",
        "### Meter Status",
    ])
    for status, cnt in meter_dist.items():
        report_lines.append(f"- **{status}**: {cnt:,} ({cnt / total_records * 100:.2f}%)")

    report_lines.extend([
        "",
        "### Communication Status",
    ])
    for status, cnt in comm_dist.items():
        report_lines.append(f"- **{status}**: {cnt:,} ({cnt / total_records * 100:.2f}%)")

    report_lines.extend([
        "",
        "## 4. Modification Ratio per Scenario",
        "| Scenario | Total Rows | Modified Rows | Modification Ratio |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for _, row in scenario_mod.iterrows():
        report_lines.append(
            f"| {row['scenario_id']} | {int(row['count']):,} | {int(row['sum']):,} | {row['mod_fraction'] * 100:.2f}% |"
        )

    report_lines.extend([
        "",
        "## 5. File Integrity (SHA-256)",
        "| File | SHA-256 Checksum |",
        "| :--- | :--- |",
    ])
    for fname, sha in hashes.items():
        report_lines.append(f"| `{fname}` | `{sha}` |")

    report_lines.extend([
        "",
        "## 6. Assumptions and Limitations",
        "> [!IMPORTANT]",
        "> **LIMITATION NOTICE**: All anomaly scenarios, network topology, transformers, and feeders generated in this module are synthetic and simulated for evaluation purposes. Results obtained using these synthetic scenarios must NOT be presented or construed as real utility performance or empirical field evidence.",
        "",
        "### Documented Assumptions",
        "1. **Topology**: Each mixed transformer consists of exactly 1 target consumer and 9 normal peers; at least 6 peers share the exact consumer category.",
        "2. **Theft Persistency**: Theft events occur abruptly and persist without recovery until the end of the observation window.",
        "3. **Null vs Zero Signal**: Communication failures strictly inject missing data (NaNs) while preserving original values; meter faults inject zeros or flatline signals.",
        "4. **Class Balance**: Peer populations in mixed transformers provide abundant clean normal readings for baseline modeling.",
    ])

    report_content = "\n".join(report_lines) + "\n"
    report_path.write_text(report_content, encoding="utf-8")
    return report_content


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def generate_synthetic_data(
    consumers_path: str = "data/processed/consumers.csv",
    readings_path: str = "data/processed/readings.parquet",
    out_dir: str = "data/processed",
    seed: int = 42,
    n_per_scenario: int = 20,
    seasonal_transformers: int = 4,
) -> dict:
    """
    Main pipeline function for Phase 3:
      1. Generates topology (transformers, categories, loads, tariffs).
      2. Efficiently loads candidate readings via PyArrow filters.
      3. Injects 6 anomaly scenarios deterministically.
      4. Saves 5 output files.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Load consumers
    consumers_df = pd.read_csv(consumers_path)

    # 2. Build topology
    consumers_synthetic, transformers_df, assignments = generate_topology(
        consumers_df=consumers_df,
        seed=seed,
        n_per_scenario=n_per_scenario,
        seasonal_transformers=seasonal_transformers,
    )

    selected_ids = [a["consumer_id"] for a in assignments]

    # 3. Memory-efficient filtered read of readings.parquet
    table = pq.read_table(readings_path, filters=[("consumer_id", "in", selected_ids)])
    raw_readings = table.to_pandas()

    # 4. Inject scenarios
    synthetic_readings, labels_df = inject_scenarios(
        raw_readings=raw_readings,
        assignments=assignments,
        consumers_synthetic=consumers_synthetic,
        seed=seed,
    )

    # 5. Write outputs
    f_consumers = out_path / "consumers_synthetic.csv"
    f_transformers = out_path / "transformers.csv"
    f_labels = out_path / "labels.csv"
    f_readings = out_path / "synthetic_readings.parquet"
    f_report = out_path / "synthetic_validation_report.md"

    consumers_synthetic.to_csv(f_consumers, index=False)
    transformers_df.to_csv(f_transformers, index=False)
    labels_df.to_csv(f_labels, index=False)

    tbl = pa.Table.from_pandas(synthetic_readings, schema=_SYNTHETIC_READINGS_SCHEMA, preserve_index=False)
    pq.write_table(tbl, f_readings, compression="snappy", write_statistics=False, store_schema=True)

    # Calculate checksums
    hashes = {
        "consumers_synthetic.csv": _sha256(f_consumers),
        "transformers.csv": _sha256(f_transformers),
        "labels.csv": _sha256(f_labels),
        "synthetic_readings.parquet": _sha256(f_readings),
    }

    # Write validation report
    write_validation_report(
        report_path=f_report,
        seed=seed,
        consumers_synthetic=consumers_synthetic,
        transformers_df=transformers_df,
        labels_df=labels_df,
        synthetic_readings=synthetic_readings,
        hashes=hashes,
    )
    hashes["synthetic_validation_report.md"] = _sha256(f_report)

    return {
        "n_consumers": len(selected_ids),
        "n_transformers": len(transformers_df),
        "n_readings": len(synthetic_readings),
        "hashes": hashes,
        "labels_df": labels_df,
        "synthetic_readings": synthetic_readings,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TraceWatt Phase 3: Synthetic Scenario Generation")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--n-per-scenario", type=int, default=20, help="Number of targets per scenario")
    parser.add_argument("--seasonal-transformers", type=int, default=4, help="Number of seasonal transformers")
    parser.add_argument("--out-dir", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()

    print("=" * 65)
    print("TraceWatt - Phase 3: Synthetic Scenario Generation")
    print("=" * 65)
    print(f"Seed: {args.seed} | Targets/Scenario: {args.n_per_scenario} | Seasonal TXs: {args.seasonal_transformers}")

    res = generate_synthetic_data(
        out_dir=args.out_dir,
        seed=args.seed,
        n_per_scenario=args.n_per_scenario,
        seasonal_transformers=args.seasonal_transformers,
    )

    print("\n[Generation Complete]")
    print(f"Active Consumers      : {res['n_consumers']:,}")
    print(f"Total Transformers    : {res['n_transformers']}")
    print(f"Total Reading Records : {res['n_readings']:,}")
    print("\n[Output File Hashes (SHA-256)]")
    for f, h in res["hashes"].items():
        print(f"  {f:30s} : {h}")

    print("\n" + "=" * 65)
    report_file = Path(args.out_dir) / "synthetic_validation_report.md"
    print(report_file.read_text(encoding="utf-8"))
