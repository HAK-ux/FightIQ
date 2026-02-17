from sqlalchemy.orm import Session
from . import models
from typing import Dict
from datetime import datetime, timedelta, timezone
import math
import os
import joblib
import numpy as np

# Path to trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'fight_predictor.joblib')

class MatchupEngine():
    """
    Computes feature deltas between two fighters and generates predictions.
    Supports rule-based fallback and ML model prediction.
    """
    def __init__(self, db: Session):
        self.db = db
        self.ml_model = self._load_model()

    def _load_model(self):
        """Load the trained ML model if available."""
        if os.path.exists(MODEL_PATH):
            try:
                model_data = joblib.load(MODEL_PATH)
                print(f"✅ ML model loaded: {model_data['model_name']} (AUC: {model_data['auc_score']:.3f})")
                return model_data
            except Exception as e:
                print(f"⚠️  Could not load ML model: {e}. Falling back to rule-based.")
                return None
        print("⚠️  No ML model found. Using rule-based fallback.")
        return None

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
        return (fighter.wins + 0.5 * fighter.draws) / total_fights * 100

    # -------------------------
    # Prediction Methods
    # -------------------------

    def predict_simple(self, fighter_a_id: int, fighter_b_id: int, use_cache: bool = True) -> Dict:
        """
        Generate prediction using ML model if available,
        otherwise fall back to rule-based scoring.
        """
        if use_cache:
            cached = self._get_cached_prediction(fighter_a_id, fighter_b_id)
            if cached:
                return cached

        deltas = self.compute_deltas(fighter_a_id, fighter_b_id)

        # Choose prediction method
        if self.ml_model:
            result = self._predict_ml(deltas)
        else:
            result = self._predict_rule_based(deltas)

        # Attach deltas to result
        result["deltas"] = deltas

        if use_cache:
            self._cache_prediction(fighter_a_id, fighter_b_id, result)

        return result

    def _predict_ml(self, deltas: Dict) -> Dict:
        """Use trained ML model for prediction."""
        pipeline = self.ml_model['pipeline']

        # Feature vector must match the order used in training
        features = np.array([[
            deltas["reach_diff_cm"],
            deltas["height_diff_cm"],
            deltas["striking_output_diff"],
            deltas["striking_defense_diff"],
            deltas["striking_accuracy_diff"],
            deltas["striking_absorbed_diff"],
            deltas["takedown_offense_diff"],
            deltas["takedown_defense_diff"],
            deltas["takedown_accuracy_diff"],
            deltas["win_percentage_diff"],
            deltas["experience_diff"]
        ]])

        probs = pipeline.predict_proba(features)[0]
        fighter_a_prob = float(probs[1])
        fighter_b_prob = float(probs[0])

        return {
            "fighter_a_win_probability": round(fighter_a_prob, 3),
            "fighter_b_win_probability": round(fighter_b_prob, 3),
            "confidence": self._calculate_confidence(fighter_a_prob),
            "method": f"ml_{self.ml_model['model_name']}",
        }

    def _predict_rule_based(self, deltas: Dict) -> Dict:
        """Fallback rule-based prediction."""
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

        fighter_a_prob = self._sigmoid(score / 10)

        return {
            "fighter_a_win_probability": round(fighter_a_prob, 3),
            "fighter_b_win_probability": round(1 - fighter_a_prob, 3),
            "confidence": self._calculate_confidence(fighter_a_prob),
            "method": "rule_based_fallback",
        }

    # -------------------------
    # Helper Methods
    # -------------------------

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

    # -------------------------
    # Cache Methods
    # -------------------------

    def predict_with_breakdown(self, fighter_a_id: int, fighter_b_id: int, use_cache: bool = True) -> Dict:
        """Generate prediction with cached breakdown if available."""
        if use_cache:
            cached = self._get_cached_breakdown(fighter_a_id, fighter_b_id)
            if cached:
                return cached

        # Generate fresh prediction
        prediction = self.predict_simple(fighter_a_id, fighter_b_id, use_cache=False)
        return prediction

    def _get_cached_prediction(self, fighter_a_id: int, fighter_b_id: int):
        """Check if we have a recent cached prediction"""
        cache_entry = self.db.query(models.MatchupCache).filter(
            models.MatchupCache.fighter_a_id == fighter_a_id,
            models.MatchupCache.fighter_b_id == fighter_b_id,
            models.MatchupCache.model_version == "v2_ml"
        ).first()

        if cache_entry:
            # Use timezone-aware datetime
            now = datetime.now(timezone.utc)
            created_at = cache_entry.created_at
            
            # Make created_at timezone-aware if it isn't
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            # Cache is valid for 7 days
            if now - created_at < timedelta(days=7):
                return cache_entry.prediction_data
        
        return None
    
    def _cache_prediction(self, fighter_a_id: int, fighter_b_id: int, prediction: Dict):
        existing = self.db.query(models.MatchupCache).filter(
            models.MatchupCache.fighter_a_id == fighter_a_id,
            models.MatchupCache.fighter_b_id == fighter_b_id,
            models.MatchupCache.model_version == "v2_ml"
        ).first()

        if existing:
            existing.prediction_data = prediction
            existing.created_at = datetime.now(timezone.utc)
        else:
            self.db.add(models.MatchupCache(
                fighter_a_id=fighter_a_id,
                fighter_b_id=fighter_b_id,
                prediction_data=prediction,
                model_version="v2_ml",
                created_at=datetime.now(timezone.utc)
            ))

        self.db.commit()

    def _get_cached_breakdown(self, fighter_a_id: int, fighter_b_id: int):
        """Check cache for complete breakdown including AI text"""
        cache_entry = self.db.query(models.MatchupCache).filter(
            models.MatchupCache.fighter_a_id == fighter_a_id,
            models.MatchupCache.fighter_b_id == fighter_b_id,
            models.MatchupCache.model_version == "v2_ml",
            models.MatchupCache.breakdown_text.isnot(None)
        ).first()

        if cache_entry:
            # Use timezone-aware datetime
            now = datetime.now(timezone.utc)
            created_at = cache_entry.created_at
            
            # Make created_at timezone-aware if it isn't
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            # Cache valid for 7 days
            if now - created_at < timedelta(days=7):
                return {
                    **cache_entry.prediction_data,
                    "breakdown": cache_entry.breakdown_text,
                    "fighter_a_win_condition": cache_entry.fighter_a_win_condition,
                    "fighter_b_win_condition": cache_entry.fighter_b_win_condition
                }
        
        return None

    def _cache_breakdown(self, fighter_a_id: int, fighter_b_id: int,
                         prediction: Dict, breakdown: str, win_conditions: Dict):
        """Store prediction + AI breakdown + win conditions"""
        
        existing = self.db.query(models.MatchupCache).filter(
            models.MatchupCache.fighter_a_id == fighter_a_id,
            models.MatchupCache.fighter_b_id == fighter_b_id,
            models.MatchupCache.model_version == "v2_ml"
        ).first()

        if existing:
            # Update existing cache
            existing.breakdown_text = breakdown
            existing.prediction_data = prediction
            existing.fighter_a_win_condition = win_conditions["fighter_a_win_condition"]
            existing.fighter_b_win_condition = win_conditions["fighter_b_win_condition"]
            existing.created_at = datetime.now(timezone.utc)
        else:
            self.db.add(models.MatchupCache(
                fighter_a_id=fighter_a_id,
                fighter_b_id=fighter_b_id,
                prediction_data=prediction,
                breakdown_text=breakdown,
                fighter_a_win_condition=win_conditions["fighter_a_win_condition"],
                fighter_b_win_condition=win_conditions["fighter_b_win_condition"],
                model_version="v2_ml",
                created_at=datetime.now(timezone.utc)
            ))

        self.db.commit()