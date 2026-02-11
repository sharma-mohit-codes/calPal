from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage
from services.groq_service import groq_service
from services.calendar_service import CalendarService
from utils.nlp_extractor import NLPExtractor
from pymongo import MongoClient
from config import get_settings

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()

client = MongoClient(settings.MONGODB_URI)
db = client[settings.DATABASE_NAME]
users_collection = db['users']

@router.post("/message")
async def process_message(chat_msg: ChatMessage):
    try:
        
        user = users_collection.find_one({'email': chat_msg.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        print(f"\n{'='*60}")
        print(f"📨 USER: {chat_msg.message}")
        
        # Extract intent using Groq
        intent = await groq_service.extract_intent(chat_msg.message)
        action = intent.get("action")
        title = intent.get("title")
        
        print(f"🎯 Action: {action}, Title: {title}")
        
        # Extract date/time/duration
        extracted = NLPExtractor.extract_all(chat_msg.message)
        date = extracted["date"]
        time = extracted["time"]
        duration = extracted["duration"]
        
        print(f"📅 Date: {date}, Time: {time}, Duration: {duration}min")
        print(f"{'='*60}\n")

        cal = CalendarService(user['credentials'])

        if action == 'create':
            if not title:
                title = "Event"
            
            if not time:
                return {"success": True, "message": "⏰ What time should I schedule this?"}
            
            if not date:
                date = "today"
            
            cal.create_event(title, date, time, duration)
            msg = f"✅ Created '{title}' on {date} at {time}"
            if duration != 60:
                msg += f" ({duration} min)"
            return {"success": True, "message": msg}

        elif action == 'delete':
            if not title:
                return {"success": False, "message": "❌ Which event should I delete?"}
            
            date_filter = date if date and date != "today" else None
            ev = cal.find_event(title, date_filter)
            
            if not ev:
                if date_filter:
                    print("🔄 Trying without date filter...")
                    ev = cal.find_event(title, None)
                
                if not ev:
                    return {"success": False, "message": f"❌ Couldn't find '{title}'. Try: 'list my events' to see what's available."}
            
            cal.delete_event(ev['id'])
            return {"success": True, "message": f"🗑️ Deleted '{ev['summary']}'"}

        elif action == 'update':
            if not title:
                return {"success": False, "message": "❌ Which event should I update?"}
            
            date_filter = date if date and date != "today" else None
            ev = cal.find_event(title, date_filter)
            
            if not ev:
                if date_filter:
                    ev = cal.find_event(title, None)
                if not ev:
                    return {"success": False, "message": f"❌ Couldn't find '{title}'"}
            
            # Pass duration if it's not default (60)
            new_duration = duration if duration != 60 else None
            
            cal.update_event(
                ev['id'],
                date if date and date != "today" else None,
                time,
                new_duration
            )
            
            msg = f"✅ Updated '{ev['summary']}'"
            if time:
                msg += f" to {time}"
            if date and date != "today":
                msg += f" on {date}"
            if new_duration:
                hours = new_duration // 60
                mins = new_duration % 60
                if hours > 0 and mins > 0:
                    msg += f" (duration: {hours}h {mins}min)"
                elif hours > 0:
                    msg += f" (duration: {hours}h)"
                else:
                    msg += f" (duration: {mins}min)"
            
            return {"success": True, "message": msg}

        elif action == 'list':
            date_filter = date if date else None
            events = cal.list_events(10, date_filter)
            
            if not events:
                return {"success": True, "message": "📭 No upcoming events"}
            
            lines = [f"{i+1}. {e['summary']} - {cal.format_time(e)}" 
                    for i, e in enumerate(events)]
            msg = "📅 Upcoming events:\n\n" + "\n".join(lines)
            return {"success": True, "message": msg, "events": events}

        return {"success": False, "message": "🤔 Didn't understand that. Try: 'Add meeting tomorrow at 2pm'"}

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "😔 Something went wrong. Please try again."}