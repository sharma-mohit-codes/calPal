from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from services.auth_service import AuthService
from config import get_settings
from pymongo import MongoClient
from datetime import datetime
import httpx

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()

# MongoDB connection
client = MongoClient(settings.MONGODB_URI)
db = client[settings.DATABASE_NAME]
users_collection = db['users']

@router.get("/login")
async def login():
    """
    Initiate Google OAuth login
    """
    auth_url, state = AuthService.get_authorization_url()
    return {"auth_url": auth_url, "state": state}

@router.get("/callback")
async def callback(code: str):
    """
    Handle OAuth callback
    """
    try:
        # Exchange code for tokens
        credentials = AuthService.exchange_code_for_token(code)
        
        # Get user info from Google
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {credentials["token"]}'}
            )
            user_info = response.json()
        
        # Store/update user in database
        user_data = {
            'email': user_info['email'],
            'name': user_info.get('name', ''),
            'google_id': user_info['id'],
            'credentials': credentials,
            'updated_at': datetime.utcnow()
        }
        
        users_collection.update_one(
            {'google_id': user_info['id']},
            {'$set': user_data, '$setOnInsert': {'created_at': datetime.utcnow()}},
            upsert=True
        )
        
        # Redirect to frontend with user info
        redirect_url = f"{settings.FRONTEND_URL}?login=success&email={user_info['email']}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        print(f"Auth error: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?login=error")

@router.get("/user/{email}")
async def get_user(email: str):
    """
    Get user by email
    """
    user = users_collection.find_one({'email': email}, {'_id': 0, 'credentials': 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user