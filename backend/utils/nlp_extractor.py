import re
from datetime import datetime, timedelta
from typing import Dict

class NLPExtractor:

    @staticmethod
    def extract_all(text: str) -> Dict:
        return {
            "date": NLPExtractor.extract_date(text),
            "time": NLPExtractor.extract_time(text),
            "duration": NLPExtractor.extract_duration(text)
        }

    @staticmethod
    def extract_date(text: str):
        tl = text.lower()

        # 🔥 Handle "tomorrow" and common misspellings
        tomorrow_patterns = [
            "tomorrow", "tommorow", "tmrw", "tmr", "tommorrow"
        ]
        for word in tomorrow_patterns:
            if word in tl:
                return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        if "today" in tl:
            return datetime.now().strftime("%Y-%m-%d")

        # Weekdays support
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for day, num in weekdays.items():
            if day in tl:
                today = datetime.now()
                days_ahead = num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        return None

    @staticmethod
    def extract_time(text: str):
        tl = text.lower()

        # Time ranges first
        range_match = re.search(r'from\s+(\d{1,2})[:.\-]?\d*\s*(am|pm)?', tl)
        if range_match:
            hour = int(range_match.group(1))
            if range_match.group(2) == 'pm' and hour != 12:
                hour += 12
            return f"{hour:02d}:00"

        m = re.search(r'(\d{1,2})[:.]?(\d{2})?\s*(am|pm)', tl)
        if m:
            h = int(m.group(1))
            min = int(m.group(2) or 0)
            if m.group(3) == 'pm' and h != 12: h += 12
            if m.group(3) == 'am' and h == 12: h = 0
            return f"{h:02d}:{min:02d}"

        return None

    @staticmethod
    def extract_duration(text: str):
        tl = text.lower()

        m = re.search(r'(\d+)\s*(minutes?|mins?)', tl)
        if m: return int(m.group(1))

        m = re.search(r'(\d+)\s*(hours?|hrs?)', tl)
        if m: return int(m.group(1)) * 60

        m = re.search(r'(\d{1,2})[:.]?(\d{2})?\s*(am|pm)?.*to\s*(\d{1,2})[:.]?(\d{2})', tl)
        if m:
            sh, sm = int(m.group(1)), int(m.group(2) or 0)
            eh, em = int(m.group(4)), int(m.group(5))
            return max((eh*60+em) - (sh*60+sm), 60)

        return 60
