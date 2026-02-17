import sys
sys.path.append('..')
import math
from app.database import SessionLocal
from app.models import FighterStats

def clean_nan_stats():
    db = SessionLocal()
    stats = db.query(FighterStats).all()
    
    fixed = 0
    for s in stats:
        changed = False
        
        float_fields = [
            'sig_strikes_landed_per_min',
            'sig_strikes_absorbed_per_min',
            'striking_accuracy',
            'striking_defense',
            'takedown_avg_per_fight',
            'takedown_accuracy',
            'takedown_defense',
            'submission_avg_per_fight'
        ]
        
        for field in float_fields:
            val = getattr(s, field)
            if val is not None and (math.isnan(val) or math.isinf(val)):
                setattr(s, field, 0.0)
                changed = True
        
        if changed:
            fixed += 1
    
    db.commit()
    db.close()
    print(f"Fixed {fixed} fighters with NaN stats")

if __name__ == "__main__":
    clean_nan_stats()