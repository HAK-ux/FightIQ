from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone

class Fighter(Base):
    __tablename__ = "fighters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    nickname = Column(String)
    weight_class = Column(String)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    height_cm = Column(Float)
    reach_cm = Column(Float)
    stance = Column(String)

    # Relationship to stats
    stats = relationship("FighterStats", back_populates="fighter", uselist=False)

class FighterStats(Base):
    __tablename__ = "fighter_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), unique=True)
    
    # Striking stats
    sig_strikes_landed_per_min = Column(Float)
    sig_strikes_absorbed_per_min = Column(Float)
    striking_accuracy = Column(Float)  # percentage
    striking_defense = Column(Float)   # percentage
    
    # Grappling stats
    takedown_avg_per_fight = Column(Float)
    takedown_accuracy = Column(Float)  # percentage
    takedown_defense = Column(Float)   # percentage
    submission_avg_per_fight = Column(Float)
    
    # Relationship back to fighter
    fighter = relationship("Fighter", back_populates="stats")

class Fight(Base):
    __tablename__ = "fights"
    
    id = Column(Integer, primary_key=True, index=True)
    fighter_a_id = Column(Integer, ForeignKey("fighters.id"))
    fighter_b_id = Column(Integer, ForeignKey("fighters.id"))
    winner_id = Column(Integer, ForeignKey("fighters.id"))
    fight_date = Column(Date)
    method = Column(String)  # KO/TKO, Submission, Decision, etc.
    round = Column(Integer)
    event_name = Column(String)

class MatchupCache(Base):
    __tablename__ = "matchup_cache"

    id = Column(Integer, primary_key=True, index=True)
    fighter_a_id = Column(Integer, ForeignKey("fighters.id"))
    fighter_b_id = Column(Integer, ForeignKey("fighters.id"))
    prediction_data = Column(JSON)  # Store the full prediction
    model_version = Column(String, default="v1_simple") # Which model we used to predict
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_matchup_lookup', 'fighter_a_id', 'fighter_b_id', 'model_version'),
    )