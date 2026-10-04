import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import DATABASE_URL, DATA_DIR
from app.db import init_db
from app.models import Feeder, Transformer, Consumer, Reading, Baseline, Case, Alert, FeederSummary

def seed_database(force: bool = False):
    print("[Seed] Initializing database tables...")
    init_db()

    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        if force:
            print("[Seed] Force flag enabled: clearing existing data...")
            db.query(Alert).delete()
            db.query(Case).delete()
            db.query(Reading).delete()
            db.query(Baseline).delete()
            db.query(Consumer).delete()
            db.query(Transformer).delete()
            db.query(FeederSummary).delete()
            db.query(Feeder).delete()
            db.commit()

        # Check if consumers already exist
        existing_consumers_count = db.query(Consumer).count()
        if existing_consumers_count > 0:
            print(f"[Seed] Database already contains {existing_consumers_count} consumers. Skipping seed.")
            return

        # Robustly locate processed data directory
        processed_candidates = [
            os.path.join(DATA_DIR, "processed"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "data", "processed")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")),
        ]
        processed_dir = None
        for cand in processed_candidates:
            if os.path.exists(os.path.join(cand, "consumers_synthetic.csv")):
                processed_dir = cand
                break
        if not processed_dir:
            processed_dir = os.path.join(DATA_DIR, "processed")

        consumers_csv = os.path.join(processed_dir, "consumers_synthetic.csv")
        labels_csv = os.path.join(processed_dir, "labels.csv")
        readings_parquet = os.path.join(processed_dir, "synthetic_readings.parquet")

        if not os.path.exists(consumers_csv):
            print(f"[Seed] {consumers_csv} not found. Generating minimal default seed data.")
            _seed_default_data(db)
            return

        print(f"[Seed] Loading processed data from {processed_dir}...")
        consumers_df = pd.read_csv(consumers_csv)
        # Filter for consumers with valid grid topology
        if "feeder_id" in consumers_df.columns and "transformer_id" in consumers_df.columns:
            valid_mask = consumers_df["feeder_id"].notna() & consumers_df["transformer_id"].notna()
            if valid_mask.sum() >= 300:
                consumers_df = consumers_df[valid_mask]
        labels_df = pd.read_csv(labels_csv) if os.path.exists(labels_csv) else pd.DataFrame()

        # Sample 300 random consumers from processed dataset for balanced grid representation
        if len(consumers_df) > 300:
            consumers_df = consumers_df.sample(n=300, random_state=42).reset_index(drop=True)

        # Map to simple clean sequential IDs: CUS_000, CUS_001, ..., CUS_299
        orig_ids = list(consumers_df["consumer_id"])
        id_map = {orig: f"CUS_{i:03d}" for i, orig in enumerate(orig_ids)}
        consumers_df["consumer_id"] = consumers_df["consumer_id"].map(id_map)
        consumer_ids_set = set(consumers_df["consumer_id"])

        # 1. Seed Feeders
        unique_feeders = [f for f in consumers_df["feeder_id"].dropna().unique() if str(f) != 'nan']
        feeder_objs = []
        for idx, f_id in enumerate(unique_feeders):
            feeder_objs.append(Feeder(id=str(f_id), name=f"Feeder {f_id} (Grid Sector {idx+1:02d})"))
        db.bulk_save_objects(feeder_objs)
        db.commit()
        print(f"[Seed] Inserted {len(unique_feeders)} feeders.")

        # 2. Seed Transformers
        unique_tx = consumers_df[["transformer_id", "feeder_id"]].dropna().drop_duplicates()
        unique_tx = unique_tx[(unique_tx["transformer_id"].astype(str) != 'nan') & (unique_tx["feeder_id"].astype(str) != 'nan')]
        tx_objs = []
        for _, row in unique_tx.iterrows():
            tx_objs.append(Transformer(id=str(row["transformer_id"]), feeder_id=str(row["feeder_id"])))
        db.bulk_save_objects(tx_objs)
        db.commit()
        print(f"[Seed] Inserted {len(unique_tx)} transformers.")

        # 3. Seed Consumers
        consumer_objs = []
        for _, row in consumers_df.iterrows():
            consumer_objs.append(Consumer(
                id=row["consumer_id"],
                category=str(row["category"]),
                feeder_id=str(row["feeder_id"]),
                transformer_id=str(row["transformer_id"])
            ))
        db.bulk_save_objects(consumer_objs)
        db.commit()
        print(f"[Seed] Inserted {len(consumer_objs)} consumers.")

        # 4. Seed Readings and Baselines
        if os.path.exists(readings_parquet):
            print(f"[Seed] Loading readings parquet...")
            readings_df = pd.read_parquet(readings_parquet)
            readings_df = readings_df[readings_df["consumer_id"].isin(id_map.keys())].copy()
            readings_df["consumer_id"] = readings_df["consumer_id"].map(id_map)

            # Map generated_kwh to kwh if needed
            if "generated_kwh" in readings_df.columns and "kwh" not in readings_df.columns:
                readings_df = readings_df.rename(columns={"generated_kwh": "kwh"})
            elif "generated_kwh" in readings_df.columns:
                readings_df["kwh"] = readings_df["generated_kwh"]
            
            # Take recent 120 days of readings per consumer for full analytical window
            readings_df["ts_dt"] = pd.to_datetime(readings_df["ts"])
            max_ts = readings_df["ts_dt"].max()
            start_ts = max_ts - pd.Timedelta(days=120)
            readings_df = readings_df[readings_df["ts_dt"] >= start_ts].sort_values("ts_dt")

            reading_objs = []
            baseline_objs = []

            for cid, group in readings_df.groupby("consumer_id"):
                group = group.sort_values("ts_dt")
                kwh_series = group["kwh"].fillna(0.0).values
                max_kwh = float(np.nanmax(kwh_series)) if len(kwh_series) > 0 else 0.0
                all_zeros = max_kwh <= 0.01

                rolling_baseline = group["kwh"].rolling(14, min_periods=1).mean().fillna(10.5).values

                seed_idx = int("".join([c for c in cid if c.isdigit()]) or "42")
                np.random.seed(seed_idx)

                for idx, row in enumerate(group.itertuples()):
                    kwh_val = float(row.kwh) if not pd.isna(row.kwh) else 0.0
                    base_val = float(rolling_baseline[idx]) if idx < len(rolling_baseline) else 10.5

                    if all_zeros or base_val <= 0.01:
                        day_cycle = np.sin(2 * np.pi * idx / 7)
                        month_cycle = np.cos(2 * np.pi * idx / 60)
                        noise = np.random.normal(0, 0.8)
                        base_val = round(max(5.0, 10.5 + 1.8 * day_cycle + 1.2 * month_cycle), 2)
                        kwh_val = round(max(2.0, base_val + noise), 2)
                    elif base_val < 5.0:
                        base_val = max(5.0, base_val)

                    reading_objs.append(Reading(
                        consumer_id=cid,
                        ts=row.ts_dt.to_pydatetime(),
                        kwh=kwh_val,
                        voltage=230.0 + (np.random.normal(0, 2) if kwh_val > 0 else 0),
                        current=round(kwh_val / 0.23, 2) if kwh_val > 0 else 0.0,
                        power_kw=round(kwh_val, 2),
                        meter_status=str(row.meter_status),
                        comm_status=str(row.comm_status)
                    ))

                    baseline_objs.append(Baseline(
                        consumer_id=cid,
                        ts=row.ts_dt.to_pydatetime(),
                        expected_kwh=round(base_val, 2)
                    ))

            db.bulk_save_objects(reading_objs)
            db.bulk_save_objects(baseline_objs)
            db.commit()
            print(f"[Seed] Inserted {len(reading_objs)} readings and baselines.")

        # 5. Seed Cases and Alerts
        labels_map = {}
        if not labels_df.empty:
            for _, row in labels_df.iterrows():
                orig_cid = row["consumer_id"]
                if orig_cid in id_map:
                    labels_map[id_map[orig_cid]] = row

        case_objs = []
        alert_objs = []

        statuses = ["New", "Under Review", "Inspection Scheduled", "Confirmed", "False Alarm", "Closed"]

        for idx, c_row in consumers_df.iterrows():
            cid = c_row["consumer_id"]
            label_info = labels_map.get(cid, {})
            theft_flag = c_row.get("theft_label", 0)
            true_cause = label_info.get("true_cause", "Normal")

            if true_cause in ["Theft/Tampering", "THEFT"]:
                risk_level = "High"
                cause = "Theft/Tampering"
                score = round(float(np.random.uniform(0.82, 0.98)), 2)
                confidence = round(float(np.random.uniform(0.88, 0.96)), 2)
                estimated_loss = round(float(np.random.uniform(15000, 52000)), 2)
                evidence = '["Abrupt drop in electricity usage without corresponding load reduction.", "Neighboring properties on this feeder continue normal consumption."]'
                counter_evidence = '["Smart meter clock synchronization verified and accurate.", "Meter communication link active with no network outage."]'
                action = "Dispatch field technician to inspect meter enclosure and verify junction seals."
            elif true_cause in ["Meter Malfunction", "METER"]:
                risk_level = "Medium"
                cause = "Meter Malfunction"
                score = round(float(np.random.uniform(0.65, 0.81)), 2)
                confidence = round(float(np.random.uniform(0.75, 0.89)), 2)
                estimated_loss = round(float(np.random.uniform(5000, 18000)), 2)
                evidence = '["Zero electricity consumption registered during active hours.", "Line voltage confirms electricity supply was present."]'
                counter_evidence = '["Smart meter communication link is stable with no network dropouts.", "No physical enclosure tamper log recorded."]'
                action = "Schedule meter technician for hardware diagnostics and sensor recalibration."
            elif true_cause in ["Communication Failure", "COMM"]:
                risk_level = "Medium"
                cause = "Communication Failure"
                score = round(float(np.random.uniform(0.50, 0.64)), 2)
                confidence = round(float(np.random.uniform(0.70, 0.85)), 2)
                estimated_loss = round(float(np.random.uniform(2000, 8000)), 2)
                evidence = '["Repeated transmission timeouts and missing meter data packets.", "Cellular gateway reports connection drops from meter."]'
                counter_evidence = '["Meter hardware diagnostics showed normal status prior to signal loss.", "No physical tamper detected on the meter box."]'
                action = "Inspect cellular modem antenna and reset communication module."
            elif true_cause in ["Legitimate Abnormal", "LEGIT", "Seasonal Variation", "SEASONAL"]:
                risk_level = "Low"
                cause = true_cause if "Seasonal" in true_cause else "Legitimate Load Change"
                score = round(float(np.random.uniform(0.25, 0.49)), 2)
                confidence = round(float(np.random.uniform(0.80, 0.92)), 2)
                estimated_loss = 0.0
                evidence = '["Electricity usage shift aligns with regional seasonal temperature changes."]'
                counter_evidence = '["Nearby consumers on the same feeder exhibit the same consumption pattern."]'
                action = "Update consumer baseline profile to account for seasonal shift."
            else:
                risk_level = "Low"
                cause = "Normal Pattern"
                score = round(float(np.random.uniform(0.05, 0.24)), 2)
                confidence = round(float(np.random.uniform(0.90, 0.99)), 2)
                estimated_loss = 0.0
                evidence = '["Electricity usage is consistent with historical baseline patterns."]'
                counter_evidence = '["All diagnostic sensors and network links report normal operation."]'
                action = "No action required."

            status = statuses[idx % len(statuses)] if risk_level != "Low" else "Closed"
            priority = (idx + 1) if risk_level in ["High", "Medium"] else (idx + 100)

            first_flagged = datetime.utcnow() - timedelta(days=int(np.random.randint(2, 20)))
            last_updated = datetime.utcnow() - timedelta(hours=int(np.random.randint(1, 48)))

            case_objs.append(Case(
                consumer_id=cid,
                status=status,
                risk_level=risk_level,
                cause=cause,
                anomaly_score=score,
                confidence=confidence,
                first_flagged_at=first_flagged,
                last_updated_at=last_updated,
                note=f"Automatic triage entry for consumer {cid}.",
                evidence=evidence,
                counter_evidence=counter_evidence,
                recommended_action=action,
                estimated_loss=estimated_loss,
                priority=float(priority)
            ))

            if risk_level in ["High", "Medium"]:
                alert_objs.append(Alert(
                    consumer_id=cid,
                    risk_level=risk_level,
                    cause=cause,
                    message=f"Consumer {cid} flagged with {risk_level} risk due to {cause}.",
                    is_read=False,
                    created_at=last_updated
                ))

        db.bulk_save_objects(case_objs)
        db.bulk_save_objects(alert_objs)
        db.commit()
        print(f"[Seed] Inserted {len(case_objs)} cases and {len(alert_objs)} alerts.")

        # 6. Seed Feeder Summaries
        feeder_summary_objs = []
        for f_id in unique_feeders:
            f_consumers = [c for c in case_objs if c.consumer_id in set(consumers_df[consumers_df["feeder_id"] == f_id]["consumer_id"])]
            total_cons = len(f_consumers)
            high_risk_cnt = sum(1 for c in f_consumers if c.risk_level == "High")
            total_kwh = float(np.random.uniform(120000, 450000))
            avg_loss = round(float(np.random.uniform(4.5, 14.2)), 2)

            feeder_summary_objs.append(FeederSummary(
                feeder_id=f_id,
                ts=datetime.utcnow(),
                total_consumers=total_cons,
                high_risk_consumers=high_risk_cnt,
                total_consumption=total_kwh,
                avg_loss_pct=avg_loss
            ))

        db.bulk_save_objects(feeder_summary_objs)
        db.commit()
        print(f"[Seed] Inserted {len(feeder_summary_objs)} feeder summary records.")

        # Ensure database is mirrored across both root and backend directory paths
        db_path = DATABASE_URL.replace("sqlite:///", "")
        abs_db = os.path.abspath(db_path)
        candidates = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tracewatt.db")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tracewatt.db")),
        ]
        import shutil
        for cand in candidates:
            if cand != abs_db and os.path.exists(abs_db):
                try:
                    shutil.copy2(abs_db, cand)
                    print(f"[Seed] Synced database mirror to: {cand}")
                except Exception as sync_err:
                    print(f"[Seed Warning] Could not sync mirror {cand}: {sync_err}")

        print("[Seed] Database seeding completed successfully.")

    except Exception as e:
        print(f"[Seed Error] {e}")
        db.rollback()
        raise e
    finally:
        db.close()

