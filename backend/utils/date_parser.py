from datetime import datetime, timedelta
import re

class DateParser:
    """Advanced date/time parser"""
    
    @staticmethod
    def parse_relative(date_str: str) -> datetime:
        """Parse relative dates like 'today', 'tomorrow', 'next monday'"""
        ds = date_str.lower().strip()
        now = datetime.now()
        
        if ds == "today": return now
        if ds == "tomorrow": return now + timedelta(days=1)
        if ds == "yesterday": return now - timedelta(days=1)
        if "next week" in ds: return now + timedelta(weeks=1)
        
        # Weekdays
        weekdays = {'monday':0, 'tuesday':1, 'wednesday':2, 'thursday':3, 
                   'friday':4, 'saturday':5, 'sunday':6}
        
        for day, num in weekdays.items():
            if day in ds:
                days_ahead = num - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return now + timedelta(days=days_ahead)
        
        # "in X days"
        m = re.search(r'in (\d+) days?', ds)
        if m:
            return now + timedelta(days=int(m.group(1)))
        
        return now
    
    @staticmethod
    def parse_time(time_str: str) -> str:
        """Parse time to HH:MM format"""
        ts = time_str.lower().strip()
        
        # 12-hour with am/pm
        m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', ts)
        if m:
            h = int(m.group(1))
            min = int(m.group(2)) if m.group(2) else 0
            ap = m.group(3)
            
            if ap == 'pm' and h != 12: h += 12
            if ap == 'am' and h == 12: h = 0
            return f"{h:02d}:{min:02d}"
        
        # 24-hour
        m = re.search(r'(\d{1,2}):(\d{2})', ts)
        if m:
            return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
        
        # Just hour
        m = re.search(r'(\d{1,2})', ts)
        if m:
            return f"{int(m.group(1)):02d}:00"
        
        return "09:00"
    
    @staticmethod
    def extract_duration(text: str) -> int:
        """Extract duration in minutes"""
        patterns = [
            (r'(\d+)\s*hours?', 60),
            (r'(\d+)\s*hrs?', 60),
            (r'(\d+)\s*minutes?', 1),
            (r'(\d+)\s*mins?', 1)
        ]
        
        for pattern, mult in patterns:
            m = re.search(pattern, text.lower())
            if m:
                return int(m.group(1)) * mult
        
        return 60