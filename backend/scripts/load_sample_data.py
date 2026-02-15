import sys
sys.path.append('..')

from app.database import SessionLocal, engine
from app.models import Base, Fighter, FighterStats

# Create tables
Base.metadata.create_all(bind=engine)

def load_sample_fighters():
    db = SessionLocal()
    
    # Sample fighters with realistic stats
    fighters_data = [
        {
            "fighter": {
                "name": "Israel Adesanya",
                "nickname": "The Last Stylebender",
                "weight_class": "Middleweight",
                "wins": 24, "losses": 3, "draws": 0,
                "height_cm": 193, "reach_cm": 203,
                "stance": "Orthodox"
            },
            "stats": {
                "sig_strikes_landed_per_min": 4.81,
                "sig_strikes_absorbed_per_min": 2.66,
                "striking_accuracy": 52,
                "striking_defense": 61,
                "takedown_avg_per_fight": 0.14,
                "takedown_accuracy": 33,
                "takedown_defense": 81
            }
        },
        {
            "fighter": {
                "name": "Alex Pereira",
                "nickname": "Poatan",
                "weight_class": "Light Heavyweight",
                "wins": 11, "losses": 2, "draws": 0,
                "height_cm": 193, "reach_cm": 201,
                "stance": "Orthodox"
            },
            "stats": {
                "sig_strikes_landed_per_min": 5.23,
                "sig_strikes_absorbed_per_min": 3.87,
                "striking_accuracy": 58,
                "striking_defense": 54,
                "takedown_avg_per_fight": 0.00,
                "takedown_accuracy": 0,
                "takedown_defense": 92
            }
        },
        {
            "fighter": {
                "name": "Islam Makhachev",
                "nickname": "Dagestani Destroyer",
                "weight_class": "Lightweight",
                "wins": 26, "losses": 1, "draws": 0,
                "height_cm": 178, "reach_cm": 178,
                "stance": "Orthodox"
            },
            "stats": {
                "sig_strikes_landed_per_min": 3.40,
                "sig_strikes_absorbed_per_min": 1.94,
                "striking_accuracy": 48,
                "striking_defense": 60,
                "takedown_avg_per_fight": 4.54,
                "takedown_accuracy": 52,
                "takedown_defense": 90
            }
        },
    ]
    
    for data in fighters_data:
        fighter = Fighter(**data["fighter"])
        db.add(fighter)
        db.flush()  # Get the fighter ID
        
        stats = FighterStats(fighter_id=fighter.id, **data["stats"])
        db.add(stats)
    
    db.commit()
    print(f"Loaded {len(fighters_data)} sample fighters")
    db.close()

if __name__ == "__main__":
    load_sample_fighters()