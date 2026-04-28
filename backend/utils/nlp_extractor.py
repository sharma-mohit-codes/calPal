import re
from datetime import datetime, timedelta
from typing import Dict

WEEKDAYS = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6
}

MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

def _next_weekday(target_weekday: int, force_next: bool = False) -> datetime:
    """Return the next occurrence of target_weekday (0=Mon...6=Sun).
    If force_next=True, always returns a future week (used for 'next X')."""
    now = datetime.now()
    days_ahead = target_weekday - now.weekday()
    if days_ahead < 0 or (days_ahead == 0 and force_next):
        days_ahead += 7
    elif days_ahead == 0 and not force_next:
        # "this monday" when today is monday → today
        pass
    return now + timedelta(days=days_ahead)

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
        now = datetime.now()

        # Explicit keywords
        if "tomorrow" in tl:
            return (now + timedelta(days=1)).strftime("%Y-%m-%d")
        if "today" in tl or "tonight" in tl:
            return now.strftime("%Y-%m-%d")
        if "yesterday" in tl:
            return (now - timedelta(days=1)).strftime("%Y-%m-%d")

        # "next week"
        if "next week" in tl:
            return (now + timedelta(weeks=1)).strftime("%Y-%m-%d")

        # "in X days" / "in X weeks"
        m = re.search(r'\bin\s+(\d+)\s+days?\b', tl)
        if m:
            return (now + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")
        m = re.search(r'\bin\s+(\d+)\s+weeks?\b', tl)
        if m:
            return (now + timedelta(weeks=int(m.group(1)))).strftime("%Y-%m-%d")

        # "next <weekday>" → always the coming week
        m = re.search(r'\bnext\s+(' + '|'.join(WEEKDAYS.keys()) + r')\b', tl)
        if m:
            dt = _next_weekday(WEEKDAYS[m.group(1)], force_next=True)
            return dt.strftime("%Y-%m-%d")

        # "this <weekday>" → nearest occurrence this week (or today)
        m = re.search(r'\bthis\s+(' + '|'.join(WEEKDAYS.keys()) + r')\b', tl)
        if m:
            dt = _next_weekday(WEEKDAYS[m.group(1)], force_next=False)
            return dt.strftime("%Y-%m-%d")

        # Bare weekday name (e.g. "on friday", "schedule for monday") → this or next occurrence
        # If today matches the target weekday, return today; otherwise next occurrence
        weekday_pattern = r'\b(' + '|'.join(WEEKDAYS.keys()) + r')\b'
        m = re.search(weekday_pattern, tl)
        if m:
            target = WEEKDAYS[m.group(1)]
            days_ahead = target - now.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        # "<Month> <day>" or "<day> <Month>" e.g. "April 30", "30th April"
        month_pat = '|'.join(MONTHS.keys())
        m = re.search(r'\b(' + month_pat + r')\s+(\d{1,2})(?:st|nd|rd|th)?\b', tl)
        if not m:
            m = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(' + month_pat + r')\b', tl)
            if m:
                day_num = int(m.group(1))
                month_num = MONTHS[m.group(2)]
            else:
                day_num = month_num = None
        else:
            month_num = MONTHS[m.group(1)]
            day_num = int(m.group(2))

        if month_num and day_num:
            year = now.year
            try:
                candidate = datetime(year, month_num, day_num)
                if candidate < now:
                    candidate = datetime(year + 1, month_num, day_num)
                return candidate.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Numeric date: MM/DD or DD/MM (assume MM/DD for ambiguous cases)
        m = re.search(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', tl)
        if m:
            try:
                month_n, day_n = int(m.group(1)), int(m.group(2))
                year_n = int(m.group(3)) if m.group(3) else now.year
                if year_n < 100:
                    year_n += 2000
                candidate = datetime(year_n, month_n, day_n)
                if candidate < now and not m.group(3):
                    candidate = datetime(year_n + 1, month_n, day_n)
                return candidate.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return None

    @staticmethod
    def extract_time(text: str):
        tl = text.lower()

        # Priority 1: Range start time "from 5 to 5:30 PM"
        range_match = re.search(r'from\s+(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?', tl)
        if range_match:
            hour = int(range_match.group(1))
            minute = int(range_match.group(2) or 0)
            meridiem = range_match.group(3)
            
            if meridiem:
                if meridiem == 'pm' and hour != 12:
                    hour += 12
                elif meridiem == 'am' and hour == 12:
                    hour = 0
            
            return f"{hour:02d}:{minute:02d}"

        # Priority 2: Regular time "at 5 PM", "5:30 PM"
        m = re.search(r'(\d{1,2})(?:[:.] ?(\d{2}))?\s*(am|pm)', tl)
        if m:
            h = int(m.group(1))
            min_val = int(m.group(2) or 0)
            meridiem = m.group(3)
            
            if meridiem == 'pm' and h != 12:
                h += 12
            elif meridiem == 'am' and h == 12:
                h = 0
            
            return f"{h:02d}:{min_val:02d}"

        return None

    @staticmethod
    def extract_duration(text: str):
        tl = text.lower()

        # Priority 1: Explicit hours "3 hours", "2 hrs"
        m = re.search(r'(\d+)\s*(?:hours?|hrs?)', tl)
        if m:
            return int(m.group(1)) * 60

        # Priority 2: Explicit minutes "30 min", "45 minutes"
        m = re.search(r'(\d+)\s*(?:minutes?|mins?)', tl)
        if m:
            return int(m.group(1))

        # Priority 3: "of X min/hour" pattern
        m = re.search(r'of\s+(\d+)\s*(?:hours?|hrs?)', tl)
        if m:
            return int(m.group(1)) * 60
        
        m = re.search(r'of\s+(\d+)\s*(?:minutes?|mins?)', tl)
        if m:
            return int(m.group(1))

        # Priority 4: Time range "from 5 to 5:30", "5 to 5:30 PM"
        range_pattern = r'from\s+(\d{1,2})(?::(\d{2}))?\s*(?:am|pm)?\s+to\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
        m = re.search(range_pattern, tl)
        if m:
            start_h = int(m.group(1))
            start_m = int(m.group(2) or 0)
            end_h = int(m.group(3))
            end_m = int(m.group(4) or 0)
            meridiem = m.group(5)
            
            # Handle PM times
            if meridiem == 'pm':
                if end_h != 12:
                    end_h += 12
                # If start hour is less and in same period, also PM
                if start_h < 12 and start_h < (end_h - 12):
                    start_h += 12
            
            duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
            if duration > 0:
                print(f"⏱️  Calculated duration from range: {duration}min")
                return duration

        # Default
        return 60