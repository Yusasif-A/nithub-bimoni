"""
Simple script to recreate user after deletion
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

from bmoni_client import get_or_create_bmoni_user, ensure_wallet_created

PHONE = "+2348020812523"


async def main():
    print("="*60)
    print("RECREATE USER AND WALLET")
    print("="*60)
    
    # Wait longer for BMONI to fully process the deletion
    print("\n⏳ Waiting 10 seconds for BMONI to process previous deletion...")
    await asyncio.sleep(10)
    
    # Create user
    print("\n👤 Creating BMONI user...")
    bmoni_user_id = await get_or_create_bmoni_user(PHONE, "Test User")
    
    if not bmoni_user_id:
        print("❌ Failed to create user")
        print("\nTry again in a few minutes. BMONI may need more time to process the deletion.")
        return
    
    print(f"✅ User created: {bmoni_user_id}")
    
    # Create wallet
    print("\n🏦 Creating wallet...")
    wallet_result = await ensure_wallet_created(PHONE, bmoni_user_id, currency="CNGN")
    
    if wallet_result.get("success"):
        print(f"\n🎉 SUCCESS!")
        print(f"   BMONI User ID: {bmoni_user_id}")
        print(f"   Wallet ID: {wallet_result.get('wallet_id')}")
        print(f"   Wallet Address: {wallet_result.get('wallet_address')}")
        
        # Show owner key
        from key_vault import get_user_address
        owner_address = get_user_address(bmoni_user_id)
        print(f"\n🔐 Owner key in vault: {owner_address}")
        print(f"\n✅ Signatures should now work correctly!")
    else:
        print(f"\n❌ Failed to create wallet: {wallet_result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
