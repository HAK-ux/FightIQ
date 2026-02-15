import sys
sys.path.append('..')

import pandas as pd
from app.database import SessionLocal
from app.models import Fighter, FighterStats

def import_from_csv(filepath='../data/fighters.csv'):
    db = SessionLocal()
    
    # Read CSV
    df = pd.read_csv(filepath)
    
    print(f"Found {len(df)} fighters in CSV")
    
    imported = 0
    for _, row in df.iterrows():
        # Check if fighter already exists
        existing = db.query(Fighter).filter(
            Fighter.name == row['name']
        ).first()
        
        if existing:
            print(f"Skipping {row['name']} (already exists)")
            continue
        
        # Create fighter
        fighter = Fighter(
            name=row['name'],
            nickname=row['nickname'] if pd.notna(row['nickname']) else None,
            weight_class=row['weight_class'],
            wins=int(row['wins']),
            losses=int(row['losses']),
            draws=int(row['draws']),
            height_cm=float(row['height_cm']) if pd.notna(row['height_cm']) else None,
            reach_cm=float(row['reach_cm']) if pd.notna(row['reach_cm']) else None,
            stance=row['stance'] if pd.notna(row['stance']) else None
        )
        db.add(fighter)
        db.flush()
        
        # Create stats
        stats = FighterStats(
            fighter_id=fighter.id,
            sig_strikes_landed_per_min=float(row['sig_strikes_landed_per_min']),
            sig_strikes_absorbed_per_min=float(row['sig_strikes_absorbed_per_min']),
            striking_accuracy=float(row['striking_accuracy']),
            striking_defense=float(row['striking_defense']),
            takedown_avg_per_fight=float(row['takedown_avg_per_fight']),
            takedown_accuracy=float(row['takedown_accuracy']),
            takedown_defense=float(row['takedown_defense']),
            submission_avg_per_fight=float(row['submission_avg_per_fight']) if 'submission_avg_per_fight' in row else 0.0
        )
        db.add(stats)
        
        imported += 1
        print(f"Imported {row['name']}")
    
    db.commit()
    print(f"\nSuccessfully imported {imported} fighters")
    db.close()

if __name__ == "__main__":
    import_from_csv()
