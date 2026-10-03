"""
backend/app/models.py
=====================
SQLAlchemy models for TraceWatt application database.
"""

from __future__ import annotations

from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Consumer(Base):
    __tablename__ = "consumers"

    consumer_id = Column(String, primary_key=True)
    transformer_id = Column(String, nullable=True)


class Reading(Base):
    __tablename__ = "readings"

    consumer_id = Column(String, primary_key=True)
    ts = Column(String, primary_key=True)
    kwh = Column(Float, nullable=True)


class TransformerReading(Base):
    __tablename__ = "transformer_readings"

    transformer_id = Column(String, primary_key=True)
    ts = Column(String, primary_key=True)
    energy_in_kwh = Column(Float, nullable=False)


class FeederSummary(Base):
    __tablename__ = "feeder_summary"

    transformer_id = Column(String, primary_key=True)
    window_start = Column(String, primary_key=True)
    window_end = Column(String, primary_key=True)
    energy_in_kwh = Column(Float, nullable=False)
    energy_metered_kwh = Column(Float, nullable=False)
    unexplained_loss_pct = Column(Float, nullable=False)
    cluster_score = Column(Float, nullable=False)
    cluster_flag = Column(Integer, nullable=False)
