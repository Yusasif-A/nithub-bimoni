"""
Setup a new SabiSpend user with wallet for testing

This script completes the full onboarding process:
1. Creates BMONI user account
2. Generates EVM keypair (encrypted)
3. Creates managed wallet
4. Verifies setup

Usage:
    python setup_new_user.py <phone_number> <user_name>

Example:
    python setup_new_user.py +2348142392322 "Test User"
"""

import sys
import os
import asyncio
import logging

# Add whatsapp_chatbot to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_store import bmoni_store
from bmoni_client import get_or_create_bmoni_user, ensure_wallet_created, get_user_balance_naira


def _normalize(phone: str) -> str:
    return phone if phone.startswith("+") else f"+{phone}"


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExample: python setup_new_user.py +2348142392322 'Test User'")
        sys.exit(1)

    phone_number = _normalize(sys.argv[1])
    user_name = sys.argv[2] if len(sys.argv) > 2 else "SabiSpend User"

    print(f"\n=== Setting up SabiSpend account for {phone_number} ===\n")

    # Step 1: Check if user already exists in local database
    print(f"=== Step 1: Checking local database ===")
    existing_account = bmoni_store.get_by_phone(phone_number)
    
    if existing_account:
        print(f"✅ Account found in local database")
        bmoni_user_id = existing_account.get("bmoni_user_id")
        if bmoni_user_id:
            print(f"✅ BMONI User ID: {bmoni_user_id}")
        else:
            print(f"⚠️ Account exists but missing bmoni_user_id")
    else:
        print(f"ℹ️ No existing account in local database")
        bmoni_user_id = None

    # Step 2: Get or create BMONI user
    print(f"\n=== Step 2: Creating/verifying BMONI user ===")
    bmoni_user_id = await get_or_create_bmoni_user(phone_number, user_name)
    
    if not bmoni_user_id:
        print(f"❌ Failed to create/get BMONI user")
        sys.exit(1)
    
    print(f"✅ BMONI User ID: {bmoni_user_id}")

    # Step 3: Create wallet (server-side signing, automatic)
    print(f"\n=== Step 3: Creating wallet ===")
    wallet_result = await ensure_wallet_created(phone_number, bmoni_user_id)
    
    if not wallet_result.get("success"):
        print(f"❌ Wallet creation failed: {wallet_result.get('error')}")
        sys.exit(1)
    
    wallet_id = wallet_result.get("wallet_id")
    wallet_address = wallet_result.get("wallet_address")
    
    if wallet_result.get("already_exists"):
        print(f"✅ Wallet already exists")
    else:
        print(f"✅ Wallet created successfully!")
    
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")

    # Step 4: Check balance
    print(f"\n=== Step 4: Checking wallet balance ===")
    balance = await get_user_balance_naira(bmoni_user_id)
    print(f"💰 Current balance: ₦{balance:,.2f}")

    # Step 5: Verify final setup
    print(f"\n=== Step 5: Verifying setup ===")
    final_account = bmoni_store.get_by_phone(phone_number)
    
    if not final_account:
        print(f"❌ Account not found in database after setup")
        sys.exit(1)
    
    has_user_id = bool(final_account.get("bmoni_user_id"))
    has_wallet = bool(final_account.get("wallet"))
    
    print(f"✅ Account in database: {has_user_id}")
    print(f"✅ Wallet in database: {has_wallet}")
    
    if has_user_id and has_wallet:
        print(f"\n🎉 Setup complete! User {phone_number} is ready to:")
        print(f"   - Receive money transfers")
        print(f"   - Send money to other users")
        print(f"   - Use SabiSpend features")
        print(f"\nAccount Details:")
        print(f"   Phone: {phone_number}")
        print(f"   Name: {user_name}")
        print(f"   BMONI User ID: {bmoni_user_id}")
        print(f"   Wallet Address: {wallet_address}")
        print(f"   Balance: ₦{balance:,.2f}")
    else:
        print(f"\n⚠️ Setup incomplete - some components missing")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
