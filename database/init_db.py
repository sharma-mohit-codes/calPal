"""
Database initialization script
Run this once to set up MongoDB collections and indexes
"""

from pymongo import MongoClient, ASCENDING
from datetime import datetime
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def init_database():
    """
    Initialize MongoDB database with required collections and indexes
    """
    try:
        # Import settings
        from config import get_settings
        settings = get_settings()
        
        print(f"📍 Backend directory: {backend_dir}")
        print(f"🔑 MongoDB URI: {settings.MONGODB_URI[:20]}...")
        print(f"🗄️  Database name: {settings.DATABASE_NAME}")
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        print(f"\n💡 Make sure backend/.env file exists with all required values")
        sys.exit(1)
    
    try:
        # Connect to MongoDB
        print(f"\n🔌 Connecting to MongoDB...")
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.server_info()
        print(f"✅ Connected to MongoDB successfully")
        
        db = client[settings.DATABASE_NAME]
        
        # Create collections
        collections = ['users', 'chat_history', 'events_cache']
        
        print(f"\n📦 Creating collections...")
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
            else:
                print(f"ℹ️  Collection already exists: {collection_name}")
        
        # Create indexes
        print(f"\n📑 Creating indexes...")
        
        # Users collection indexes
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("google_id", ASCENDING)], unique=True)
        print("✅ Users indexes created")
        
        # Chat history indexes
        db.chat_history.create_index([("user_email", ASCENDING)])
        db.chat_history.create_index([("timestamp", ASCENDING)])
        print("✅ Chat history indexes created")
        
        # Events cache indexes
        db.events_cache.create_index([("user_email", ASCENDING)])
        db.events_cache.create_index([("event_id", ASCENDING)])
        print("✅ Events cache indexes created")
        
        print(f"\n🎉 Database initialization completed successfully!")
        print(f"📊 Database: {settings.DATABASE_NAME}")
        print(f"📦 Collections: {', '.join(collections)}")
        
        # Show stats
        print(f"\n📈 Collection Stats:")
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            print(f"   {collection_name}: {count} documents")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Make sure MongoDB is running")
        print(f"   2. Check MONGODB_URI in backend/.env")
        print(f"   3. For local MongoDB, default is: mongodb://localhost:27017/")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 calPal Database Initialization")
    print("=" * 60)
    init_database()