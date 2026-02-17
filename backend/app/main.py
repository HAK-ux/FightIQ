from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import models
from .matchup import MatchupEngine
from .database import engine, get_db
from app.schemas import (FightResponse, FighterResponse, FighterStatsResponse, 
                        MatchupRequest, DeltasResponse, MatchupPredictionResponse,
                        MatchupBreakdownResponse)
from .ai_breakdown import AIBreakDownService

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="FightIQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

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

@app.post("/matchup/predict", response_model=MatchupPredictionResponse)
def predict_matchup(request: MatchupRequest, db: Session = Depends(get_db)):
    """
    Predict the outcome of a matchup between two fighters.
    Returns win probabilities and key statisstical deltas.
    """

    engine = MatchupEngine(db)

    try:
        prediction = engine.predict_simple(request.fighter_a_id, request.fighter_b_id)

        # Fetch fighter details for response
        fighter_a = db.query(models.Fighter).filter(
            models.Fighter.id == request.fighter_a_id
        ).first()
        fighter_b = db.query(models.Fighter).filter(
            models.Fighter.id == request.fighter_b_id
        ).first()

        if not fighter_a or not fighter_b:
            raise HTTPException(status_code=404, detail="Fighter not found")
        
        # Return prediction + fighters
        return {
            **prediction, "fighter_a": fighter_a, "fighter_b": fighter_b
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/matchup/{fighter_a_id}/vs/{fighter_b_id}")
def get_matchup_prediction(fighter_a_id: int, fighter_b_id: int, db: Session = Depends(get_db)):
    """
    Alternative GET endpoint for matchup prediction - direct URL access.
    """
    engine = MatchupEngine(db)
    
    try:
        prediction = engine.predict_simple(fighter_a_id, fighter_b_id)
        
        fighter_a = db.query(models.Fighter).filter(
            models.Fighter.id == fighter_a_id
        ).first()
        fighter_b = db.query(models.Fighter).filter(
            models.Fighter.id == fighter_b_id
        ).first()
        
        return {
            **prediction,
            "fighter_a": fighter_a,
            "fighter_b": fighter_b
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@app.post("/matchup/breakdown", response_model=MatchupBreakdownResponse)
def get_matchup_breakdown(request: MatchupRequest, db: Session = Depends(get_db)):
    """
    Get a full fight breakdown with AI-generated analysis.
    Checks cache first to avoid redundant AI calls.
    """
    engine = MatchupEngine(db)
    
    try:
        # Check if we have a cached breakdown
        cached_breakdown = engine._get_cached_breakdown(
            request.fighter_a_id,
            request.fighter_b_id
        )
        
        if cached_breakdown:
            # Fetch fighter details for response
            fighter_a = db.query(models.Fighter).filter(
                models.Fighter.id == request.fighter_a_id
            ).first()
            fighter_b = db.query(models.Fighter).filter(
                models.Fighter.id == request.fighter_b_id
            ).first()
            
            return {
                **cached_breakdown,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "from_cache": True
            }
        
        # No cache - generate fresh prediction
        prediction = engine.predict_simple(
            request.fighter_a_id,
            request.fighter_b_id,
            use_cache=True  # This caches the prediction part
        )
        
        # Fetch fighter details
        fighter_a = db.query(models.Fighter).filter(
            models.Fighter.id == request.fighter_a_id
        ).first()
        fighter_b = db.query(models.Fighter).filter(
            models.Fighter.id == request.fighter_b_id
        ).first()
        
        # Generate AI breakdown (this is the expensive part)
        ai_service = AIBreakDownService()
        breakdown_text = ai_service.generate_breakdown(
            fighter_a, fighter_b, prediction
        )
        
        # Generate quick win conditions
        win_conditions = ai_service.generate_quick_summary(
            fighter_a, fighter_b, prediction
        )
        
        # Cache the complete breakdown
        engine._cache_breakdown(
            request.fighter_a_id,
            request.fighter_b_id,
            prediction,
            breakdown_text,
            win_conditions
        )
        
        return {
            **prediction,
            "fighter_a": fighter_a,
            "fighter_b": fighter_b,
            "breakdown": breakdown_text,
            "fighter_a_win_condition": win_conditions["fighter_a_win_condition"],
            "fighter_b_win_condition": win_conditions["fighter_b_win_condition"],
            "from_cache": False
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating breakdown: {str(e)}")


@app.get("/matchup/{fighter_a_id}/vs/{fighter_b_id}/breakdown", response_model=MatchupBreakdownResponse)
def get_matchup_breakdown_by_url(fighter_a_id: int, fighter_b_id: int, db: Session = Depends(get_db)):
    """
    GET version of breakdown endpoint with caching.
    """
    engine = MatchupEngine(db)
    
    try:
        # Check cache first
        cached_breakdown = engine._get_cached_breakdown(fighter_a_id, fighter_b_id)
        
        if cached_breakdown:
            fighter_a = db.query(models.Fighter).filter(
                models.Fighter.id == fighter_a_id
            ).first()
            fighter_b = db.query(models.Fighter).filter(
                models.Fighter.id == fighter_b_id
            ).first()
            
            return {
                **cached_breakdown,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "from_cache": True
            }
        
        # Generate fresh
        prediction = engine.predict_simple(fighter_a_id, fighter_b_id)
        
        fighter_a = db.query(models.Fighter).filter(
            models.Fighter.id == fighter_a_id
        ).first()
        fighter_b = db.query(models.Fighter).filter(
            models.Fighter.id == fighter_b_id
        ).first()
        
        ai_service = AIBreakDownService()
        breakdown_text = ai_service.generate_breakdown(
            fighter_a, fighter_b, prediction
        )
        
        win_conditions = ai_service.generate_quick_summary(
            fighter_a, fighter_b, prediction
        )
        
        # Cache it
        engine._cache_breakdown(
            fighter_a_id,
            fighter_b_id,
            prediction,
            breakdown_text,
            win_conditions
        )
        
        return {
            **prediction,
            "fighter_a": fighter_a,
            "fighter_b": fighter_b,
            "breakdown": breakdown_text,
            **win_conditions,
            "from_cache": False
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating breakdown: {str(e)}")
    
@app.get("/model/info")
def get_model_info():
    """Returns info about the currently loaded prediction model."""
    import joblib, os
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'fight_predictor.joblib')
    
    if not os.path.exists(model_path):
        return {"status": "rule_based_fallback", "model": None}
    
    model_data = joblib.load(model_path)
    return {
        "status": "ml_model_loaded",
        "model_name": model_data["model_name"],
        "version": model_data["version"],
        "auc_score": model_data["auc_score"],
        "features": model_data["feature_columns"]
    }