from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

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
        
        dl = date_str.lower()
        if dl == "today":
            dt = now
        elif dl == "tomorrow":
            dt = now + timedelta(days=1)
        else:
            try:
                dt = self.tz.localize(datetime.strptime(date_str, "%Y-%m-%d"))
            except:
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
        start = self.parse_dt(date, time)
        end = start + timedelta(minutes=duration)
        
        event = {
            'summary': title,
            'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'Asia/Kolkata'}
        }
        return self.service.events().insert(calendarId='primary', body=event).execute()
    
    def list_events(self, max_results: int = 10) -> list:
        now = datetime.utcnow().isoformat() + 'Z'
        result = self.service.events().list(
            calendarId='primary', timeMin=now, maxResults=max_results,
            singleEvents=True, orderBy='startTime'
        ).execute()
        return result.get('items', [])
    
    def find_event(self, title: str) -> dict:
        from difflib import SequenceMatcher
        events = self.list_events(50)
        
        best = None
        score = 0.3
        tl = title.lower()
        
        for e in events:
            et = e.get('summary', '').lower()
            s = SequenceMatcher(None, tl, et).ratio()
            if tl in et or et in tl:
                s += 0.4
            if s > score:
                score, best = s, e
        
        return best
    
    def update_event(self, event_id: str, new_date: str = None, new_time: str = None) -> dict:
        event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if new_date or new_time:
            curr = datetime.fromisoformat(event['start']['dateTime'])
            new_dt = self.parse_dt(
                new_date or curr.strftime("%Y-%m-%d"),
                new_time or curr.strftime("%H:%M")
            )
            
            dur = datetime.fromisoformat(event['end']['dateTime']) - curr
            event['start']['dateTime'] = new_dt.isoformat()
            event['end']['dateTime'] = (new_dt + dur).isoformat()
        
        return self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    
    def delete_event(self, event_id: str) -> bool:
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True