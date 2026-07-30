import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pending responses for feedback pairing (stores question and response for feedback)
pending_responses: Dict[str, Dict[str, str]] = {}


def get_feedback_collection():
    """Initialize MongoDB connection and return feedback collection"""
    connection_string = os.getenv("MONGO_URI")
    if not connection_string:
        logger.warning("MONGO_URI is not set - feedback logging will be disabled")
        return None, None
    
    try:
        client = MongoClient(connection_string, server_api=ServerApi('1'))
        client.admin.command('ping')
        logger.info("Connected to MongoDB Atlas for feedback!")
        db = client.get_database("SabiSpend")
        return db.get_collection("conversations"), db.get_collection("user_settings")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None, None


# Initialize collections
feedback_collection, settings_collection = get_feedback_collection()


def store_feedback(thread_id: str, user_name: str, question: str, response: str, feedback_type: str) -> bool:
    """
    Store user feedback in MongoDB
    
    Args:
        thread_id: User's phone number (thread identifier)
        user_name: User's display name
        question: User's original question
        response: Agent's response
        feedback_type: 'like' or 'dislike'
    
    Returns:
        bool: True if stored successfully, False otherwise
    """
    if feedback_collection is None:
        logger.warning(f"⚠️ MongoDB feedback collection not available")
        return False
    
    try:
        feedback_doc = {
            "user_id": thread_id,
            "user_name": user_name,
            "question": question,
            "response": response,
            "feedback": feedback_type,
            "timestamp": datetime.utcnow()
        }
        result = feedback_collection.insert_one(feedback_doc)
        logger.info(f"✅ Feedback saved to MongoDB! ID: {result.inserted_id}")
        logger.info(f"   User: {user_name} ({thread_id})")
        logger.info(f"   Question: {question[:100]}...")
        logger.info(f"   Response: {response[:100]}...")
        logger.info(f"   Feedback: {feedback_type}")
        return True
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")
        return False


def store_conversation(thread_id: str, user_name: str, question: str, response: str, feedback: str = None) -> bool:
    """
    Store conversation (question + response) in MongoDB.
    Feedback is optional and can be updated later.
    
    Args:
        thread_id: User's phone number
        user_name: User's display name
        question: User's question
        response: Agent's response
        feedback: 'like', 'dislike', or None
    
    Returns:
        bool: Success
    """
    if feedback_collection is None:
        logger.warning("⚠️ MongoDB feedback collection not available")
        return False
    
    try:
        doc = {
            "user_id": thread_id,
            "user_name": user_name,
            "question": question,
            "response": response,
            "feedback": feedback,  # None initially
            "timestamp": datetime.utcnow(),
            "has_feedback": feedback is not None
        }
        
        # Use upsert: if feedback comes later, we can update it
        result = feedback_collection.update_one(
            {
                "user_id": thread_id,
                "question": question,
                "response": response,
                "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=10)}  # rough match
            },
            {"$set": doc},
            upsert=True
        )
        
        if result.upserted_id:
            logger.info(f"✅ Conversation saved (new): {result.upserted_id}")
        elif result.modified_count > 0:
            logger.info("✅ Conversation feedback updated")
        else:
            logger.info("✅ Conversation saved (matched existing)")
            
        return True
    except Exception as e:
        logger.error(f"Failed to store conversation: {e}")
        return False

def store_pending_response(thread_id: str, question: str, response: str):
    """
    Store a pending response waiting for feedback
    
    Args:
        thread_id: User's phone number (thread identifier)
        question: User's original question
        response: Agent's response
    """
    pending_responses[thread_id] = {
        "question": question,
        "response": response
    }
    logger.info(f"[Feedback] Stored question & response for feedback tracking (thread: {thread_id})")


def get_pending_response(thread_id: str) -> Optional[Dict[str, str]]:
    """
    Get and remove pending response for a user
    
    Args:
        thread_id: User's phone number (thread identifier)
    
    Returns:
        Dict with 'question' and 'response' keys, or None if not found
    """
    return pending_responses.pop(thread_id, None)


def has_pending_response(thread_id: str) -> bool:
    """
    Check if there's a pending response for a user
    
    Args:
        thread_id: User's phone number (thread identifier)
    
    Returns:
        bool: True if pending response exists
    """
    return thread_id in pending_responses


def get_user_language(thread_id: str) -> str:
    """Get user's preferred language from MongoDB, default to 'english'"""
    if settings_collection is None:
        return "english"
    try:
        user_settings = settings_collection.find_one({"user_id": thread_id})
        if user_settings and "language" in user_settings:
            return user_settings["language"]
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
    return "english"

def is_new_user(thread_id: str) -> bool:
    """Return True if this phone number has never appeared in the conversations collection."""
    if feedback_collection is None:
        return False
    try:
        return feedback_collection.count_documents({"user_id": thread_id}, limit=1) == 0
    except Exception as e:
        logger.error(f"Error checking new user: {e}")
        return False


def set_user_journey(thread_id: str, journey: str, business_type: str = None) -> bool:
    """
    Save user's profile to MongoDB.
    journey: 'onboarding_language_selected' | 'onboarding_complete'
    business_type: 'trader' | 'market_woman' | 'artisan' | 'individual' | 'other'
    """
    if settings_collection is None:
        return False
    try:
        update = {"journey": journey, "updated_at": datetime.utcnow()}
        if business_type is not None:
            update["business_type"] = business_type
        settings_collection.update_one(
            {"user_id": thread_id},
            {"$set": update},
            upsert=True
        )
        logger.info(f"✅ User {thread_id} journey set to {journey}")
        return True
    except Exception as e:
        logger.error(f"Failed to set user journey: {e}")
        return False


def get_user_journey(thread_id: str) -> dict:
    """
    Get user's saved profile.
    Returns dict with 'journey' and optionally 'business_type', or empty dict.
    """
    if settings_collection is None:
        return {}
    try:
        doc = settings_collection.find_one({"user_id": thread_id})
        if doc and "journey" in doc:
            return {
                "journey": doc["journey"],
                "business_type": doc.get("business_type"),
            }
    except Exception as e:
        logger.error(f"Error getting user journey: {e}")
    return {}


def get_all_users_with_journey() -> list:
    """Return all users that have a saved journey — used for daily tips."""
    if settings_collection is None:
        return []
    try:
        docs = list(settings_collection.find(
            {"journey": {"$exists": True}},
            {"user_id": 1, "journey": 1, "business_type": 1, "language": 1, "_id": 0}
        ))
        return docs
    except Exception as e:
        logger.error(f"Error fetching users with journey: {e}")
        return []


def set_user_language(thread_id: str, language: str) -> bool:
    """Save user's preferred language to MongoDB"""
    if settings_collection is None:
        return False
    try:
        settings_collection.update_one(
            {"user_id": thread_id},
            {"$set": {"language": language, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        logger.info(f"User {thread_id} language set to {language}")
        return True
    except Exception as e:
        logger.error(f"Failed to set user language: {e}")
        return False

