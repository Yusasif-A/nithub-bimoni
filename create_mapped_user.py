"""
Create new BMONI user with phone +2348134232353 and map to WhatsApp +2348020812523

This allows:
- WhatsApp chats use: +2348020812523 (for testing/demo)
- BMONI account uses: +2348134232353 (actual account)
- Code automatically maps between them
"""

import sys
import os
import asyncio
import logging
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_client import get_or_create_bmoni_user, ensure_wallet_created, bmoni_client
from bmoni_store import bmoni_store
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Real BMONI number (new)
BMONI_PHONE = "+2348134232353"

# WhatsApp number (for testing/demo)
WHATSAPP_PHONE = "+2348020812523"

# Test BVN
BVN = "22238719042"


async def main():
    print("="*70)
    print("CREATE MAPPED USER")
    print("="*70)
    print(f"\nBMONI phone:    {BMONI_PHONE} (real account)")
    print(f"WhatsApp phone: {WHATSAPP_PHONE} (mapped for chat)")
    
    # Step 1: Create BMONI user with the NEW phone number
    print(f"\n📱 Step 1: Creating BMONI user with {BMONI_PHONE}...")
    bmoni_user_id = await get_or_create_bmoni_user(BMONI_PHONE, "Test User")
    
    if not bmoni_user_id:
        print("❌ Failed to create BMONI user")
        return
    
    print(f"✅ BMONI User ID: {bmoni_user_id}")
    
    # Step 2: Create wallet
    print(f"\n🏦 Step 2: Creating wallet...")
    wallet_result = await ensure_wallet_created(BMONI_PHONE, bmoni_user_id, currency="CNGN")
    
    if not wallet_result.get("success"):
        print(f"❌ Failed to create wallet: {wallet_result.get('error')}")
        return
    
    print(f"✅ Wallet created:")
    print(f"   Wallet ID: {wallet_result.get('wallet_id')}")
    print(f"   Wallet Address: {wallet_result.get('wallet_address')}")
    
    # Step 3: Activate NGN rail with BVN
    print(f"\n🇳🇬 Step 3: Activating NGN rail with BVN...")
    
    # Submit KYC with BVN
    kyc_payload = {
        "bvn": BVN,
        "address": {
            "street": "123 Test Street",
            "city": "Lagos",
            "state": "Lagos",
            "country": "NG",
            "postalCode": "100001"
        }
    }
    
    kyc_result = await bmoni_client.update_kyc(bmoni_user_id, kyc_payload, BMONI_PHONE)
    if "error" in kyc_result:
        print(f"⚠️  KYC update failed: {kyc_result['error']}")
    else:
        print(f"✅ KYC submitted with BVN")
    
    # Start Nigeria onboarding
    wallet_address = wallet_result.get("wallet_address")
    nigeria_result = await bmoni_client.start_nigeria(
        bmoni_user_id,
        BVN,
        wallet_address,
        wallet_index=0,
        phone_number=BMONI_PHONE
    )
    
    if "error" in nigeria_result:
        print(f"⚠️  Nigeria onboarding failed: {nigeria_result['error']}")
    else:
        print(f"✅ NGN rail activated")
    
    # Step 4: Create phone mapping in database
    print(f"\n🔗 Step 4: Creating phone number mapping...")
    
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri, server_api=ServerApi("1"))
    db = client.get_database("SabiSpend")
    
    # Create mapping collection if it doesn't exist
    mapping_col = db.get_collection("phone_mappings")
    mapping_col.create_index("whatsapp_phone", unique=True)
    
    # Insert mapping
    mapping_col.update_one(
        {"whatsapp_phone": WHATSAPP_PHONE},
        {
            "$set": {
                "whatsapp_phone": WHATSAPP_PHONE,
                "bmoni_phone": BMONI_PHONE,
                "bmoni_user_id": bmoni_user_id,
                "created_at": "2026-07-30T10:00:00Z",
                "note": "WhatsApp demo number mapped to real BMONI account"
            }
        },
        upsert=True
    )
    
    print(f"✅ Mapping created in database")
    
    client.close()
    
    # Step 5: Summary
    print(f"\n🎉 SUCCESS! Setup complete:")
    print(f"   BMONI User ID: {bmoni_user_id}")
    print(f"   BMONI Phone: {BMONI_PHONE}")
    print(f"   WhatsApp Phone: {WHATSAPP_PHONE}")
    print(f"   Wallet: {wallet_result.get('wallet_address')}")
    print(f"   NGN Rail: Activated with BVN {BVN}")
    print(f"\n💬 Users can now chat via WhatsApp at {WHATSAPP_PHONE}")
    print(f"   and the code will use BMONI account {BMONI_PHONE}")


if __name__ == "__main__":
    asyncio.run(main())
