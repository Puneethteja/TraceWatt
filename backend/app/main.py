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

app.include_router(readings.router)
