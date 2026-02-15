from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models
from .database import engine, get_db
from app.schemas import FightResponse, FighterResponse, FighterStatsResponse

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="FightIQ API", version="0.1.0")

# Endpoints 
@app.get("/health")
def health():
    return {"message": "FightIQ API v0.1", "status": "running"}

@app.get("/fighters/search")
def search_fighters(
    q: str,
    db: Session = Depends(get_db)
):
    """Search fighters by name or nickname"""
    fighters = db.query(models.Fighter).filter(
        (models.Fighter.name.ilike(f"%{q}%")) | 
        (models.Fighter.nickname.ilike(f"%{q}%"))
    ).limit(10).all()
    
    return fighters

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

@app.get("/weight-classes")
def get_weight_classes(db: Session = Depends(get_db)):
    """Get list of all weight classes in database"""
    weight_classes = db.query(models.Fighter.weight_class).distinct().all()
    return [wc[0] for wc in weight_classes if wc[0]]

@app.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """Get overall database statistics"""
    total_fighters = db.query(models.Fighter).count()
    total_fights = db.query(models.Fight).count()
    
    return {
        "total_fighters": total_fighters,
        "total_fights": total_fights,
        "weight_classes": db.query(models.Fighter.weight_class).distinct().count()
    }

@app.get("/fighters/{fighter_id}/fights", response_model=List[FightResponse])
def get_fighter_fights(fighter_id: int, db: Session = Depends(get_db)):
    """Get all fights for a specific fighter"""
    fights = db.query(models.Fight).filter(
        (models.Fight.fighter_a_id == fighter_id) |
        (models.Fight.fighter_b_id == fighter_id)
    ).order_by(models.Fight.fight_date.desc()).all()
    
    return fights