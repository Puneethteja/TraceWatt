import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db import init_db
from app.models import Feeder, Transformer, Consumer, Reading, Baseline, Label
from app.config import DATABASE_URL, DATA_DIR

def load_data():
    print("Initializing database...")
    init_db()
    
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Load Feeders
        feeders_path = os.path.join(DATA_DIR, "feeders.csv")
        if os.path.exists(feeders_path):
            print("Loading feeders...")
            df = pd.read_csv(feeders_path)
            for _, row in df.iterrows():
                if not db.query(Feeder).filter_by(id=row["id"]).first():
                    db.add(Feeder(id=row["id"], name=row.get("name", f"Feeder {row['id']}")))
            db.commit()

        # Load Transformers
        transformers_path = os.path.join(DATA_DIR, "transformers.csv")
        if os.path.exists(transformers_path):
            print("Loading transformers...")
            df = pd.read_csv(transformers_path)
            for _, row in df.iterrows():
                if not db.query(Transformer).filter_by(id=row["id"]).first():
                    db.add(Transformer(id=row["id"], feeder_id=row["feeder_id"]))
            db.commit()

        # Load Consumers
        consumers_path = os.path.join(DATA_DIR, "consumers.csv")
        if os.path.exists(consumers_path):
            print("Loading consumers...")
            df = pd.read_csv(consumers_path)
            for _, row in df.iterrows():
                if not db.query(Consumer).filter_by(id=row["id"]).first():
                    db.add(Consumer(
                        id=row["id"], 
                        category=row["category"], 
                        feeder_id=row["feeder_id"], 
                        transformer_id=row["transformer_id"]
                    ))
            db.commit()

        print("Data loaded successfully.")
    except Exception as e:
        print(f"Error loading data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_data()
