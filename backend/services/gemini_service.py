import google.generativeai as genai
from config import get_settings
import json

settings = get_settings()
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def parse_calendar_command(self, user_message: str) -> dict:
        """
        Convert natural language to structured calendar command
        """
        prompt = f"""
You are a calendar command parser. Convert the user's message into a structured JSON command.

Rules:
- action: can be "create", "update", "delete", or "list"
- For times, use 24-hour format (HH:MM)
- For dates, use YYYY-MM-DD format or relative terms like "today", "tomorrow"
- Extract title from the user's description
- Default duration is 60 minutes

User message: "{user_message}"

Respond ONLY with valid JSON in this exact format:
{{
  "action": "create|update|delete|list",
  "title": "event title",
  "date": "YYYY-MM-DD or today/tomorrow",
  "time": "HH:MM",
  "new_time": "HH:MM (only for updates)",
  "new_date": "YYYY-MM-DD (only for updates)",
  "duration_minutes": 60
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            parsed = json.loads(text)
            return parsed
        except Exception as e:
            print(f"Gemini parsing error: {e}")
            return {
                "action": "error",
                "message": "Could not understand the command"
            }

gemini_service = GeminiService()