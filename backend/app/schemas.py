from datetime import date
from pydantic import BaseModel, ConfigDict


class FighterStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # can serialize this model instance

    sig_strikes_landed_per_min: float | None
    sig_strikes_absorbed_per_min: float | None
    striking_accuracy: float | None
    striking_defense: float | None
    takedown_avg_per_fight: float | None
    takedown_accuracy: float | None
    takedown_defense: float | None


class FighterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    

class FightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fighter_a_id: int
    fighter_b_id: int
    winner_id: int
    fight_date: date 
    method: str
    round: int
    event_name: str
    
