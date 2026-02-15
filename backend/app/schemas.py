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

class MatchupRequest(BaseModel):
    fighter_a_id: int
    fighter_b_id: int

class DeltasResponse(BaseModel):
    reach_diff_cm: float
    height_diff_cm: float
    striking_output_diff: float
    striking_defense_diff: float
    striking_accuracy_diff: float
    striking_absorbed_diff: float
    takedown_offense_diff: float
    takedown_defense_diff: float
    takedown_accuracy_diff: float
    win_percentage_diff: float
    experience_diff: float

class MatchupPredictionResponse(BaseModel):
    fighter_a_win_probability: float
    fighter_b_win_probability: float
    confidence: str
    method: str
    deltas: DeltasResponse
    fighter_a: FighterResponse
    fighter_b: FighterResponse