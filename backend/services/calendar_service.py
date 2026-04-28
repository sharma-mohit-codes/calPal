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
    
    def parse_dt(self, date_str: str, time_str: str = None) -> datetime:
        """Parse date/time to datetime object"""
        now = datetime.now(self.tz)
        
        if not date_str:
            return now
        
        # Handle YYYY-MM-DD format
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
    
    def list_events(self, max_results: int = 10, date_filter: str = None, include_past: bool = False) -> list:
        """
        List events, optionally filtered by date
        
        Args:
            max_results: Maximum number of events to return
            date_filter: Filter by specific date (today/tomorrow/YYYY-MM-DD)
            include_past: If True, include past events from today
        """
        
        # Determine time range
        if include_past:
            # Start from beginning of today
            time_min = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        else:
            # Start from now (future events only)
            time_min = datetime.utcnow().isoformat() + 'Z'
        
        # If date filter provided, set specific day range
        if date_filter:
            try:
                if date_filter == "today":
                    filter_date = datetime.now()
                elif date_filter == "tomorrow":
                    filter_date = datetime.now() + timedelta(days=1)
                else:
                    filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
                
                # Start of day
                start_of_day = filter_date.replace(hour=0, minute=0, second=0, microsecond=0)
                # End of day
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
                # Fallback
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
        """
        Find event by title with improved matching
        
        Searches ALL events from today (including past) to avoid missing events
        """
        # Search from start of today to include past events
        events = self.list_events(100, date_filter, include_past=True)
        
        if not events:
            print(f"🔍 No events found")
            return None
        
        print(f"🔍 Searching '{title}' among {len(events)} events:")
        for e in events[:10]:  # Show first 10 for debug
            print(f"   - {e.get('summary', 'Untitled')}")
        if len(events) > 10:
            print(f"   ... and {len(events) - 10} more")
        
        best = None
        best_score = 0
        tl = title.lower().strip()
        
        for e in events:
            et = e.get('summary', '').lower().strip()
            
            # Exact match (case insensitive)
            if tl == et:
                print(f"✅ Exact match: '{et}'")
                return e
            
            # Substring match (either direction)
            if tl in et or et in tl:
                print(f"✅ Substring match: '{et}'")
                return e
            
            # Fuzzy similarity
            score = SequenceMatcher(None, tl, et).ratio()
            
            # Bonus for partial word match
            title_words = set(tl.split())
            event_words = set(et.split())
            common_words = title_words & event_words
            if common_words:
                score += 0.3
            
            if score > best_score:
                best_score = score
                best = e
        
        # Lower threshold for short titles
        threshold = 0.3 if len(tl) <= 5 else 0.4
        
        if best_score >= threshold:
            print(f"✅ Found match: '{best.get('summary')}' (score: {best_score:.2f})")
            return best
        
        print(f"❌ No match found (best score: {best_score:.2f}, threshold: {threshold})")
        return None
    
    def update_event(self, event_id: str, new_date: str = None, new_time: str = None, new_duration: int = None) -> dict:
        """Update event with support for date, time, and duration changes"""
        event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Get current start and end times
        curr_start = datetime.fromisoformat(event['start']['dateTime'])
        curr_end = datetime.fromisoformat(event['end']['dateTime'])
        current_duration = (curr_end - curr_start).total_seconds() / 60  # in minutes
        
        print(f"📝 Current: {curr_start} → {curr_end} ({current_duration:.0f}min)")
        
        # Calculate new start time
        if new_date or new_time:
            new_start = self.parse_dt(
                new_date or curr_start.strftime("%Y-%m-%d"),
                new_time or curr_start.strftime("%H:%M")
            )
        else:
            new_start = curr_start
        
        # Calculate new end time
        if new_duration:
            # User specified new duration
            new_end = new_start + timedelta(minutes=new_duration)
            print(f"✏️  Updated duration: {new_duration}min")
        else:
            # Keep existing duration
            duration_to_use = current_duration
            new_end = new_start + timedelta(minutes=duration_to_use)
        
        # Update event
        event['start']['dateTime'] = new_start.isoformat()
        event['end']['dateTime'] = new_end.isoformat()
        
        print(f"📅 New: {new_start} → {new_end}")
        
        return self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    
    def delete_event(self, event_id: str) -> bool:
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True