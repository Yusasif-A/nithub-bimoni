import os
import logging
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_user_conversations(user_id: str):
    """
    Delete all conversations for a specific user from MongoDB
    
    Args:
        user_id: User's phone number (e.g., '08020812523')
    
    Returns:
        int: Number of conversations deleted
    """
    connection_string = os.getenv("MONGO_URI")
    if not connection_string:
        logger.error("MONGO_URI is not set in .env file")
        return 0
    
    try:
        # Connect to MongoDB
        client = MongoClient(connection_string, server_api=ServerApi('1'))
        client.admin.command('ping')
        logger.info("✅ Connected to MongoDB Atlas")
        
        # Get the database and collection
        db = client.get_database("SabiSpend")
        conversations_collection = db.get_collection("conversations")
        
        # Count conversations before deletion
        count_before = conversations_collection.count_documents({"user_id": user_id})
        logger.info(f"Found {count_before} conversations for user {user_id}")
        
        if count_before == 0:
            logger.info(f"No conversations found for user {user_id}")
            return 0
        
        # Delete all conversations for this user
        result = conversations_collection.delete_many({"user_id": user_id})
        deleted_count = result.deleted_count
        
        logger.info(f"✅ Successfully deleted {deleted_count} conversations for user {user_id}")
        
        # Close connection
        client.close()
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Failed to delete conversations: {e}")
        return 0


if __name__ == "__main__":
    phone_numbers = [
        "2348020812523",
        # "2348134232353"
    ]
    
    print("=" * 60)
    print("CONVERSATION DELETION SCRIPT")
    print("=" * 60)
    print("\nThis script will delete conversations for the following users:")
    for number in phone_numbers:
        print(f"  - {number}")
    
    # Ask for confirmation
    confirmation = input("\n⚠️  Are you sure you want to delete these conversations? (yes/no): ")
    
    if confirmation.lower() == "yes":
        print("\nStarting deletion...\n")
        total_deleted = 0
        
        for phone_number in phone_numbers:
            deleted = delete_user_conversations(phone_number)
            total_deleted += deleted
            print()
        
        print("=" * 60)
        print(f"TOTAL CONVERSATIONS DELETED: {total_deleted}")
        print("=" * 60)
    else:
        print("\n❌ Deletion cancelled.")
