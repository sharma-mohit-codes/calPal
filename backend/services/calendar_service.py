from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

class CalendarService:
    def __init__(self, credentials_dict: dict):
        """
        Initialize with user's OAuth credentials
        """
        creds = Credentials(
            token=credentials_dict.get('token'),
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict.get('token_uri'),
            client_id=credentials_dict.get('client_id'),
            client_secret=credentials_dict.get('client_secret'),
            scopes=credentials_dict.get('scopes')
        )
        self.service = build('calendar', 'v3', credentials=creds)
    
    def parse_datetime(self, date_str: str, time_str: str = None) -> datetime:
        """
        Convert date/time strings to datetime object
        """
        today = datetime.now()
        
        # Handle relative dates
        if date_str.lower() == "today":
            date_obj = today
        elif date_str.lower() == "tomorrow":
            date_obj = today + timedelta(days=1)
        else:
            # Parse YYYY-MM-DD format
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Add time if provided
        if time_str:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            date_obj = datetime.combine(date_obj.date(), time_obj)
        
        return date_obj
    
    def create_event(self, title: str, date: str, time: str, duration_minutes: int = 60) -> dict:
        """
        Create a new calendar event
        """
        start_time = self.parse_datetime(date, time)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
        }
        
        created_event = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return created_event
    
    def list_events(self, max_results: int = 10) -> list:
        """
        List upcoming events
        """
        now = datetime.utcnow().isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    
    def find_event_by_title(self, title: str) -> dict:
        """
        Find event by title (fuzzy match)
        """
        events = self.list_events(max_results=50)
        
        # Simple fuzzy matching
        title_lower = title.lower()
        for event in events:
            event_title = event.get('summary', '').lower()
            if title_lower in event_title or event_title in title_lower:
                return event
        
        return None
    
    def update_event(self, event_id: str, new_date: str = None, new_time: str = None) -> dict:
        """
        Update an existing event
        """
        event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if new_date or new_time:
            current_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            
            if new_date:
                new_dt = self.parse_datetime(new_date, new_time or current_start.strftime("%H:%M"))
            else:
                new_dt = self.parse_datetime(current_start.strftime("%Y-%m-%d"), new_time)
            
            duration = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')) - current_start
            end_dt = new_dt + duration
            
            event['start']['dateTime'] = new_dt.isoformat()
            event['end']['dateTime'] = end_dt.isoformat()
        
        updated_event = self.service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()
        
        return updated_event
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event
        """
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True