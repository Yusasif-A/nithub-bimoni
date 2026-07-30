#!/usr/bin/env python3
"""
Setup wallet for existing BMONI user
"""

import asyncio
from bmoni_store import bmoni_store
from bmoni_client import ensure_wallet_created

# Existing BMONI user found in API
PHONE = "+2348020812523"
BMONI_USER_ID = "a348e005-bc63-4809-99c8-5ebb9a3aae5b"
NAME = "Test User"
EMAIL = "sabispend+2348020812523@example.com"

async def setup():
    print(f"\n🔧 Setting up existing BMONI user {PHONE}...\n")
    
    # Save to bmoni_store
    bmoni_store.save_user(
        PHONE,
        BMONI_USER_ID,
        first_name=NAME,
        email=EMAIL,
        lifecycle_stage="user_created"
    )
    print(f"✅ Saved user to database")
    print(f"   BMONI User ID: {BMONI_USER_ID}")
    
    # Create wallet
    print(f"\n🔐 Creating wallet...")
    wallet_result = await ensure_wallet_created(PHONE, BMONI_USER_ID)
    
    if wallet_result.get("success"):
        print(f"\n🎉 Wallet created!")
        print(f"   Wallet ID: {wallet_result.get('wallet_id')}")
        print(f"   Wallet Address: {wallet_result.get('wallet_address')}")
        
        print("\n" + "="*60)
        print("📋 SEND TO BMONI TEAM FOR FUNDING:")
        print("="*60)
        print(f"Phone: {PHONE}")
        print(f"BMONI User ID: {BMONI_USER_ID}")
        print(f"Wallet ID: {wallet_result.get('wallet_id')}")
        print(f"Wallet Address: {wallet_result.get('wallet_address')}")
        print("="*60 + "\n")
    else:
        print(f"\n❌ Wallet creation failed: {wallet_result.get('error')}")

if __name__ == "__main__":
    asyncio.run(setup())
