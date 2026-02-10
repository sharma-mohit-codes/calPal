from groq import Groq
import json
import re
from config import get_settings

settings = get_settings()

class GroqService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        # Using llama3-70b - very fast and accurate
        self.model = "llama-3.1-8b-instant"
    
    async def extract_intent(self, user_message: str) -> dict:
        """Extract action and title using Groq"""
        
        prompt = f"""You are a calendar intent parser. Extract only ACTION and TITLE.

User message: "{user_message}"

ACTIONS:
- create: add, schedule, book, create, set up
- update: move, change, reschedule, update
- delete: delete, remove, cancel
- list: list, show, display

TITLE RULES:
1. Extract ONLY the event name
2. Text in quotes → use that
3. "named X" or "called X" → use X
4. Ignore: time, dates, action words
5. For delete/update: just the event name to search

Examples:
"add meeting named PWC tomorrow at 10am" → {{"action":"create","title":"PWC"}}
"schedule team standup at 9:30" → {{"action":"create","title":"team standup"}}
"delete pwc meeting" → {{"action":"delete","title":"pwc"}}
"move gym to 7pm" → {{"action":"update","title":"gym"}}
"list events" → {{"action":"list","title":null}}

Respond ONLY with JSON:
{{"action":"...","title":"..."}}"""

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
                max_tokens=100
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
            return {"action": "list", "title": None}
        else:
            action = "create"
        
        # Extract title
        title = self._extract_title(msg)
        return {"action": action, "title": title}
    
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