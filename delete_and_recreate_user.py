"""
Delete BMONI user completely and recreate with correct owner key

This script:
1. Gets user info from BMONI
2. Deletes the user (this removes the wallet too)
3. Deletes key vault entry and generates new one
4. Recreates user with same phone number
5. Creates wallet with the new owner key

This ensures the owner key in key vault matches what BMONI has registered.
"""

import sys
import os
import asyncio
import httpx
import logging
from dotenv import load_dotenv

# Load environment first
env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_client import bmoni_client, get_or_create_bmoni_user, ensure_wallet_created
from bmoni_store import bmoni_store
from pymongo import MongoClient
from pymongo.server_api import ServerApi

PHONE = "+2348020812523"
OLD_BMONI_USER_ID = "a348e005-bc63-4809-99c8-5ebb9a3aae5b"


async def get_user_info(bmoni_user_id: str):
    """Get user information from BMONI"""
    return await bmoni_client._request("GET", f"/v1/users/{bmoni_user_id}")


async def delete_user(bmoni_user_id: str):
    """Delete user from BMONI (removes wallet too)"""
    return await bmoni_client._request("DELETE", f"/v1/users/{bmoni_user_id}")


def delete_key_vault_entry(bmoni_user_id: str):
    """Delete keypair from key vault so a new one will be generated"""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI not set")
        return False
    
    try:
        client = MongoClient(mongo_uri, server_api=ServerApi("1"))
        db = client.get_database("SabiSpend")
        key_vault_col = db.get_collection("evm_key_vault")
        
        result = key_vault_col.delete_one({"bmoni_user_id": bmoni_user_id})
        client.close()
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"❌ Failed to delete from key vault: {e}")
        return False


def delete_db_entry(phone_number: str):
    """Delete account from local database"""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI not set")
        return False
    
    try:
        client = MongoClient(mongo_uri, server_api=ServerApi("1"))
        db = client.get_database("SabiSpend")
        accounts_col = db.get_collection("bmoni_accounts")
        
        result = accounts_col.delete_one({"phone_number": phone_number})
        client.close()
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"❌ Failed to delete from DB: {e}")
        return False


async def main():
    print("="*70)
    print("DELETE AND RECREATE USER WITH CORRECT OWNER KEY")
    print("="*70)
    
    # Step 1: Get current user info
    print("\n📋 Step 1: Getting current user info from BMONI...")
    user_info = await get_user_info(OLD_BMONI_USER_ID)
    
    if "error" in user_info:
        print(f"❌ Failed to get user info: {user_info.get('error')}")
        if user_info.get("status_code") == 404:
            print("   User already deleted from BMONI")
        else:
            return
    else:
        print(f"✅ User found:")
        print(f"   Phone: {user_info.get('phoneNumber')}")
        print(f"   Email: {user_info.get('email')}")
        print(f"   First Name: {user_info.get('firstName')}")
    
    # Step 2: Delete user from BMONI
    print("\n🗑️  Step 2: Deleting user from BMONI...")
    delete_result = await delete_user(OLD_BMONI_USER_ID)
    
    if "error" in delete_result:
        print(f"⚠️  Delete failed: {delete_result.get('error')}")
        if delete_result.get("status_code") == 404:
            print("   User already deleted (continuing...)")
        else:
            response = input("\n   Continue anyway? (yes/no): ")
            if response.lower() != "yes":
                print("\n❌ Cancelled by user")
                return
    else:
        print("✅ User deleted from BMONI")
    
    # Step 3: Delete key vault entry
    print("\n🔑 Step 3: Deleting old keypair from key vault...")
    if delete_key_vault_entry(OLD_BMONI_USER_ID):
        print("✅ Old keypair deleted from key vault")
    else:
        print("⚠️  Key vault entry not found (may already be deleted)")
    
    # Step 4: Delete from local database
    print("\n💾 Step 4: Deleting from local database...")
    if delete_db_entry(PHONE):
        print("✅ Account deleted from local DB")
    else:
        print("⚠️  DB entry not found (may already be deleted)")
    
    # Step 5: Wait a moment for BMONI to process
    print("\n⏳ Waiting 3 seconds for BMONI to process deletion...")
    await asyncio.sleep(3)
    
    # Step 6: Recreate user
    print("\n👤 Step 5: Creating new BMONI user...")
    new_bmoni_user_id = await get_or_create_bmoni_user(PHONE, "Test User")
    
    if not new_bmoni_user_id:
        print("❌ Failed to create new user")
        return
    
    print(f"✅ New user created: {new_bmoni_user_id}")
    
    # Step 7: Create wallet (will generate new keypair automatically)
    print("\n🏦 Step 6: Creating wallet with new keypair...")
    wallet_result = await ensure_wallet_created(PHONE, new_bmoni_user_id, currency="CNGN")
    
    if wallet_result.get("success"):
        print(f"\n🎉 SUCCESS! Everything recreated properly:")
        print(f"   New BMONI User ID: {new_bmoni_user_id}")
        print(f"   Wallet ID: {wallet_result.get('wallet_id')}")
        print(f"   Wallet Address: {wallet_result.get('wallet_address')}")
        print(f"\n✅ The owner key in key vault now matches BMONI's registration!")
        print(f"✅ Signatures should work correctly now!")
        
        # Verify in key vault
        from key_vault import get_user_address
        owner_address = get_user_address(new_bmoni_user_id)
        print(f"\n🔐 Owner key in vault: {owner_address}")
        
    else:
        print(f"\n❌ Failed to create wallet: {wallet_result.get('error')}")


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will COMPLETELY DELETE the user from BMONI!")
    print("   - All wallet data will be lost")
    print("   - Any balance will be inaccessible")
    print("   - A fresh user and wallet will be created")
    print("   - The new user will have a different BMONI user ID\n")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(main())
    else:
        print("\n❌ Cancelled by user")
