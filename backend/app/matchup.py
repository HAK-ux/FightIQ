from sqlalchemy.orm import Session
from . import models
from typing import Dict, Tuple
import math

class MatchupEngine():
    """
    Computes feature deltas between two fighters and generates predictions.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_fighter_with_stats(self, fighter_id: int):
        fighter = self.db.query(models.Fighter).filter(models.Fighter.id == fighter_id).first()

        if not fighter or not fighter.stats:
            return None

        return fighter

    def compute_deltas(self, fighter_a_id: int, fighter_b_id: int) -> Dict:
        """
        Compute the feature differences between two fighters.
        Positive values favor fighter_a, negative favor fighter_b
        """
        fighter_a = self.get_fighter_with_stats(fighter_a_id)
        fighter_b = self.get_fighter_with_stats(fighter_b_id)

        if not fighter_a or not fighter_b:
            raise ValueError("One or both fighters not found or missing stats")
        
        stats_a = fighter_a.stats
        stats_b = fighter_b.stats

        deltas = {
            # Physical attributes
            "reach_diff_cm": (fighter_a.reach_cm or 0) - (fighter_b.reach_cm or 0),
            "height_diff_cm": (fighter_a.height_cm or 0) - (fighter_b.height_cm or 0),
            
            # Striking
            "striking_output_diff": stats_a.sig_strikes_landed_per_min - stats_b.sig_strikes_landed_per_min,
            "striking_defense_diff": stats_a.striking_defense - stats_b.striking_defense,
            "striking_accuracy_diff": stats_a.striking_accuracy - stats_b.striking_accuracy,
            "striking_absorbed_diff": stats_b.sig_strikes_absorbed_per_min - stats_a.sig_strikes_absorbed_per_min,  # Lower is better
            
            # Grappling
            "takedown_offense_diff": stats_a.takedown_avg_per_fight - stats_b.takedown_avg_per_fight,
            "takedown_defense_diff": stats_a.takedown_defense - stats_b.takedown_defense,
            "takedown_accuracy_diff": stats_a.takedown_accuracy - stats_b.takedown_accuracy,
            
            # Record
            "win_percentage_diff": self._calculate_win_pct(fighter_a) - self._calculate_win_pct(fighter_b),
            "experience_diff": (fighter_a.wins + fighter_a.losses) - (fighter_b.wins + fighter_b.losses)
        }

        return deltas
    
    def _calculate_win_pct(self, fighter: models.Fighter) -> float:
        """ Calculate win percentage """
        total_fights = fighter.wins + fighter.losses + fighter.draws
        if total_fights == 0:
            return 0.0
        percentage = (fighter.wins + 0.5 * fighter.draws)/total_fights * 100
        return percentage 
    
    def predict_simple(self, fighter_a_id: int, fighter_b_id: int) -> Dict:
        """
        Simple rule-based prediction model, will improve later with ML
        """
        deltas = self.compute_deltas(fighter_a_id, fighter_b_id)

        # Weighted scoring system
        score = 0.0

        # Striking advantage (25% weight)
        striking_score = (
            deltas["striking_output_diff"] * 2 +
            deltas["striking_defense_diff"] * 1.5 +
            deltas["striking_accuracy_diff"] * 1 +
            deltas["striking_absorbed_diff"] * 1
        )
        score += striking_score * 0.25

         # Grappling advantage (30% weight)
        grappling_score = (
            deltas["takedown_offense_diff"] * 3 +
            deltas["takedown_defense_diff"] * 1.5 +
            deltas["takedown_accuracy_diff"] * 1
        )

        score += grappling_score * 0.30

        # Physical attributes (15% weight)
        physical_score = (
            deltas["reach_diff_cm"] * 0.5 +
            deltas["height_diff_cm"] * 0.3
        )
        score += physical_score * 0.15

        # Experience and record (30% weight)
        record_score = (
            deltas["win_percentage_diff"] * 2 +
            deltas["experience_diff"] * 0.5
        )
        score += record_score * 0.30

         # Convert score to probability using sigmoid
        fighter_a_prob = self._sigmoid(score / 10)  # Normalize (b/w 0 and 1)
        fighter_b_prob = 1 - fighter_a_prob
        
        return {
            "fighter_a_win_probability": round(fighter_a_prob, 3),
            "fighter_b_win_probability": round(fighter_b_prob, 3),
            "confidence": self._calculate_confidence(fighter_a_prob),
            "method": "simple_rule_based",
            "deltas": deltas
        }

    def _sigmoid(self, x: float) -> float:
        """Sigmoid function to convert score to probability"""
        return 1 / (1 + math.exp(-x))
    
    def _calculate_confidence(self, prob: float) -> str:
        """Calculate confidence level based on probability"""
        margin = abs(prob - 0.5)
        if margin > 0.25:
            return "high"
        elif margin > 0.15:
            return "medium"
        else:
            return "low"