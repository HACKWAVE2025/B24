from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://akifaliparvez:<db_password>@cluster0.lg4jnnj.mongodb.net/?appName=Cluster0')
DB_NAME = os.getenv('DB_NAME', 'figment')

# Global connection
_client = None
_db = None

def get_db():
    """Get MongoDB database instance"""
    global _db
    if _db is None:
        connect()
    return _db

def connect():
    """Connect to MongoDB"""
    global _client, _db
    try:
        if _client is None:
            # Replace <db_password> placeholder if still present
            connection_string = MONGODB_URI
            if '<db_password>' in connection_string:
                print("⚠️  WARNING: Please set your MongoDB password in .env file!")
                print("   Replace <db_password> in MONGODB_URI with your actual password")
                raise ValueError("MongoDB password not set in .env file")
            
            _client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            _client.admin.command('ping')
            print("✅ Connected to MongoDB successfully!")
        
        _db = _client[DB_NAME]
        init_collections()
        return _db
    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("   Please check your MONGODB_URI in .env file")
        raise
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        raise

def init_collections():
    """Initialize collections with indexes"""
    global _db
    if _db is None:
        connect()
    
    # Users Collection
    users = _db.users
    users.create_index("email", unique=True)
    users.create_index("google_id")
    users.create_index("created_at")
    
    # Scam Reports Collection
    scam_reports = _db.scam_reports
    scam_reports.create_index("receiver_id", unique=True)
    scam_reports.create_index("updated_at")
    
    # Transactions Collection
    transactions = _db.transactions
    transactions.create_index("user_id")
    transactions.create_index("receiver_id")
    transactions.create_index("created_at")
    
    # User Behavior Collection
    user_behavior = _db.user_behavior
    user_behavior.create_index("user_id", unique=True)
    
    # Feedback Collection
    feedback = _db.feedback
    feedback.create_index("transaction_id")
    feedback.create_index("receiver_id")
    feedback.create_index("created_at")
    
    print("✅ Collections initialized with indexes!")

def close_connection():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        print("MongoDB connection closed")
