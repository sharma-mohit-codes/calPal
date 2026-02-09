from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    google_id: str
    name: str

class User(BaseModel):
    id: str
    email: str
    name: str
    google_id: str
    created_at: datetime

class ChatMessage(BaseModel):
    message: str
    user_id: str

class CalendarAction(BaseModel):
    action: str  # create, update, delete, list
    title: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    new_time: Optional[str] = None
    new_date: Optional[str] = None
    duration_minutes: Optional[int] = 60

class EventResponse(BaseModel):
    id: str
    title: str
    start: str
    end: str
    description: Optional[str] = None