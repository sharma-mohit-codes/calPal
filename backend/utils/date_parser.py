from datetime import datetime, timedelta
import re

class DateParser:
    """
    Advanced date parsing utility
    """
    
    @staticmethod
    def parse_relative_date(date_str: str) -> datetime:
        """
        Parse relative dates like 'today', 'tomorrow', 'next monday', etc.
        """
        date_str = date_str.lower().strip()
        today = datetime.now()
        
        # Handle today/tomorrow
        if date_str == "today":
            return today
        elif date_str == "tomorrow":
            return today + timedelta(days=1)
        elif date_str == "day after tomorrow":
            return today + timedelta(days=2)
        elif date_str == "yesterday":
            return today - timedelta(days=1)
        
        # Handle "next week"
        if "next week" in date_str:
            return today + timedelta(weeks=1)
        
        # Handle "next [weekday]"
        weekdays = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        for day_name, day_num in weekdays.items():
            if day_name in date_str:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
        
        # Handle "in X days"
        match = re.search(r'in (\d+) days?', date_str)
        if match:
            days = int(match.group(1))
            return today + timedelta(days=days)
        
        # Handle "X days from now"
        match = re.search(r'(\d+) days? from now', date_str)
        if match:
            days = int(match.group(1))
            return today + timedelta(days=days)
        
        # Default to today if can't parse
        return today
    
    @staticmethod
    def parse_time(time_str: str) -> str:
        """
        Parse various time formats to HH:MM (24-hour)
        """
        time_str = time_str.lower().strip()
        
        # Handle 12-hour format with am/pm
        match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            meridiem = match.group(3)
            
            if meridiem == 'pm' and hour != 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        
        # Handle 24-hour format
        match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            return f"{hour:02d}:{minute:02d}"
        
        # Handle just hour (assume :00)
        match = re.search(r'(\d{1,2})', time_str)
        if match:
            hour = int(match.group(1))
            # If hour > 12, assume 24-hour format, else assume PM for common times
            if hour > 12:
                return f"{hour:02d}:00"
            else:
                # Default afternoon times (9-5 workday)
                return f"{hour:02d}:00"
        
        # Default to 9 AM
        return "09:00"
    
    @staticmethod
    def extract_duration(text: str) -> int:
        """
        Extract duration from text in minutes
        """
        # Check for explicit duration mentions
        patterns = [
            (r'(\d+)\s*hours?', 60),
            (r'(\d+)\s*hrs?', 60),
            (r'(\d+)\s*h', 60),
            (r'(\d+)\s*minutes?', 1),
            (r'(\d+)\s*mins?', 1),
            (r'(\d+)\s*m(?!o)', 1),  # m but not 'mo' (month)
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1)) * multiplier
        
        # Default 1 hour
        return 60