"""
Phone Number Mapping for SabiSpend
===================================

Maps WhatsApp phone numbers to BMONI phone numbers for testing/demo purposes.

Use case: 
- WhatsApp uses +2348020812523 for testing
- BMONI account uses +2348134232353 (actual account)
- Code automatically translates between them

This allows using a fixed WhatsApp number for demos while BMONI requires unique numbers.
"""

import os
import logging
from typing import Optional, Dict
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class PhoneMapper:
    """Maps WhatsApp phone numbers to BMONI phone numbers"""
    
    def __init__(self):
        self.collection = None
        uri = os.getenv("MONGO_URI")
        
        if uri:
            try:
                client = MongoClient(uri, server_api=ServerApi("1"))
                db = client.get_database("SabiSpend")
                self.collection = db.get_collection("phone_mappings")
                self.collection.create_index("whatsapp_phone", unique=True)
            except Exception as e:
                logger.error(f"❌ Phone mapper initialization failed: {e}")
    
    def get_bmoni_phone(self, whatsapp_phone: str) -> str:
        """
        Get BMONI phone number for a WhatsApp phone number
        
        Args:
            whatsapp_phone: Phone number from WhatsApp (e.g., +2348020812523)
        
        Returns:
            BMONI phone number if mapped, otherwise returns the original number
        """
        if self.collection is None:
            return whatsapp_phone
        
        try:
            mapping = self.collection.find_one({"whatsapp_phone": whatsapp_phone})
            if mapping and mapping.get("bmoni_phone"):
                bmoni_phone = mapping["bmoni_phone"]
                logger.info(f"📞 Mapping {whatsapp_phone} → {bmoni_phone} (BMONI)")
                return bmoni_phone
        except Exception as e:
            logger.error(f"❌ Error looking up phone mapping: {e}")
        
        return whatsapp_phone
    
    def get_mapping_info(self, whatsapp_phone: str) -> Optional[Dict]:
        """
        Get full mapping information for a WhatsApp phone number
        
        Returns:
            Dict with bmoni_phone, bmoni_user_id, etc., or None if not mapped
        """
        if self.collection is None:
            return None
        
        try:
            return self.collection.find_one({"whatsapp_phone": whatsapp_phone}, {"_id": 0})
        except Exception as e:
            logger.error(f"❌ Error getting mapping info: {e}")
            return None
    
    def create_mapping(
        self,
        whatsapp_phone: str,
        bmoni_phone: str,
        bmoni_user_id: str,
        note: str = ""
    ) -> bool:
        """
        Create a phone number mapping
        
        Args:
            whatsapp_phone: WhatsApp phone number (for chat)
            bmoni_phone: BMONI phone number (for account)
            bmoni_user_id: BMONI user ID
            note: Optional note about the mapping
        
        Returns:
            True if successful, False otherwise
        """
        if self.collection is None:
            return False
        
        try:
            from datetime import datetime, timezone
            
            self.collection.update_one(
                {"whatsapp_phone": whatsapp_phone},
                {
                    "$set": {
                        "whatsapp_phone": whatsapp_phone,
                        "bmoni_phone": bmoni_phone,
                        "bmoni_user_id": bmoni_user_id,
                        "note": note,
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ Created mapping: {whatsapp_phone} → {bmoni_phone}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating phone mapping: {e}")
            return False
    
    def delete_mapping(self, whatsapp_phone: str) -> bool:
        """Delete a phone mapping"""
        if self.collection is None:
            return False
        
        try:
            result = self.collection.delete_one({"whatsapp_phone": whatsapp_phone})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Error deleting mapping: {e}")
            return False


# Global instance
phone_mapper = PhoneMapper()


# Convenience functions
def get_bmoni_phone(whatsapp_phone: str) -> str:
    """Get BMONI phone for WhatsApp phone (returns original if no mapping)"""
    return phone_mapper.get_bmoni_phone(whatsapp_phone)


def get_mapping_info(whatsapp_phone: str) -> Optional[Dict]:
    """Get full mapping info"""
    return phone_mapper.get_mapping_info(whatsapp_phone)


def create_phone_mapping(whatsapp_phone: str, bmoni_phone: str, bmoni_user_id: str, note: str = "") -> bool:
    """Create a new phone mapping"""
    return phone_mapper.create_mapping(whatsapp_phone, bmoni_phone, bmoni_user_id, note)
