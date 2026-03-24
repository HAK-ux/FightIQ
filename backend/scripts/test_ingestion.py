import sys
sys.path.append('..')

from app.database import SessionLocal
from app.pipeline.ingestion import DataIngestionService
from app.models import Fighter

def test_single_fighter_update():
    db = SessionLocal()
    
    # Step 1: Check if we have a fighter to test with
    print("🔍 Finding a fighter in your database...")
    fighter = db.query(Fighter).first()
    
    if not fighter:
        print("❌ No fighters in database. Import your CSV first!")
        db.close()
        return
    
    print(f"✅ Found fighter: {fighter.name} (ID: {fighter.id})")
    print(f"   Current status: {fighter.status}")
    print(f"   Current last_fight_date: {fighter.last_fight_date}")
    
    # Step 2: Try to update this fighter
    print(f"\n🔄 Attempting to update {fighter.name} from UFCStats...")
    
    service = DataIngestionService(db)
    result = service.update_fighter(fighter.name)
    
    # Step 3: Check result
    print(f"\n📊 Result:")
    print(f"   Status: {result['status']}")
    
    if result["status"] == "success":
        print(f"   Fighter status: {result['fighter_status']}")
        print(f"   Last fight date: {result['last_fight_date']}")
        
        # Verify it actually updated in DB
        db.refresh(fighter)
        print(f"\n✅ Updated fighter in DB:")
        print(f"   New status: {fighter.status}")
        print(f"   New last_fight_date: {fighter.last_fight_date}")
        print(f"   Reach: {fighter.reach_cm}")
        print(f"   Stance: {fighter.stance}")
    elif result["status"] == "not_found":
        print(f"   ⚠️  Fighter '{fighter.name}' not in your database")
    elif result["status"] == "scrape_failed":
        print(f"   ❌ Could not scrape '{fighter.name}' from UFCStats")
        print(f"   This might mean the name doesn't match UFCStats exactly")
    
    db.close()

if __name__ == "__main__":
    test_single_fighter_update()