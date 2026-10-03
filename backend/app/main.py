from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from .config import ALLOWED_ORIGINS
from .db import init_db
from .routers import readings
from .services.pipeline import process_queue

app = FastAPI(title="TraceWatt API")

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
    # Start the pipeline background task
    asyncio.create_task(process_queue())

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from .routers import readings, consumers, cases, feeders, export, alerts

app.include_router(readings.router)
app.include_router(consumers.router)
app.include_router(cases.router)
app.include_router(feeders.router)
app.include_router(alerts.router)
app.include_router(export.router)
