import requests
import math
import time
from bs4 import BeautifulSoup
from datetime import datetime, date
from typing import Dict, Optional, List


BASE_URL = "http://ufcstats.com"


class UFCStatsScraper:
    """
    Scrapes fighter stats, status, and fight history from UFCStats.com.
    Used to keep existing fighters fresh after new events.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    # ---------------------------
    # Helpers
    # ---------------------------

    def safe_float(self, val: str, default=0.0) -> float:
        if not val:
            return default
        try:
            result = float(str(val).replace('%', '').replace('---', '').strip())
            return default if (math.isnan(result) or math.isinf(result)) else result
        except (ValueError, TypeError):
            return default

    def normalize_name(self, name: str) -> str:
        return " ".join(name.lower().strip().split())

    def _get(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        """Fetch a page and return parsed soup. Polite 0.5s delay."""
        try:
            time.sleep(0.5)
            response = self.session.get(url, params=params, timeout=10)
            print(f"  GET {response.url} -> {response.status_code}")
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"  ⚠️  Request failed: {url} params={params} → {e}")
            return None

    # ---------------------------
    # Fighter Search
    # ---------------------------

    def search_fighters(self, query: str) -> List[Dict]:
        """
        Search UFCStats fighters directory using a broad query and
        return candidate fighters.
        """
        search_url = f"{BASE_URL}/statistics/fighters/search"
        soup = self._get(search_url, params={"query": query})
        if not soup:
            return []

        fighters = []
        rows = soup.select("table.b-statistics__table tbody tr")

        for row in rows:
            cols = row.select("td")
            if len(cols) < 3:
                continue

            first_name = cols[0].get_text(" ", strip=True)
            last_name = cols[1].get_text(" ", strip=True)
            nickname = cols[2].get_text(" ", strip=True)

            link = row.select_one("a.b-link")
            if not link or not link.get("href"):
                continue

            full_name = f"{first_name} {last_name}".strip()

            fighters.append({
                "first_name": first_name,
                "last_name": last_name,
                "nickname": nickname,
                "full_name": full_name,
                "url": link["href"],
            })

        return fighters

    def find_fighter_url(self, name: str) -> Optional[str]:
        """
        Search UFCStats using a broad query, then match the exact fighter locally.
        Strategy:
        1. Search by first name
        2. Fallback to last name
        3. Fallback to full name
        """
        parts = name.strip().split()
        if not parts:
            return None

        target = self.normalize_name(name)

        queries = []
        first_name = parts[0]
        last_name = parts[-1]

        queries.append(first_name)
        if last_name != first_name:
            queries.append(last_name)
        if self.normalize_name(name) not in {self.normalize_name(q) for q in queries}:
            queries.append(name)

        seen_urls = set()
        candidates = []

        for query in queries:
            results = self.search_fighters(query)

            for fighter in results:
                fighter_url = fighter["url"]
                if fighter_url in seen_urls:
                    continue
                seen_urls.add(fighter_url)

                candidates.append(fighter)

                full_name = self.normalize_name(fighter["full_name"])
                if full_name == target:
                    return fighter_url

        # Partial fallback
        for fighter in candidates:
            full_name = self.normalize_name(fighter["full_name"])
            if target in full_name or full_name in target:
                return fighter["url"]

        return None

    # ---------------------------
    # Fighter Profile
    # ---------------------------

    def scrape_fighter(self, name: str) -> Optional[Dict]:
        """
        Full scrape of a fighter profile.
        Returns dict with stats, status, reach, stance, last_fight_date.
        """
        profile_url = self.find_fighter_url(name)
        if not profile_url:
            print(f"  ⚠️  '{name}' not found on UFCStats")
            return None

        soup = self._get(profile_url)
        if not soup:
            return None

        result = {
            "name": name,
            "ufcstats_url": profile_url,
        }

        # --- Performance Stats ---
        for item in soup.select("li.b-list__box-list-item"):
            title_el = item.select_one("i.b-list__box-item-title")
            if not title_el:
                continue

            title = title_el.text.strip().lower()
            value = item.text.replace(title_el.text, "").strip()

            if "slpm" in title:
                result["sig_strikes_landed_per_min"] = self.safe_float(value)
            elif "str. acc" in title:
                result["striking_accuracy"] = self.safe_float(value)
            elif "sapm" in title:
                result["sig_strikes_absorbed_per_min"] = self.safe_float(value)
            elif "str. def" in title:
                result["striking_defense"] = self.safe_float(value)
            elif "td avg" in title:
                result["takedown_avg_per_fight"] = self.safe_float(value)
            elif "td acc" in title:
                result["takedown_accuracy"] = self.safe_float(value)
            elif "td def" in title:
                result["takedown_defense"] = self.safe_float(value)
            elif "sub. avg" in title:
                result["submission_avg_per_fight"] = self.safe_float(value)
            elif "reach" in title:
                reach_inches = self.safe_float(value.replace('"', ''))
                if reach_inches > 0:
                    result["reach_cm"] = round(reach_inches * 2.54, 1)
            elif "height" in title:
                result["height_cm"] = self._parse_height(value)
            elif "stance" in title and value and value != "--":
                result["stance"] = value

        # --- Fight History → last fight date + derive status ---
        last_fight_date = self._scrape_last_fight_date(soup)
        if last_fight_date:
            result["last_fight_date"] = last_fight_date
            result["status"] = self._derive_status(last_fight_date)
        else:
            result["status"] = "unknown"

        return result

    def _scrape_last_fight_date(self, soup: BeautifulSoup) -> Optional[date]:
        """
        Parse fight history table to find most recent fight date.
        UFCStats lists fights in reverse chronological order so first row = latest.
        """
        rows = soup.select("table.b-fight-details__table tbody tr")
        
        for row in rows:
            # Look for <p class="b-fight-details__table-text"> elements
            date_elements = row.select("p.b-fight-details__table-text")
            
            for elem in date_elements:
                text = elem.get_text(strip=True)
                
                # Skip empty or very short text
                if not text or len(text) < 8:
                    continue
                
                # Check if it contains a month name (indicates it's a date)
                if not any(month in text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    continue
                
                # Try parsing the date
                try:
                    return datetime.strptime(text, "%b. %d, %Y").date()
                except ValueError:
                    try:
                        return datetime.strptime(text, "%b %d, %Y").date()
                    except ValueError:
                        try:
                            # Try without period
                            cleaned = text.replace('.', ' ').strip()
                            # Handle multiple spaces
                            cleaned = ' '.join(cleaned.split())
                            return datetime.strptime(cleaned, "%b %d, %Y").date()
                        except ValueError:
                            continue
        
        return None

    def _derive_status(self, last_fight_date: date) -> str:
        """
        Derive fighter status from how long ago they last fought.
        UFCStats doesn't expose status directly so we infer it.
        """
        if not last_fight_date:
            return "unknown"

        days_since = (date.today() - last_fight_date).days

        if days_since <= 548:
            return "active"
        elif days_since <= 1095:
            return "inactive"
        else:
            return "retired"

    def _parse_height(self, height_str: str) -> Optional[float]:
        """Convert 6'1" to cm."""
        try:
            cleaned = height_str.replace('"', '').strip()
            parts = cleaned.split("'")
            feet = int(parts[0].strip())
            inches = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
            return round((feet * 12 + inches) * 2.54, 1)
        except Exception:
            return None

    # ---------------------------
    # Event Scraping
    # ---------------------------

    def get_recent_events(self, limit: int = 5) -> List[Dict]:
        """
        Get most recent completed UFC events.
        """
        url = f"{BASE_URL}/statistics/events/completed?page=all"
        soup = self._get(url)

        if not soup:
            return []

        events = []
        seen = set()

        links = soup.select('a[href*="event-details"]')

        for link in links:
            href = link.get("href")
            name = link.get_text(" ", strip=True)

            if not href or not name or href in seen:
                continue

            seen.add(href)

            row = link.find_parent("tr")
            date_text = ""

            if row:
                cols = row.select("td")
                for col in cols:
                    text = col.get_text(" ", strip=True)
                    if "," in text:
                        date_text = text
                        break

            events.append({
                "name": name,
                "url": href,
                "date": date_text
            })

            if len(events) >= limit:
                break

        return events


    def search_events(self, query: str) -> List[Dict]:
        """
        Search UFCStats events by query and return candidate events.
        """
        search_url = f"{BASE_URL}/statistics/events/search"
        soup = self._get(search_url, params={"query": query})

        if not soup:
            return []

        events = []
        seen = set()

        links = soup.select('a[href*="event-details"]')

        for link in links:
            href = link.get("href")
            name = link.get_text(" ", strip=True)

            if not href or not name or href in seen:
                continue

            seen.add(href)

            row = link.find_parent("tr")
            date_text = ""

            if row:
                cols = row.select("td")
                for col in cols:
                    text = col.get_text(" ", strip=True)
                    if "," in text:
                        date_text = text
                        break

            events.append({
                "name": name,
                "url": href,
                "date": date_text
            })

        return events


    def find_event_url(self, event_query: str) -> Optional[str]:
        """
        Resolve an event query like '314' or 'UFC 314' to the final event-details URL.
        """
        target = self.normalize_name(event_query)
        results = self.search_events(event_query)

        # Exact match first
        for event in results:
            event_name = self.normalize_name(event["name"])
            if event_name == target:
                return event["url"]

        # Numeric special case: "314" should match "UFC 314: ..."
        for event in results:
            event_name = self.normalize_name(event["name"])
            if target in event_name:
                return event["url"]

        # Reverse partial fallback
        for event in results:
            event_name = self.normalize_name(event["name"])
            if event_name in target:
                return event["url"]

        return None


    def get_event_fighters(self, event_url: str) -> List[str]:
        """
        Get all fighters appearing on an event card.
        """
        soup = self._get(event_url)

        if not soup:
            return []

        fighter_names = []
        seen = set()

        links = soup.select('a[href*="fighter-details"]')

        for link in links:
            name = " ".join(link.get_text(" ", strip=True).split())
            normalized = self.normalize_name(name)

            if name and normalized not in seen:
                seen.add(normalized)
                fighter_names.append(name)

        return fighter_names