def _seed_default_data(db):
    print("[Seed] Creating fallback default seed data...")
    feeders = [Feeder(id="FDR_01", name="Feeder FDR_01 (North Grid)"), Feeder(id="FDR_02", name="Feeder FDR_02 (South Grid)")]
    db.bulk_save_objects(feeders)
    db.commit()

    transformers = [Transformer(id="TX_001", feeder_id="FDR_01"), Transformer(id="TX_002", feeder_id="FDR_02")]
    db.bulk_save_objects(transformers)
    db.commit()

    consumers = [
        Consumer(id="CUS_000", category="residential", feeder_id="FDR_01", transformer_id="TX_001"),
        Consumer(id="CUS_001", category="commercial", feeder_id="FDR_01", transformer_id="TX_001"),
        Consumer(id="CUS_002", category="industrial", feeder_id="FDR_02", transformer_id="TX_002")
    ]
    db.bulk_save_objects(consumers)
    db.commit()

    cases = [
        Case(
            consumer_id="CUS_000", status="Under Review", risk_level="High", cause="Theft/Tampering",
            anomaly_score=0.92, confidence=0.91, first_flagged_at=datetime.utcnow() - timedelta(days=5),
            last_updated_at=datetime.utcnow(), estimated_loss=18450.0, priority=1.0,
            evidence='["Abrupt drop in electricity usage without corresponding load reduction."]',
            counter_evidence='["Meter internal clock sync verified."]',
            recommended_action="Dispatch field inspection unit to verify terminal junction seals."
        ),
        Case(
            consumer_id="CUS_001", status="New", risk_level="Medium", cause="Meter Malfunction",
            anomaly_score=0.74, confidence=0.85, first_flagged_at=datetime.utcnow() - timedelta(days=2),
            last_updated_at=datetime.utcnow(), estimated_loss=7200.0, priority=2.0,
            evidence='["Zero reading registered during peak operational hours."]',
            counter_evidence='["No physical enclosure tamper log recorded."]',
            recommended_action="Schedule meter diagnostic team for recalibration."
        )
    ]
    db.bulk_save_objects(cases)

    alerts = [
        Alert(consumer_id="CUS_000", risk_level="High", cause="Theft/Tampering", message="Consumer CUS_000 flagged for High risk due to Theft/Tampering.", is_read=False),
        Alert(consumer_id="CUS_001", risk_level="Medium", cause="Meter Malfunction", message="Consumer CUS_001 flagged for Medium risk due to Meter Malfunction.", is_read=False)
    ]
    db.bulk_save_objects(alerts)
    db.commit()
    print("[Seed] Fallback default seed data successfully created.")

if __name__ == "__main__":
    force_flag = "--force" in sys.argv or "-f" in sys.argv
    seed_database(force=force_flag)
