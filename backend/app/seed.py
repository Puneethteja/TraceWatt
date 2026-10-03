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

def seed_database():
    print("[Seed] Initializing database tables...")
    init_db()

    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if consumers already exist
        existing_consumers_count = db.query(Consumer).count()
        if existing_consumers_count > 0:
            print(f"[Seed] Database already contains {existing_consumers_count} consumers. Skipping seed.")
            return

        processed_dir = os.path.join(DATA_DIR, "processed")
        consumers_csv = os.path.join(processed_dir, "consumers_synthetic.csv")
        labels_csv = os.path.join(processed_dir, "labels.csv")
        readings_parquet = os.path.join(processed_dir, "synthetic_readings.parquet")

        if not os.path.exists(consumers_csv):
            print(f"[Seed] {consumers_csv} not found. Generating minimal default seed data.")
            _seed_default_data(db)
            return

        print(f"[Seed] Loading synthetic data from {processed_dir}...")
        consumers_df = pd.read_csv(consumers_csv)
        labels_df = pd.read_csv(labels_csv) if os.path.exists(labels_csv) else pd.DataFrame()

        # Limit to 300 consumers for fast database initialization and high responsiveness
        consumers_df = consumers_df.head(300)
        consumer_ids_set = set(consumers_df["consumer_id"])

        # 1. Seed Feeders
        unique_feeders = consumers_df["feeder_id"].dropna().unique()
        feeder_objs = []
        for idx, f_id in enumerate(unique_feeders):
            feeder_objs.append(Feeder(id=f_id, name=f"Feeder {f_id} (Grid Sector {idx+1:02d})"))
        db.bulk_save_objects(feeder_objs)
        db.commit()
        print(f"[Seed] Inserted {len(unique_feeders)} feeders.")

        # 2. Seed Transformers
        unique_tx = consumers_df[["transformer_id", "feeder_id"]].drop_duplicates()
        tx_objs = []
        for _, row in unique_tx.iterrows():
            tx_objs.append(Transformer(id=row["transformer_id"], feeder_id=row["feeder_id"]))
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
            readings_df = readings_df[readings_df["consumer_id"].isin(consumer_ids_set)]
            
            # Take recent 60 days of readings per consumer for performance
            readings_df["ts_dt"] = pd.to_datetime(readings_df["ts"])
            max_ts = readings_df["ts_dt"].max()
            start_ts = max_ts - pd.Timedelta(days=60)
            readings_df = readings_df[readings_df["ts_dt"] >= start_ts].sort_values("ts_dt")

            reading_objs = []
            baseline_objs = []

            for cid, group in readings_df.groupby("consumer_id"):
                group = group.sort_values("ts_dt")
                kwh_series = group["kwh"].fillna(0.0).values
                rolling_baseline = group["kwh"].rolling(14, min_periods=1).mean().fillna(30.0).values

                for idx, row in enumerate(group.itertuples()):
                    kwh_val = float(row.kwh) if not pd.isna(row.kwh) else 0.0
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
                        expected_kwh=round(float(rolling_baseline[idx]), 2)
                    ))

            db.bulk_save_objects(reading_objs)
            db.bulk_save_objects(baseline_objs)
            db.commit()
            print(f"[Seed] Inserted {len(reading_objs)} readings and baselines.")

        # 5. Seed Cases and Alerts
        labels_map = {}
        if not labels_df.empty:
            for _, row in labels_df.iterrows():
                labels_map[row["consumer_id"]] = row

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
                evidence = '["Abrupt 54% drop in active power without load reduction.", "Feeder aggregate balance shows corresponding gap."]'
                counter_evidence = '["Meter internal clock sync verified.", "No historical solar net metering installed."]'
                action = "Dispatch field inspection unit to verify terminal junction seals."
            elif true_cause in ["Meter Malfunction", "METER"]:
                risk_level = "Medium"
                cause = "Meter Malfunction"
                score = round(float(np.random.uniform(0.65, 0.81)), 2)
                confidence = round(float(np.random.uniform(0.75, 0.89)), 2)
                estimated_loss = round(float(np.random.uniform(5000, 18000)), 2)
                evidence = '["Zero reading sequence registered during peak load hours.", "Voltage telemetry shows active supply."]'
                counter_evidence = '["No physical enclosure tamper log recorded."]'
                action = "Schedule meter diagnostic team for recalibration."
            elif true_cause in ["Communication Failure", "COMM"]:
                risk_level = "Medium"
                cause = "Communication Failure"
                score = round(float(np.random.uniform(0.50, 0.64)), 2)
                confidence = round(float(np.random.uniform(0.70, 0.85)), 2)
                estimated_loss = round(float(np.random.uniform(2000, 8000)), 2)
                evidence = '["Intermittent SIM gateway ping timeout.", "Packet retransmission threshold exceeded."]'
                counter_evidence = '["Last manual index reading matches transformer total."]'
                action = "Reset cellular modem interface and test signal strength."
            elif true_cause in ["Legitimate Abnormal", "LEGIT", "Seasonal Variation", "SEASONAL"]:
                risk_level = "Low"
                cause = true_cause if "Seasonal" in true_cause else "Legitimate Load Change"
                score = round(float(np.random.uniform(0.25, 0.49)), 2)
                confidence = round(float(np.random.uniform(0.80, 0.92)), 2)
                estimated_loss = 0.0
                evidence = '["HVAC load variance matches ambient temperature series."]'
                counter_evidence = '["Peer consumer group exhibits identical seasonal slope."]'
                action = "Update consumer load profile baseline."
            else:
                risk_level = "Low"
                cause = "Normal Pattern"
                score = round(float(np.random.uniform(0.05, 0.24)), 2)
                confidence = round(float(np.random.uniform(0.90, 0.99)), 2)
                estimated_loss = 0.0
                evidence = '["Telemetry inline with historical 30-day baseline."]'
                counter_evidence = '["All diagnostic checks passed."]'
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
        Consumer(id="CONS-001", category="residential", feeder_id="FDR_01", transformer_id="TX_001"),
        Consumer(id="CONS-002", category="commercial", feeder_id="FDR_01", transformer_id="TX_001"),
        Consumer(id="CONS-003", category="industrial", feeder_id="FDR_02", transformer_id="TX_002")
    ]
    db.bulk_save_objects(consumers)
    db.commit()

    cases = [
        Case(
            consumer_id="CONS-001", status="Under Review", risk_level="High", cause="Theft/Tampering",
            anomaly_score=0.92, confidence=0.91, first_flagged_at=datetime.utcnow() - timedelta(days=5),
            last_updated_at=datetime.utcnow(), estimated_loss=18450.0, priority=1.0,
            evidence='["Abrupt 54% drop in active power without load reduction."]',
            counter_evidence='["Meter internal clock sync verified."]',
            recommended_action="Dispatch field inspection unit to verify terminal junction seals."
        ),
        Case(
            consumer_id="CONS-002", status="New", risk_level="Medium", cause="Meter Malfunction",
            anomaly_score=0.74, confidence=0.85, first_flagged_at=datetime.utcnow() - timedelta(days=2),
            last_updated_at=datetime.utcnow(), estimated_loss=7200.0, priority=2.0,
            evidence='["Zero reading registered during peak operational hours."]',
            counter_evidence='["No physical enclosure tamper log recorded."]',
            recommended_action="Schedule meter diagnostic team for recalibration."
        )
    ]
    db.bulk_save_objects(cases)

    alerts = [
        Alert(consumer_id="CONS-001", risk_level="High", cause="Theft/Tampering", message="Consumer CONS-001 flagged for High risk due to Theft/Tampering.", is_read=False),
        Alert(consumer_id="CONS-002", risk_level="Medium", cause="Meter Malfunction", message="Consumer CONS-002 flagged for Medium risk due to Meter Malfunction.", is_read=False)
    ]
    db.bulk_save_objects(alerts)
    db.commit()
    print("[Seed] Fallback default seed data successfully created.")

if __name__ == "__main__":
    seed_database()
