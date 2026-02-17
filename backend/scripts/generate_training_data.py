import sys
sys.path.append('..')

import pandas as pd
import numpy as np
from app.database import SessionLocal
from app.models import Fighter, FighterStats, Fight

def generate_training_data_from_db():
    """
    Build training data from fights already in the database.
    For each fight, compute the stat deltas between the two fighters
    and label with the outcome (1 = fighter_a won, 0 = fighter_b won).
    """
    db = SessionLocal()
    
    fights = db.query(Fight).all()
    rows = []
    
    for fight in fights:
        fighter_a = db.query(Fighter).filter(Fighter.id == fight.fighter_a_id).first()
        fighter_b = db.query(Fighter).filter(Fighter.id == fight.fighter_b_id).first()
        
        if not fighter_a or not fighter_b:
            continue
        if not fighter_a.stats or not fighter_b.stats:
            continue
        
        stats_a = fighter_a.stats
        stats_b = fighter_b.stats
        
        def win_pct(f):
            total = f.wins + f.losses + f.draws
            return (f.wins + 0.5 * f.draws) / total * 100 if total > 0 else 50.0
        
        row = {
            # Feature deltas (positive = fighter_a advantage)
            "reach_diff": (fighter_a.reach_cm or 0) - (fighter_b.reach_cm or 0),
            "height_diff": (fighter_a.height_cm or 0) - (fighter_b.height_cm or 0),
            "striking_output_diff": stats_a.sig_strikes_landed_per_min - stats_b.sig_strikes_landed_per_min,
            "striking_defense_diff": stats_a.striking_defense - stats_b.striking_defense,
            "striking_accuracy_diff": stats_a.striking_accuracy - stats_b.striking_accuracy,
            "striking_absorbed_diff": stats_b.sig_strikes_absorbed_per_min - stats_a.sig_strikes_absorbed_per_min,
            "takedown_offense_diff": stats_a.takedown_avg_per_fight - stats_b.takedown_avg_per_fight,
            "takedown_defense_diff": stats_a.takedown_defense - stats_b.takedown_defense,
            "takedown_accuracy_diff": stats_a.takedown_accuracy - stats_b.takedown_accuracy,
            "win_pct_diff": win_pct(fighter_a) - win_pct(fighter_b),
            "experience_diff": (fighter_a.wins + fighter_a.losses) - (fighter_b.wins + fighter_b.losses),
            # Label: 1 = fighter_a won
            "label": 1 if fight.winner_id == fight.fighter_a_id else 0
        }
        rows.append(row)
    
    db.close()
    return pd.DataFrame(rows)

def generate_synthetic_training_data(n_samples: int = 2000) -> pd.DataFrame:
    """
    Generate realistic synthetic training data when real fight history is limited.
    
    Uses real UFC statistical distributions to simulate fights:
    - Better strikers win more striking matchups
    - Better grapplers win more grappling matchups
    - Physical advantages matter but don't dominate
    - There's always randomness (upsets happen)
    """
    np.random.seed(42)
    rows = []
    
    for _ in range(n_samples):
        # Simulate realistic stat deltas using UFC stat distributions
        reach_diff          = np.random.normal(0, 8)       # cm
        height_diff         = np.random.normal(0, 4)       # cm
        striking_output     = np.random.normal(0, 1.5)     # SL/min
        striking_defense    = np.random.normal(0, 12)      # %
        striking_accuracy   = np.random.normal(0, 8)       # %
        striking_absorbed   = np.random.normal(0, 1.2)     # SL absorbed/min
        td_offense          = np.random.normal(0, 1.8)     # TDs/fight
        td_defense          = np.random.normal(0, 15)      # %
        td_accuracy         = np.random.normal(0, 12)      # %
        win_pct_diff        = np.random.normal(0, 20)      # %
        experience_diff     = np.random.normal(0, 8)       # total fights
        
        # Compute a win score based on weighted advantages
        # These weights are informed by MMA analytics research
        score = (
            striking_output    * 0.25 +
            striking_defense   * 0.15 +
            striking_accuracy  * 0.10 +
            striking_absorbed  * 0.15 +
            td_offense         * 0.10 +
            td_defense         * 0.10 +
            td_accuracy        * 0.05 +
            win_pct_diff       * 0.05 +
            reach_diff         * 0.03 +
            experience_diff    * 0.02
        )
        
        # Convert score to win probability using sigmoid + noise
        noise = np.random.normal(0, 3)  # Upsets happen
        win_prob = 1 / (1 + np.exp(-(score + noise) / 8))
        label = 1 if np.random.random() < win_prob else 0
        
        rows.append({
            "reach_diff": reach_diff,
            "height_diff": height_diff,
            "striking_output_diff": striking_output,
            "striking_defense_diff": striking_defense,
            "striking_accuracy_diff": striking_accuracy,
            "striking_absorbed_diff": striking_absorbed,
            "takedown_offense_diff": td_offense,
            "takedown_defense_diff": td_defense,
            "takedown_accuracy_diff": td_accuracy,
            "win_pct_diff": win_pct_diff,
            "experience_diff": experience_diff,
            "label": label
        })
    
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Try to use real data first, supplement with synthetic
    real_data = generate_training_data_from_db()
    print(f"Real fights in database: {len(real_data)}")
    
    synthetic_data = generate_synthetic_training_data(n_samples=2000)
    print(f"Synthetic samples generated: {len(synthetic_data)}")
    
    # Combine real + synthetic (real data weighted 10x)
    combined = pd.concat([real_data] * 10 + [synthetic_data], ignore_index=True)
    print(f"Total training samples: {len(combined)}")
    
    # Save for inspection
    combined.to_csv('../data/training_data.csv', index=False)
    print("Saved to backend/data/training_data.csv")