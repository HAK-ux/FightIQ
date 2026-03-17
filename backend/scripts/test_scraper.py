import sys
sys.path.append('..')

from app.pipeline.ufcstats_scraper import UFCStatsScraper
from app.pipeline.ufcstats_scraper import UFCStatsScraper


def test_scraper():
    scraper = UFCStatsScraper()

    # Test 1: Search for a fighter
    print("🔍 Test 1: Finding Jon Jones...")
    fighter_url = scraper.find_fighter_url("Jon Jones")
    if fighter_url:
        print(f"✅ Found URL: {fighter_url}\n")
    else:
        print("❌ Could not find Jon Jones\n")
        return

    # Test 2: Scrape full fighter data
    print("📊 Test 2: Scraping Jon Jones stats...")
    fighter_data = scraper.scrape_fighter("Jon Jones")

    if fighter_data:
        print("✅ Scrape successful!\n")
        print("Data received:")
        for key, value in fighter_data.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Scrape failed\n")
        return

    # Test 3: Get recent events
    print("\n📅 Test 3: Getting recent events...")
    events = scraper.get_recent_events(limit=3)
    if events:
        print(f"✅ Found {len(events)} events:\n")
        for event in events:
            print(f"  - {event['name']} ({event['date']})")
    else:
        print("❌ Could not fetch recent events\n")
        return

    # Test 4: Search for a specific event
    print("\n🎟️ Test 4: Finding event '314'...")
    event_url = scraper.find_event_url("314")
    if event_url:
        print(f"✅ Found event URL: {event_url}\n")
    else:
        print("❌ Could not find event 314\n")
        return

    # Test 5: Get fighters from that event
    print("🥊 Test 5: Getting fighters from event...")
    event_fighters = scraper.get_event_fighters(event_url)
    if event_fighters:
        print(f"✅ Found {len(event_fighters)} fighters:\n")
        for fighter in event_fighters[:10]:
            print(f"  - {fighter}")
        if len(event_fighters) > 10:
            print("  ...")
    else:
        print("❌ Could not fetch fighters from event\n")


if __name__ == "__main__":
    test_scraper()