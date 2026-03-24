from sqlalchemy.orm import Session
from typing import Dict, Optional
from ..models import Fighter, FighterStats, MatchupCache
from .ufcstats_scraper import UFCStatsScraper

class DataIngestionService:
    """
    Orchestrates syncing fighter data from UFCStats into the FightIQ database.
    """

    def __init__(self, db: Session):
        self.db = db
        self.scraper = UFCStatsScraper()

    # ---------------------------
    # Single Fighter Update
    # ---------------------------

    def update_fighter(self, name: str) -> Dict:
        """
        Scrape and update a single fighter.
        Only updates fighters that already exist in your DB.
        """
        # Check fighter exists
        fighter = self.db.query(Fighter).filter(
            Fighter.name == name
        ).first()

        if not fighter:
            return {"status": "not_found", "name": name}

        # Scrape fresh data
        print(f"\n🔄 Updating: {name}")
        scraped = self.scraper.scrape_fighter(name)
        
        if not scraped:
            return {"status": "scrape_failed", "name": name}

        # Update fighter record
        self._apply_fighter_update(fighter, scraped)

        # Invalidate cached predictions for this fighter
        self._invalidate_cache(fighter.id)

        self.db.commit()
        print(f"  ✅ Updated: {name} (status: {fighter.status})")

        return {
            "status": "success",
            "name": name,
            "fighter_status": fighter.status,
            "last_fight_date": str(fighter.last_fight_date) if fighter.last_fight_date else None
        }

    def _apply_fighter_update(self, fighter: Fighter, scraped: Dict):
        """Apply scraped data to fighter + stats records."""

        # Update physical attributes if we got them
        if scraped.get("height_cm"):
            fighter.height_cm = scraped["height_cm"]
        if scraped.get("reach_cm"):
            fighter.reach_cm = scraped["reach_cm"]
        if scraped.get("stance"):
            fighter.stance = scraped["stance"]

        # Always update status + last fight date
        fighter.status = scraped.get("status", "unknown")
        if scraped.get("last_fight_date"):
            fighter.last_fight_date = scraped["last_fight_date"]

        # Update performance stats
        stats = self.db.query(FighterStats).filter(
            FighterStats.fighter_id == fighter.id
        ).first()

        if not stats:
            stats = FighterStats(fighter_id=fighter.id)
            self.db.add(stats)

        # Only update stats if we got data
        if scraped.get("sig_strikes_landed_per_min") is not None:
            stats.sig_strikes_landed_per_min = scraped["sig_strikes_landed_per_min"]
        if scraped.get("sig_strikes_absorbed_per_min") is not None:
            stats.sig_strikes_absorbed_per_min = scraped["sig_strikes_absorbed_per_min"]
        if scraped.get("striking_accuracy") is not None:
            stats.striking_accuracy = scraped["striking_accuracy"]
        if scraped.get("striking_defense") is not None:
            stats.striking_defense = scraped["striking_defense"]
        if scraped.get("takedown_avg_per_fight") is not None:
            stats.takedown_avg_per_fight = scraped["takedown_avg_per_fight"]
        if scraped.get("takedown_accuracy") is not None:
            stats.takedown_accuracy = scraped["takedown_accuracy"]
        if scraped.get("takedown_defense") is not None:
            stats.takedown_defense = scraped["takedown_defense"]
        if scraped.get("submission_avg_per_fight") is not None:
            stats.submission_avg_per_fight = scraped["submission_avg_per_fight"]

    # ---------------------------
    # Bulk Updates
    # ---------------------------

    def update_after_event(self, event_query: str) -> Dict:
        """
        Update all fighters who fought in a specific event.
        Run this the day after each UFC event.
        
        Example: update_after_event("UFC 314") or update_after_event("314")
        """
        print(f"\n🔍 Finding event: {event_query}")
        
        # Find the event URL
        event_url = self.scraper.find_event_url(event_query)
        if not event_url:
            return {"error": f"Could not find event '{event_query}'"}

        print(f"📅 Found event URL: {event_url}")

        # Get fighters from this event
        fighter_names = self.scraper.get_event_fighters(event_url)
        if not fighter_names:
            return {"error": "No fighters found for this event"}

        print(f"  Found {len(fighter_names)} fighters on card\n")

        results = {
            "event": event_query,
            "fighters_updated": [],
            "fighters_not_found": [],
            "errors": []
        }

        for name in fighter_names:
            result = self.update_fighter(name)

            if result["status"] == "success":
                results["fighters_updated"].append(name)
            elif result["status"] == "not_found":
                results["fighters_not_found"].append(name)
            else:
                results["errors"].append(f"{name}: {result['status']}")

        print(f"\n✅ Done: {len(results['fighters_updated'])} updated, "
              f"{len(results['fighters_not_found'])} not in DB")

        return results

    def update_recent_events(self, limit: int = 1) -> Dict:
        """
        Update fighters from the N most recent UFC events.
        Run this weekly to stay current.
        """
        print(f"\n🔄 Syncing {limit} most recent events...")
        
        events = self.scraper.get_recent_events(limit=limit)
        if not events:
            return {"error": "Could not fetch recent events"}

        total_results = {
            "events_synced": [],
            "total_fighters_updated": 0,
            "total_fighters_not_found": 0,
            "errors": []
        }

        for event in events:
            print(f"\n📅 Processing: {event['name']}")
            
            fighter_names = self.scraper.get_event_fighters(event["url"])
            print(f"  Found {len(fighter_names)} fighters on card")

            for name in fighter_names:
                result = self.update_fighter(name)

                if result["status"] == "success":
                    total_results["total_fighters_updated"] += 1
                elif result["status"] == "not_found":
                    total_results["total_fighters_not_found"] += 1
                else:
                    total_results["errors"].append(f"{name}: {result['status']}")

            total_results["events_synced"].append(event["name"])

        print(f"\n✅ Synced {len(total_results['events_synced'])} events, "
              f"{total_results['total_fighters_updated']} fighters updated")

        return total_results

    # ---------------------------
    # Cache Management
    # ---------------------------

    def _invalidate_cache(self, fighter_id: int):
        """Clear stale predictions after a fighter update."""
        # Normalize order: min ID first, max ID second
        deleted_a = self.db.query(MatchupCache).filter(
            MatchupCache.fighter_a_id == fighter_id
        ).delete()
        
        deleted_b = self.db.query(MatchupCache).filter(
            MatchupCache.fighter_b_id == fighter_id
        ).delete()
        
        total_deleted = deleted_a + deleted_b
        
        if total_deleted:
            print(f"  🗑️  Cleared {total_deleted} cached predictions")