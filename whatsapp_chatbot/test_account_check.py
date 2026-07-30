#!/usr/bin/env python3
"""
Test the account check and recovery for existing BMONI users
"""

import asyncio
from bmoni_client import get_or_create_bmoni_user
from bmoni_store import bmoni_store

PHONE = "+2348020812523"
USER_NAME = "Test User"

async def main():
    print(f"\n🔍 Testing account recovery for {PHONE}...\n")
    
    # Check database first
    print("Step 1: Checking local database...")
    existing = bmoni_store.get_by_phone(PHONE)
    if existing:
        print(f"✅ Found in database:")
        print(f"   BMONI User ID: {existing.get('bmoni_user_id')}")
        print(f"   Lifecycle: {existing.get('lifecycle_stage')}")
        if existing.get('wallet'):
            print(f"   Wallet: {existing['wallet'].get('address')}")
    else:
        print("❌ Not found in database")
    
    # Try to get or create (should handle 409 gracefully)
    print("\nStep 2: Testing get_or_create_bmoni_user...")
    bmoni_user_id = await get_or_create_bmoni_user(PHONE, USER_NAME)
    
    if bmoni_user_id:
        print(f"✅ Success! BMONI User ID: {bmoni_user_id}")
        
        # Verify it's saved
        print("\nStep 3: Verifying database update...")
        final_check = bmoni_store.get_by_phone(PHONE)
        if final_check and final_check.get('bmoni_user_id') == bmoni_user_id:
            print("✅ Database updated successfully")
            print(f"   BMONI User ID: {final_check.get('bmoni_user_id')}")
            print(f"   Lifecycle: {final_check.get('lifecycle_stage')}")
        else:
            print("⚠️ Database not updated correctly")
    else:
        print("❌ Failed to get/create user")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
