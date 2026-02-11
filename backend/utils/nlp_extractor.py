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
        if "tomorrow" in tl:
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if "today" in tl:
            return datetime.now().strftime("%Y-%m-%d")
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