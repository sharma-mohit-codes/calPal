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
        """Extract action, title, date, time, duration AND time_range using Groq"""
        
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
- action: one of "create", "update", "delete", "delete_all", "list"
- title: the event name only (no time/date/duration/action words). null if none.
- date: event date in YYYY-MM-DD format. Resolve relative expressions using the reference dates above. null if no date mentioned.
- time: event start time in HH:MM 24-hour format. null if no time mentioned.
- duration: event duration in minutes as an integer. null if no duration mentioned.
- time_range: one of "this_week", "this_month", "next_week", "next_month", "next_X_days" (e.g. "next_7_days"), or null

RULES:
- action "create": triggered by add, schedule, book, create, set up, remind
- action "update": triggered by move, change, reschedule, update, shift
- action "delete": triggered by delete, remove, cancel (single event)
- action "delete_all": triggered by "delete all", "remove all", "cancel all", "clear all"
- action "list": triggered by list, show, display, what, view
- title: remove time, date, action words. Keep only the event name. null for list/delete_all.
- Resolve "next monday", "this friday", "next week", "in 3 days", "April 30" etc. using the reference dates.
- time_range: detect phrases like "this week", "this month", "next 10 days"

TIME RANGE DETECTION:
- "this week" -> "this_week"
- "this month" -> "this_month"
- "next week" -> "next_week"
- "next month" -> "next_month"
- "next 7 days", "next 10 days" -> "next_7_days", "next_10_days"

Examples:
"list my events this week" -> {{"action":"list","title":null,"date":null,"time":null,"duration":null,"time_range":"this_week"}}
"show schedules next 10 days" -> {{"action":"list","title":null,"date":null,"time":null,"duration":null,"time_range":"next_10_days"}}
"delete all events this month" -> {{"action":"delete_all","title":null,"date":null,"time":null,"duration":null,"time_range":"this_month"}}
"delete all events" -> {{"action":"delete_all","title":null,"date":null,"time":null,"duration":null,"time_range":null}}
"add meeting tomorrow at 10am" -> {{"action":"create","title":"meeting","date":"{tomorrow_str}","time":"10:00","duration":null,"time_range":null}}
"delete pwc" -> {{"action":"delete","title":"pwc","date":null,"time":null,"duration":null,"time_range":null}}

Respond ONLY with valid JSON, no explanation."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a JSON-only calendar parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
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
            
            # Normalize null-like values
            for field in ('date', 'time', 'duration', 'time_range', 'title'):
                if parsed.get(field) in ('null', '', 'none', 'None', 'N/A'):
                    parsed[field] = None

            print(f"✅ Parsed: {parsed}")
            return parsed
            
        except Exception as e:
            print(f"❌ Groq error: {e}")
            return self._fallback(user_message)
    
    def _fallback(self, msg: str) -> dict:
        """Fallback parser with time range detection"""
        ml = msg.lower()
        
        # Detect delete all
        if any(phrase in ml for phrase in ['delete all', 'remove all', 'cancel all', 'clear all']):
            action = "delete_all"
            title = None
        elif any(w in ml for w in ['delete', 'remove', 'cancel']):
            action = "delete"
            title = self._extract_title(msg)
        elif any(w in ml for w in ['update', 'move', 'change', 'reschedule']):
            action = "update"
            title = self._extract_title(msg)
        elif any(w in ml for w in ['list', 'show', 'events', 'calendar', 'schedules']):
            action = "list"
            title = None
        else:
            action = "create"
            title = self._extract_title(msg)
        
        extracted = NLPExtractor.extract_all(msg)
        time_range = self._extract_time_range(ml)
        
        return {
            "action": action,
            "title": title,
            "date": extracted.get("date"),
            "time": extracted.get("time"),
            "duration": extracted.get("duration"),
            "time_range": time_range
        }
    
    def _extract_time_range(self, text: str) -> str:
        """Extract time range from text"""
        if "this week" in text:
            return "this_week"
        elif "this month" in text:
            return "this_month"
        elif "next week" in text:
            return "next_week"
        elif "next month" in text:
            return "next_month"
        
        # Check for "next X days"
        match = re.search(r'next\s+(\d+)\s+days?', text)
        if match:
            return f"next_{match.group(1)}_days"
        
        return None
    
    def _extract_title(self, msg: str) -> str:
        """Extract title from message"""
        quote = re.search(r'["\']([^"\']+)["\']', msg)
        if quote:
            return quote.group(1).strip()
        
        named = re.search(r'(?:named|called)\s+([a-zA-Z0-9\s]+?)(?:\s+(?:at|on|from|to|tomorrow|today|for))', msg, re.I)
        if named:
            return named.group(1).strip()
        
        clean = msg
        noise = r'\b(add|create|schedule|book|delete|remove|cancel|update|move|change|a|an|the|meeting|event|appointment|named|called)\b'
        clean = re.sub(noise, '', clean, flags=re.I)
        clean = re.sub(r'\b(at|on|from|to|tomorrow|today|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday|am|pm|\d+)\b.*$', '', clean, flags=re.I)
        clean = re.sub(r'\s+', ' ', clean).strip('"\'')
        return clean if clean else "Event"

groq_service = GroqService()