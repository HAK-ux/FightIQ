import sys
sys.path.append('..')

import pandas as pd
from datetime import datetime
from app.database import SessionLocal
from app.models import Fighter, Fight

def import_fights_from_csv(filepath='../data/fights.csv'):
    db = SessionLocal()
    
    df = pd.read_csv(filepath)
    print(f"Found {len(df)} fights in CSV")
    
    imported = 0
    for _, row in df.iterrows():
        # Find fighters by name
        fighter_a = db.query(Fighter).filter(
            Fighter.name == row['fighter_a_name']
        ).first()
        
        fighter_b = db.query(Fighter).filter(
            Fighter.name == row['fighter_b_name']
        ).first()
        
        winner = db.query(Fighter).filter(
            Fighter.name == row['winner_name']
        ).first()
        
        if not fighter_a or not fighter_b or not winner:
            print(f"Skipping fight - couldn't find all fighters")
            continue
        
        # Check if fight already exists
        existing = db.query(Fight).filter(
            Fight.fighter_a_id == fighter_a.id,
            Fight.fighter_b_id == fighter_b.id,
            Fight.event_name == row['event_name']
        ).first()
        
        if existing:
            print(f"Fight already exists: {row['event_name']}")
            continue
        
        fight = Fight(
            fighter_a_id=fighter_a.id,
            fighter_b_id=fighter_b.id,
            winner_id=winner.id,
            fight_date=datetime.strptime(row['fight_date'], '%Y-%m-%d').date(),
            method=row['method'],
            round=int(row['round']),
            event_name=row['event_name']
        )
        
        db.add(fight)
        imported += 1
        print(f"Imported: {fighter_a.name} vs {fighter_b.name}")
    
    db.commit()
    print(f"\nSuccessfully imported {imported} fights")
    db.close()

if __name__ == "__main__":
    import_fights_from_csv()