from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage
from services.gemini_service import gemini_service
from services.calendar_service import CalendarService
from pymongo import MongoClient
from config import get_settings
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()

client = MongoClient(settings.MONGODB_URI)
db = client[settings.DATABASE_NAME]
users_collection = db['users']
convs = db['conversations']

@router.post("/message")
async def process_message(chat_msg: ChatMessage):
    try:
        user = users_collection.find_one({'email': chat_msg.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get conversation context
        conv = convs.find_one({'user_email': chat_msg.user_id})
        context = conv.get('messages', []) if conv else []
        
        print(f"\n{'='*60}")
        print(f"📨 USER: {chat_msg.message}")
        print(f"{'='*60}")
        
        # Parse with AI
        parsed = await gemini_service.parse_calendar_command(chat_msg.message, context)
        
        # Need clarification?
        if parsed.get('status') == 'needs_clarification':
            convs.update_one(
                {'user_email': chat_msg.user_id},
                {'$set': {'pending': parsed.get('partial_data', {})},
                 '$push': {'messages': {'$each': [
                     {'text': chat_msg.message, 'isUser': True, 'ts': datetime.utcnow()},
                     {'text': parsed['response'], 'isUser': False, 'ts': datetime.utcnow()}
                 ], '$slice': -20}}},
                upsert=True
            )
            return {'success': True, 'message': parsed['response']}
        
        # Execute action
        cal = CalendarService(user['credentials'])
        action = parsed.get('action')
        
        try:
            if action == 'create':
                print(f"📅 Creating: {parsed.get('title')} | {parsed.get('date')} | {parsed.get('time')} | {parsed.get('duration_minutes')}min")
                
                cal.create_event(
                    parsed.get('title', 'Event'),
                    parsed.get('date', 'today'),
                    parsed.get('time', '09:00'),
                    parsed.get('duration_minutes', 60)
                )
                msg = parsed.get('response', '✅ Event created!')
                
            elif action == 'list':
                events = cal.list_events(10)
                if not events:
                    msg = "📭 No upcoming events"
                else:
                    event_lines = [f"{i+1}. {e['summary']} - {cal.format_time(e)}" 
                                  for i, e in enumerate(events)]
                    msg = "📅 Upcoming events:\n\n" + "\n".join(event_lines)
                
            elif action == 'update':
                print(f"🔄 Updating: {parsed.get('title')}")
                ev = cal.find_event(parsed.get('title', ''))
                if not ev:
                    msg = f"❌ Couldn't find '{parsed.get('title')}'. Try listing your events first."
                else:
                    cal.update_event(ev['id'], parsed.get('new_date'), parsed.get('new_time'))
                    msg = parsed.get('response', f"✅ Updated '{ev['summary']}'")
                
            elif action == 'delete':
                print(f"🗑️ Deleting: {parsed.get('title')}")
                ev = cal.find_event(parsed.get('title', ''))
                if not ev:
                    msg = f"❌ Couldn't find '{parsed.get('title')}'"
                else:
                    cal.delete_event(ev['id'])
                    msg = parsed.get('response', f"🗑️ Deleted '{ev['summary']}'")
            else:
                msg = "🤔 Try: 'Add meeting tomorrow at 2pm' or 'List my events'"
            
            # Save conversation
            convs.update_one(
                {'user_email': chat_msg.user_id},
                {'$unset': {'pending': ''},
                 '$push': {'messages': {'$each': [
                     {'text': chat_msg.message, 'isUser': True, 'ts': datetime.utcnow()},
                     {'text': msg, 'isUser': False, 'ts': datetime.utcnow()}
                 ], '$slice': -20}}},
                upsert=True
            )
            
            print(f"✅ RESPONSE: {msg}\n")
            return {'success': True, 'message': msg}
            
        except Exception as ce:
            print(f"❌ Calendar error: {ce}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': "😔 Had trouble with your calendar. Please try again."}
        
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': "😔 Something went wrong. Could you rephrase that?"}