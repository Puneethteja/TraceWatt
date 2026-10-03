from fastapi import APIRouter, HTTPException, Depends
from ..schemas import ReadingIn, ReadingAck
from ..db import insert_reading, SessionLocal
from ..models import Consumer
from ..services.pipeline import queue_reading

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/readings", response_model=ReadingAck)
async def create_reading(reading: ReadingIn, db=Depends(get_db)):
    # Check if consumer exists
    consumer = db.query(Consumer).filter(Consumer.id == reading.consumer_id).first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Unknown consumer")
    
    try:
        # Try inserting reading (duplicate check is in db.insert_reading)
        stored = insert_reading(reading)
    except Exception as e:
        # Log the actual error internally in a real scenario
        raise HTTPException(status_code=500, detail="Database insertion failed")
    
    queued = False
    if stored:
        # Queue reading for processing
        await queue_reading(reading)
        queued = True

    return ReadingAck(stored=stored, queued=queued)
