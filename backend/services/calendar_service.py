from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
from difflib import SequenceMatcher

class CalendarService:
    def __init__(self, creds_dict: dict):
        creds = Credentials(
            token=creds_dict.get('token'),
            refresh_token=creds_dict.get('refresh_token'),
            token_uri=creds_dict.get('token_uri'),
            client_id=creds_dict.get('client_id'),
            client_secret=creds_dict.get('client_secret'),
            scopes=creds_dict.get('scopes')
        )
        self.service = build('calendar', 'v3', credentials=creds)
        self.tz = pytz.timezone('Asia/Kolkata')
    
    def get_time_range_bounds(self, time_range: str) -> tuple:
        """
        Convert time_range string to (start_datetime, end_datetime)
        
        Returns tuple of (time_min, time_max) as ISO strings
        """
        now = datetime.now(self.tz)
        
        if time_range == "this_week":
            # Monday of this week to Sunday
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            
        elif time_range == "next_week":
            # Next Monday to next Sunday
            days_to_monday = 7 - now.weekday()
            start = now + timedelta(days=days_to_monday)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            
        elif time_range == "this_month":
            # First day of this month to last day
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
                
        elif time_range == "next_month":
            # First day of next month to last day of next month
            if now.month == 12:
                start = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end = start.replace(month=2)
            else:
                start = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 11:
                    end = start.replace(year=now.year + 1, month=1)
                else:
                    end = start.replace(month=now.month + 2)
                    
        elif time_range and time_range.startswith("next_") and time_range.endswith("_days"):
            # Extract number of days
            import re
            match = re.search(r'next_(\d+)_days', time_range)
            if match:
                days = int(match.group(1))
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=days)
            else:
                return None, None
        else:
            return None, None
        
        return start.isoformat(), end.isoformat()
    
    def parse_dt(self, date_str: str, time_str: str = None) -> datetime:
        """Parse date/time to datetime object"""
        now = datetime.now(self.tz)
        
        if not date_str:
            return now
        
        if isinstance(date_str, str) and len(date_str) == 10 and '-' in date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dt = self.tz.localize(dt)
            except:
                dt = now
        elif date_str == "today":
            dt = now
        elif date_str == "tomorrow":
            dt = now + timedelta(days=1)
        else:
            dt = now
        
        if time_str:
            try:
                t = datetime.strptime(time_str, "%H:%M").time()
                dt = self.tz.localize(datetime.combine(dt.date(), t))
            except:
                pass
        
        return dt
    
    def format_time(self, event: dict) -> str:
        """Format event time for display"""
        start = event['start'].get('dateTime', event['start'].get('date'))
        try:
            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if dt.date() == datetime.now().date():
                return f"Today {dt.strftime('%I:%M %p')}"
            elif dt.date() == (datetime.now() + timedelta(days=1)).date():
                return f"Tomorrow {dt.strftime('%I:%M %p')}"
            return dt.strftime('%b %d, %I:%M %p')
        except:
            return start
    
    def create_event(self, title: str, date: str, time: str, duration: int = 60) -> dict:
        """Create event with duration support"""
        start = self.parse_dt(date, time)
        end = start + timedelta(minutes=duration)
        
        event = {
            'summary': title,
            'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'Asia/Kolkata'}
        }
        
        print(f"📅 Creating: {title} | {start} → {end} ({duration}min)")
        return self.service.events().insert(calendarId='primary', body=event).execute()
    
    def list_events(self, max_results: int = 10, date_filter: str = None, include_past: bool = False, time_range: str = None) -> list:
        """
        List events with optional time range filtering
        
        Args:
            max_results: Maximum number of events
            date_filter: Single date filter (legacy)
            include_past: Include past events from today
            time_range: Time range filter (this_week, this_month, etc.)
        """
        
        # If time_range specified, use it
        if time_range:
            time_min, time_max = self.get_time_range_bounds(time_range)
            if time_min and time_max:
                print(f"📅 Time range filter: {time_range} ({time_min} to {time_max})")
                result = self.service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                return result.get('items', [])
        
        # Legacy date filter logic
        if include_past:
            time_min = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        else:
            time_min = datetime.utcnow().isoformat() + 'Z'
        
        if date_filter:
            try:
                if date_filter == "today":
                    filter_date = datetime.now()
                elif date_filter == "tomorrow":
                    filter_date = datetime.now() + timedelta(days=1)
                else:
                    filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
                
                start_of_day = filter_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = filter_date.replace(hour=23, minute=59, second=59, microsecond=0)
                
                result = self.service.events().list(
                    calendarId='primary',
                    timeMin=start_of_day.isoformat() + 'Z',
                    timeMax=end_of_day.isoformat() + 'Z',
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
            except:
                result = self.service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
        else:
            result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        
        return result.get('items', [])
    
    def find_event(self, title: str, date_filter: str = None) -> dict:
        """Find event by title with improved matching"""
        events = self.list_events(100, date_filter, include_past=True)
        
        if not events:
            print(f"🔍 No events found")
            return None
        
        print(f"🔍 Searching '{title}' among {len(events)} events:")
        for e in events[:10]:
            print(f"   - {e.get('summary', 'Untitled')}")
        if len(events) > 10:
            print(f"   ... and {len(events) - 10} more")
        
        best = None
        best_score = 0
        tl = title.lower().strip()
        
        for e in events:
            et = e.get('summary', '').lower().strip()
            
            if tl == et:
                print(f"✅ Exact match: '{et}'")
                return e
            
            if tl in et or et in tl:
                print(f"✅ Substring match: '{et}'")
                return e
            
            score = SequenceMatcher(None, tl, et).ratio()
            
            title_words = set(tl.split())
            event_words = set(et.split())
            common_words = title_words & event_words
            if common_words:
                score += 0.3
            
            if score > best_score:
                best_score = score
                best = e
        
        threshold = 0.3 if len(tl) <= 5 else 0.4
        
        if best_score >= threshold:
            print(f"✅ Found match: '{best.get('summary')}' (score: {best_score:.2f})")
            return best
        
        print(f"❌ No match found (best score: {best_score:.2f})")
        return None
    
    def delete_all_events(self, time_range: str = None) -> int:
        """
        Delete all events, optionally filtered by time range
        
        Returns: Number of events deleted
        """
        if time_range:
            events = self.list_events(max_results=500, time_range=time_range)
            print(f"🗑️ Deleting all events in range: {time_range}")
        else:
            events = self.list_events(max_results=500)
            print(f"🗑️ Deleting all upcoming events")
        
        count = 0
        for event in events:
            try:
                self.service.events().delete(calendarId='primary', eventId=event['id']).execute()
                print(f"   ✓ Deleted: {event.get('summary', 'Untitled')}")
                count += 1
            except Exception as e:
                print(f"   ✗ Failed to delete: {event.get('summary', 'Untitled')} - {e}")
        
        return count
    
    def update_event(self, event_id: str, new_date: str = None, new_time: str = None, new_duration: int = None) -> dict:
        """Update event with support for date, time, and duration changes"""
        event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
        
        curr_start = datetime.fromisoformat(event['start']['dateTime'])
        curr_end = datetime.fromisoformat(event['end']['dateTime'])
        current_duration = (curr_end - curr_start).total_seconds() / 60
        
        print(f"📝 Current: {curr_start} → {curr_end} ({current_duration:.0f}min)")
        
        if new_date or new_time:
            new_start = self.parse_dt(
                new_date or curr_start.strftime("%Y-%m-%d"),
                new_time or curr_start.strftime("%H:%M")
            )
        else:
            new_start = curr_start
        
        if new_duration:
            new_end = new_start + timedelta(minutes=new_duration)
            print(f"✏️  Updated duration: {new_duration}min")
        else:
            duration_to_use = current_duration
            new_end = new_start + timedelta(minutes=duration_to_use)
        
        event['start']['dateTime'] = new_start.isoformat()
        event['end']['dateTime'] = new_end.isoformat()
        
        print(f"📅 New: {new_start} → {new_end}")
        
        return self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    
    def delete_event(self, event_id: str) -> bool:
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True