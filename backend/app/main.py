from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from .config import ALLOWED_ORIGINS
from .db import init_db, get_pipeline_metrics
from .seed import seed_database
from .services.mqtt_service import mqtt_service
from .routers import readings, consumers, cases, feeders, export, alerts, dashboard, ws
from .services.pipeline import process_queue

app = FastAPI(title="TraceWatt API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    seed_database()
    # Start MQTT background loop
    mqtt_service.start()
    # Start pipeline queue worker
    asyncio.create_task(process_queue())

@app.on_event("shutdown")
async def shutdown_event():
    mqtt_service.stop()

@app.get("/health")
async def health_check():
    metrics = get_pipeline_metrics()
    return {
        "status": "ok",
        "app": "TraceWatt API",
        "database": "synced",
        "fuzzy_engine": "active",
        "mqtt_connected": mqtt_service.is_connected,
        "pipeline_metrics": metrics
    }

@app.get("/evaluation")
def root_evaluation():
    return dashboard.dashboard_evaluation()

app.include_router(dashboard.router)
app.include_router(readings.router)
app.include_router(consumers.router)
app.include_router(cases.router)
app.include_router(feeders.router)
app.include_router(alerts.router)
app.include_router(export.router)
app.include_router(ws.router)
