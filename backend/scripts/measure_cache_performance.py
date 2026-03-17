import sys
sys.path.append('..')

import requests
import random
from app.database import SessionLocal
from app.models import Fighter, MatchupCache

def measure_cache_hit_rate():
    db = SessionLocal()
    
    # Clear cache before testing
    print("🗑️  Clearing existing cache...")
    deleted = db.query(MatchupCache).delete()
    db.commit()
    print(f"   Deleted {deleted} cached predictions\n")
    
    # Get fighters
    all_fighters = db.query(Fighter).limit(50).all()
    fighter_ids = [f.id for f in all_fighters]
    
    # Simulate realistic distribution:
    # - 5 "superstar" fighters (constant attention)
    # - 10 "contender" fighters (moderate attention)  
    # - Rest are deep roster
    superstars = fighter_ids[:5]      # Top 5 most queried
    contenders = fighter_ids[5:15]    # Next 10
    deep_roster = fighter_ids[15:]
    
    total_requests = 0
    cache_hits = 0
    
    print("Simulating realistic user behavior:")
    print(f"  - 50% of queries involve superstars (top 5 fighters)")
    print(f"  - 30% involve contenders (next 10 fighters)")
    print(f"  - 20% explore deep roster\n")
    
    # Simulate 100 user queries
    for i in range(100):
        rand = random.random()
        
        if rand < 0.50:
            # 50% - Superstar matchups (high repeat probability)
            a = random.choice(superstars)
            b = random.choice(superstars + contenders)
            if a == b:
                b = random.choice(contenders)
        elif rand < 0.80:
            # 30% - Contender matchups
            a = random.choice(contenders)
            b = random.choice(contenders + superstars)
            if a == b:
                b = random.choice(superstars)
        else:
            # 20% - Deep roster exploration
            a, b = random.sample(deep_roster + contenders, 2)
        
        # Make prediction request
        response = requests.get(f"http://localhost:8000/matchup/{a}/vs/{b}/breakdown")
        data = response.json()
        
        total_requests += 1
        if data.get("from_cache"):
            cache_hits += 1
        
        status = '✓ HIT ' if data.get('from_cache') else '✗ MISS'
        print(f"Request {total_requests:3d}: {status} (Fighter {a:2d} vs {b:2d})")
    
    hit_rate = (cache_hits / total_requests) * 100
    
    print(f"\n📊 Results:")
    print(f"   Total requests: {total_requests}")
    print(f"   Cache hits: {cache_hits}")
    print(f"   Cache misses: {total_requests - cache_hits}")
    print(f"   Cache hit rate: {hit_rate:.1f}%")
    print(f"   API call reduction: ~{int(hit_rate)}%")
    
    # Show which fighters were most queried
    print(f"\n   Most queried fighter IDs: {superstars}")
    
    db.close()
    return hit_rate

if __name__ == "__main__":
    if __name__ == "__main__":
        print("Running 5 trials to get average...\n")
        results = []
        
        for trial in range(5):
            print(f"=== Trial {trial + 1}/5 ===")
            hit_rate = measure_cache_hit_rate()
            results.append(hit_rate)
            print()
        
        avg = sum(results) / len(results)
        print(f"\n📊 Final Results Across 5 Trials:")
        print(f"   Individual: {[f'{r:.1f}%' for r in results]}")
        print(f"   Average: {avg:.1f}%")
