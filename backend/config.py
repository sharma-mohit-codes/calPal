from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    # Google OAuth
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/auth/callback")
    
    # Groq API (replacing Gemini)
    GROQ_API_KEY: str = Field(default="")
    
    # MongoDB
    MONGODB_URI: str = Field(default="mongodb://localhost:27017/")
    DATABASE_NAME: str = Field(default="calpal_db")
    
    # JWT
    JWT_SECRET_KEY: str = Field(default="change-this-secret-key-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_HOURS: int = Field(default=24)
    
    # App
    FRONTEND_URL: str = Field(default="http://localhost:5173")
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()