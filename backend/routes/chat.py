from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage
from services.gemini_service import gemini_service
from services.calendar_service import CalendarService
from pymongo import MongoClient
from config import get_settings

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()

client = MongoClient(settings.MONGODB_URI)
db = client[settings.DATABASE_NAME]
users_collection = db['users']

@router.post("/message")
async def process_message(chat_msg: ChatMessage):
    """
    Process user message and execute calendar action
    """
    try:
        # Get user credentials
        user = users_collection.find_one({'email': chat_msg.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Parse command using Gemini
        command = await gemini_service.parse_calendar_command(chat_msg.message)
        
        if command.get('action') == 'error':
            return {
                'success': False,
                'message': command.get('message', 'Could not understand command')
            }
        
        # Initialize calendar service
        cal_service = CalendarService(user['credentials'])
        
        # Execute action
        action = command['action']
        
        if action == 'create':
            event = cal_service.create_event(
                title=command.get('title', 'Untitled Event'),
                date=command.get('date', 'today'),
                time=command.get('time', '09:00'),
                duration_minutes=command.get('duration_minutes', 60)
            )
            return {
                'success': True,
                'message': f"✅ Created event: {command['title']}",
                'event': event
            }
        
        elif action == 'list':
            events = cal_service.list_events()
            return {
                'success': True,
                'message': f"📅 Found {len(events)} upcoming events",
                'events': events
            }
        
        elif action == 'update':
            # Find event by title
            event = cal_service.find_event_by_title(command.get('title', ''))
            if not event:
                return {
                    'success': False,
                    'message': f"❌ Could not find event: {command.get('title')}"
                }
            
            updated = cal_service.update_event(
                event_id=event['id'],
                new_date=command.get('new_date'),
                new_time=command.get('new_time')
            )
            return {
                'success': True,
                'message': f"✅ Updated event: {event['summary']}",
                'event': updated
            }
        
        elif action == 'delete':
            event = cal_service.find_event_by_title(command.get('title', ''))
            if not event:
                return {
                    'success': False,
                    'message': f"❌ Could not find event: {command.get('title')}"
                }
            
            cal_service.delete_event(event['id'])
            return {
                'success': True,
                'message': f"🗑️ Deleted event: {event['summary']}"
            }
        
        else:
            return {
                'success': False,
                'message': "Unknown action"
            }
            
    except Exception as e:
        print(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))