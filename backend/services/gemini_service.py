import google.generativeai as genai
from config import get_settings
import json
import re

settings = get_settings()
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def parse_calendar_command(self, user_message: str, context: list = None) -> dict:
        """Intelligent command parser using Gemini's understanding"""
        
        context_str = ""
        if context:
            context_msgs = [f"{'User' if m.get('isUser') else 'Bot'}: {m.get('text')}" 
                           for m in context[-3:]]
            context_str = "\n".join(context_msgs)
        
        prompt = f"""You are an intelligent calendar assistant. Your job is to understand what the user WANTS, not just extract keywords.

{"CONVERSATION HISTORY:" + chr(10) + context_str + chr(10) if context_str else ""}
USER REQUEST: "{user_message}"

YOUR TASK:
Understand the user's TRUE INTENT and extract the MEANINGFUL information.

ACTIONS YOU CAN PERFORM:
1. CREATE event - user wants to add/schedule something new
2. UPDATE event - user wants to change an existing event's time/date  
3. DELETE event - user wants to remove/cancel an event
4. LIST events - user wants to see their calendar

WHAT TO EXTRACT:
- Event title = the ACTUAL NAME of the event (not the surrounding fluff words)
- Date = when it happens (today, tomorrow, specific date)
- Time = what time (in 24-hour HH:MM format)
- Duration = how long (in minutes, default 60)

INTELLIGENCE RULES:
- Ignore filler words like "add a meeting named", "schedule an event called", "create a"
- Extract ONLY the core event name: "PwC", "team standup", "dentist appointment"
- For dates: understand "today", "tomorrow", "next monday", "15th March"
- For times: understand ALL formats - "11am", "11 AM", "1100", "11:00", "eleven in the morning"
- For duration: look for "30 minutes", "1 hour", "2 hrs" etc.
- For DELETE/UPDATE: you only need the event title to find, not date/time

THINK STEP BY STEP:
1. What does the user want to DO? (create/update/delete/list)
2. What is the CORE event name? (strip all fluff)
3. When is it? (extract date)
4. What time? (extract and convert to HH:MM)
5. How long? (extract duration or default 60)

RESPONSE FORMAT (JSON only, no markdown):

For CREATE:
{{
  "status": "ready",
  "action": "create",
  "title": "core event name only",
  "date": "today|tomorrow|YYYY-MM-DD",
  "time": "HH:MM",
  "duration_minutes": 30,
  "response": "friendly confirmation message"
}}

For UPDATE:
{{
  "status": "ready",
  "action": "update",
  "title": "event to find",
  "new_time": "HH:MM",
  "response": "confirmation"
}}

For DELETE:
{{
  "status": "ready",
  "action": "delete",
  "title": "event to find",
  "response": "confirmation"
}}

For LIST:
{{
  "status": "ready",
  "action": "list",
  "response": "confirmation"
}}

For INCOMPLETE (missing critical info):
{{
  "status": "needs_clarification",
  "missing": ["what's missing"],
  "response": "friendly question",
  "partial_data": {{"title": "if you extracted anything"}}
}}

EXAMPLES OF SMART EXTRACTION:

User: "add a meeting named PwC at 11 am today of 30 minutes"
THINK: Action=create, Title=PwC (not the whole sentence!), Date=today, Time=11:00, Duration=30
{{
  "status": "ready",
  "action": "create",
  "title": "PwC",
  "date": "today",
  "time": "11:00",
  "duration_minutes": 30,
  "response": "Scheduled PwC for today at 11 AM (30 minutes)"
}}

User: "schedule team standup tomorrow morning 9 30"
THINK: Action=create, Title=team standup, Date=tomorrow, Time=09:30
{{
  "status": "ready",
  "action": "create",
  "title": "team standup",
  "date": "tomorrow",
  "time": "09:30",
  "duration_minutes": 60,
  "response": "Scheduled team standup for tomorrow at 9:30 AM"
}}

User: "create an event called dentist appointment on friday at 2pm for 45 minutes"
THINK: Title=dentist appointment (core name), Time=14:00, Duration=45
{{
  "status": "ready",
  "action": "create",
  "title": "dentist appointment",
  "date": "friday",
  "time": "14:00",
  "duration_minutes": 45,
  "response": "Scheduled dentist appointment for Friday at 2 PM (45 minutes)"
}}

User: "delete pwc meeting"
THINK: Action=delete, Title=pwc meeting (or just "pwc")
{{
  "status": "ready",
  "action": "delete",
  "title": "pwc",
  "response": "Deleting PwC meeting"
}}

User: "move gym to 7pm"
THINK: Action=update, Title=gym, NewTime=19:00
{{
  "status": "ready",
  "action": "update",
  "title": "gym",
  "new_time": "19:00",
  "response": "Moving gym to 7 PM"
}}

User: "schedule coffee meeting"
THINK: Missing date and time - ask for it
{{
  "status": "needs_clarification",
  "missing": ["date", "time"],
  "response": "When should I schedule the coffee meeting?",
  "partial_data": {{"title": "coffee meeting"}}
}}

NOW PARSE THE USER'S REQUEST ABOVE. Think carefully about the INTENT and extract MEANINGFUL data only.
Respond with JSON only:"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            print(f"🤖 Gemini raw: {text[:300]}...")
            
            # Extract JSON
            text = self._clean_json(text)
            
            parsed = json.loads(text)
            
            # Validate and normalize
            parsed = self._validate_response(parsed)
            
            print(f"✅ Parsed: {json.dumps(parsed, indent=2)}")
            return parsed
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Last resort fallback
            return {
                "status": "needs_clarification",
                "missing": ["details"],
                "response": "I didn't quite understand that. Could you rephrase? Try: 'Add meeting tomorrow at 2pm'"
            }
    
    def _clean_json(self, text: str) -> str:
        """Extract clean JSON from response"""
        # Remove markdown
        if "```" in text:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return match.group(1)
        
        # Find JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        
        return text
    
    def _validate_response(self, parsed: dict) -> dict:
        """Validate and normalize AI response"""
        # Ensure status exists
        if 'status' not in parsed:
            parsed['status'] = 'ready'
        
        # Normalize time format
        if 'time' in parsed and parsed['time']:
            parsed['time'] = self._normalize_time(parsed['time'])
        
        if 'new_time' in parsed and parsed['new_time']:
            parsed['new_time'] = self._normalize_time(parsed['new_time'])
        
        # Ensure duration
        if parsed.get('action') == 'create' and 'duration_minutes' not in parsed:
            parsed['duration_minutes'] = 60
        
        # Clean title
        if 'title' in parsed and parsed['title']:
            parsed['title'] = parsed['title'].strip()
        
        return parsed
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time to HH:MM"""
        if not time_str:
            return "09:00"
        
        # Already in HH:MM
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            parts = time_str.split(':')
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        
        return time_str

gemini_service = GeminiService()