from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models
from .database import engine, get_db
from pydantic import BaseModel

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="FightIQ API", version="0.1.0")

class FighterStatsResponse(BaseModel):
    sig_strikes_landed_per_min: float | None
    sig_strikes_absorbed_per_min: float | None
    striking_accuracy: float | None
    striking_defense: float | None
    takedown_avg_per_fight: float | None
    takedown_accuracy: float | None
    takedown_defense: float | None
    
    class Config:
        from_attributes = True # can serialize this model instance

class FighterResponse(BaseModel):
    id: int
    name: str
    nickname: str | None
    weight_class: str | None
    wins: int
    losses: int
    draws: int
    height_cm: float | None
    reach_cm: float | None
    stance: str | None
    stats: FighterStatsResponse | None = None
    
    class Config:
        from_attributes = True

# Endpoints 
@app.get("/health")
def health():
    return {"message": "FightIQ API v0.1", "status": "running"}

@app.get("/fighters", response_model=List[FighterResponse])
def get_fighters(skip: int = 0, limit: int = 20, weight_class: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Fighter)
    
    if weight_class:
        query = query.filter(models.Fighter.weight_class == weight_class)
    
    fighters = query.offset(skip).limit(limit).all()
    return fighters

@app.get("/fighters/{fighter_id}", response_model=FighterResponse)
def get_fighter(fighter_id: int, db: Session = Depends(get_db)):
    fighter = db.query(models.Fighter).filter(
        models.Fighter.id == fighter_id
    ).first()
    
    if not fighter:
        raise HTTPException(status_code=404, detail="Fighter not found")
    
    return fighter

@app.get("/fighters/{fighter_id}/stats", response_model=FighterStatsResponse)
def get_fighter_stats(fighter_id: int, db: Session = Depends(get_db)):
    stats = db.query(models.FighterStats).filter(
        models.FighterStats.fighter_id == fighter_id
    ).first()
    
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    
    return stats