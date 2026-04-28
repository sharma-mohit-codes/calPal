from groq import Groq
import json
import re
from datetime import datetime, timedelta
from config import get_settings
from utils.nlp_extractor import NLPExtractor

settings = get_settings()

class GroqService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"
    
    async def extract_intent(self, user_message: str) -> dict:
        """Extract action, title, date, time and duration using Groq"""
        
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        today_day = now.strftime("%A")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        # Pre-compute next occurrences of each weekday
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        next_days = {}
        for i, name in enumerate(day_names):
            days_ahead = i - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_days[name] = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        next_week_dates = "\n".join(f"  next {name} = {date}" for name, date in next_days.items())

        prompt = f"""You are a calendar assistant. Today is {today_day}, {today_str}.

Reference dates:
  today = {today_str}
  tomorrow = {tomorrow_str}
{next_week_dates}

User message: "{user_message}"

Extract ALL of the following fields from the message:
- action: one of "create", "update", "delete", "list"
- title: the event name only (no time/date/duration/action words). null if none.
- date: event date in YYYY-MM-DD format. Resolve relative expressions using the reference dates above. null if no date mentioned.
- time: event start time in HH:MM 24-hour format. null if no time mentioned.
- duration: event duration in minutes as an integer. null if no duration mentioned.

RULES:
- action "create": triggered by add, schedule, book, create, set up, remind
- action "update": triggered by move, change, reschedule, update, shift
- action "delete": triggered by delete, remove, cancel
- action "list": triggered by list, show, display, what, view
- title: remove time, date, action words. Keep only the event name.
- Resolve "next monday", "this friday", "next week", "in 3 days", "April 30" etc. using the reference dates.
- For bare weekday names like "on friday", use the next upcoming occurrence from the reference dates.

Examples:
"add meeting named PWC tomorrow at 10am" -> {{"action":"create","title":"PWC","date":"{tomorrow_str}","time":"10:00","duration":null}}
"schedule team standup next monday at 9:30 AM" -> {{"action":"create","title":"team standup","date":"{next_days['Monday']}","time":"09:30","duration":null}}
"book dentist for 2 hours on friday at 3pm" -> {{"action":"create","title":"dentist","date":"{next_days['Friday']}","time":"15:00","duration":120}}
"delete pwc meeting" -> {{"action":"delete","title":"pwc","date":null,"time":null,"duration":null}}
"move gym to 7pm" -> {{"action":"update","title":"gym","date":null,"time":"19:00","duration":null}}
"list events" -> {{"action":"list","title":null,"date":null,"time":null,"duration":null}}

Respond ONLY with valid JSON, no explanation."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only calendar parser. Return only valid JSON, no explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            text = response.choices[0].message.content.strip()
            print(f"🤖 Groq response: {text}")
            
            # Clean and parse JSON
            text = re.sub(r'```(?:json)?|```', '', text).strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            parsed = json.loads(text)
            
            # Clean title
            if parsed.get('title'):
                parsed['title'] = parsed['title'].strip('"\'')
            
            # Normalize null-like values to Python None
            for field in ('date', 'time', 'duration'):
                if parsed.get(field) in ('null', '', 'none', 'None', 'N/A'):
                    parsed[field] = None

            print(f"✅ Parsed: {parsed}")
            return parsed
            
        except Exception as e:
            print(f"❌ Groq error: {e}")
            return self._fallback(user_message)
    
    def _fallback(self, msg: str) -> dict:
        """Simple fallback parser"""
        ml = msg.lower()
        
        if any(w in ml for w in ['delete', 'remove', 'cancel']):
            action = "delete"
        elif any(w in ml for w in ['update', 'move', 'change', 'reschedule']):
            action = "update"
        elif any(w in ml for w in ['list', 'show', 'events', 'calendar']):
            return {"action": "list", "title": None, "date": None, "time": None, "duration": None}
        else:
            action = "create"
        
        extracted = NLPExtractor.extract_all(msg)
        title = self._extract_title(msg)
        return {
            "action": action,
            "title": title,
            "date": extracted.get("date"),
            "time": extracted.get("time"),
            "duration": extracted.get("duration"),
        }
    
    def _extract_title(self, msg: str) -> str:
        """Extract title from message"""
        # Quoted text
        quote = re.search(r'["\']([^"\']+)["\']', msg)
        if quote:
            return quote.group(1).strip()
        
        # "named X" or "called X"
        named = re.search(r'(?:named|called)\s+([a-zA-Z0-9\s]+?)(?:\s+(?:at|on|from|to|tomorrow|today|for))', msg, re.I)
        if named:
            return named.group(1).strip()
        
        # Remove noise words
        clean = msg
        noise = r'\b(add|create|schedule|book|delete|remove|cancel|update|move|change|a|an|the|meeting|event|appointment|named|called)\b'
        clean = re.sub(noise, '', clean, flags=re.I)
        
        # Remove time/date
        clean = re.sub(r'\b(at|on|from|to|tomorrow|today|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday|am|pm|\d+)\b.*$', '', clean, flags=re.I)
        
        clean = re.sub(r'\s+', ' ', clean).strip('"\'')
        return clean if clean else "Event"

groq_service = GroqService()