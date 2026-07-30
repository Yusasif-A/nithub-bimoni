#!/usr/bin/env python3
"""
Create BMONI wallet for test user
==================================

Use this to manually create a wallet for testing.

Usage:
    python create_test_wallet.py
"""

import asyncio
import logging
from bmoni_client import get_or_create_bmoni_user, ensure_wallet_created
from bmoni_store import bmoni_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_wallet_for_user(phone_number: str, user_name: str = "Test User"):
    """Create BMONI wallet for a specific user"""
    
    logger.info(f"🔐 Creating BMONI wallet for {phone_number}...")
    
    # Check if already exists
    existing = bmoni_store.get_by_phone(phone_number)
    if existing and existing.get("bmoni_user_id"):
        logger.info(f"✅ Account already exists!")
        logger.info(f"   BMONI User ID: {existing['bmoni_user_id']}")
        if existing.get("wallet"):
            logger.info(f"   Wallet ID: {existing['wallet'].get('id')}")
            logger.info(f"   Wallet Address: {existing['wallet'].get('address')}")
            return existing
        else:
            logger.info(f"   Wallet not created yet - creating now...")
            bmoni_user_id = existing["bmoni_user_id"]
    else:
        # Create BMONI user
        logger.info(f"📝 Creating BMONI user...")
        bmoni_user_id = await get_or_create_bmoni_user(phone_number, user_name)
        
        if not bmoni_user_id:
            logger.error("❌ Failed to create BMONI user")
            return None
        
        logger.info(f"✅ BMONI User ID: {bmoni_user_id}")
    
    # Create wallet
    logger.info(f"🔐 Creating wallet...")
    wallet_result = await ensure_wallet_created(phone_number, bmoni_user_id)
    
    if wallet_result.get("success"):
        logger.info(f"🎉 Wallet created successfully!")
        logger.info(f"   Wallet ID: {wallet_result.get('wallet_id')}")
        logger.info(f"   Wallet Address: {wallet_result.get('wallet_address')}")
        logger.info(f"   Currency: {wallet_result.get('currency')}")
        
        # Print info for BMONI team
        print("\n" + "="*60)
        print("📋 SEND THESE DETAILS TO BMONI TEAM FOR FUNDING:")
        print("="*60)
        print(f"Phone Number: {phone_number}")
        print(f"BMONI User ID: {bmoni_user_id}")
        print(f"Wallet ID: {wallet_result.get('wallet_id')}")
        print(f"Wallet Address: {wallet_result.get('wallet_address')}")
        print("="*60 + "\n")
        
        return wallet_result
    else:
        logger.error(f"❌ Wallet creation failed: {wallet_result.get('error')}")
        return None


if __name__ == "__main__":
    # Test user - completely random fresh number
    import random
    random_digits = random.randint(10000000, 99999999)
    PHONE = f"+234{random_digits}"
    NAME = "SabiSpend Demo User"
    
    print(f"\n🚀 Creating wallet for {PHONE}...\n")
    result = asyncio.run(create_wallet_for_user(PHONE, NAME))
    
    if result:
        print("\n✅ Success! Wallet is ready for testing.")
    else:
        print("\n❌ Failed to create wallet. Check logs above.")
