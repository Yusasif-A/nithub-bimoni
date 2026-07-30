"""
Recreate wallet for +2348020812523 with the CORRECT owner key from key vault

IMPORTANT: This will create a NEW wallet. The old wallet address will be abandoned.
The user will need to transfer any funds from the old wallet to the new one.

This script:
1. Gets the current key from key vault (0x0E5372f3239A9A56dECC758E35164683468d67d8)
2. Creates a NEW CNGN wallet with this key as owner
3. Updates the database with the new wallet info
"""

import sys
import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment first
env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_client import bmoni_client, ensure_wallet_created
from bmoni_store import bmoni_store
from key_vault import get_user_address

PHONE = "+2348020812523"
BMONI_USER_ID = "a348e005-bc63-4809-99c8-5ebb9a3aae5b"


async def main():
    print("="*60)
    print("RECREATE WALLET WITH CORRECT OWNER KEY")
    print("="*60)
    
    # Step 1: Check current key vault address
    print("\nStep 1: Checking key vault...")
    key_vault_address = get_user_address(BMONI_USER_ID)
    if not key_vault_address:
        print("❌ No key found in vault!")
        return
    
    print(f"✅ Key vault address: {key_vault_address}")
    
    # Step 2: Check current wallet in DB
    print("\nStep 2: Checking current wallet in database...")
    account = bmoni_store.get_by_phone(PHONE)
    if account and account.get("wallet"):
        old_wallet = account["wallet"]
        print(f"⚠️  Current wallet will be replaced:")
        print(f"   Old Wallet ID: {old_wallet.get('id')}")
        print(f"   Old Wallet Address: {old_wallet.get('address')}")
        print(f"   Currency: {old_wallet.get('currency')}")
        
        # Check balance on old wallet
        balance_result = await bmoni_client.get_balance(BMONI_USER_ID)
        if balance_result.get("success"):
            balances = balance_result.get("balances", [])
            for bal in balances:
                if bal.get("currency") == "CNGN":
                    amount = float(bal.get("balance", 0))
                    print(f"   Balance: ₦{amount:.2f} CNGN")
                    if amount > 0:
                        print("\n⚠️  WARNING: This wallet has a balance!")
                        print("   The old wallet will be abandoned. You'll need to")
                        print("   transfer funds manually from old to new wallet.")
                        response = input("\n   Continue anyway? (yes/no): ")
                        if response.lower() != "yes":
                            print("\n❌ Cancelled by user")
                            return
    
    # Step 3: Delete old wallet from DB (keep bmoni_user_id)
    print("\nStep 3: Removing old wallet from database...")
    bmoni_store.delete_wallet(PHONE)
    print("✅ Old wallet removed from DB")
    
    # Step 4: Create new wallet with correct owner key
    print("\nStep 4: Creating new wallet with correct owner key...")
    print(f"   Owner address: {key_vault_address}")
    
    result = await ensure_wallet_created(PHONE, BMONI_USER_ID, currency="CNGN")
    
    if result.get("success"):
        print(f"\n✅ NEW WALLET CREATED SUCCESSFULLY!")
        print(f"   Wallet ID: {result.get('wallet_id')}")
        print(f"   Wallet Address: {result.get('wallet_address')}")
        print(f"   Owner Key: {key_vault_address}")
        print(f"\n🎉 Signatures should now work correctly!")
        
        # Verify in DB
        account = bmoni_store.get_by_phone(PHONE)
        if account and account.get("wallet"):
            new_wallet = account["wallet"]
            print(f"\n✅ Verified in database:")
            print(f"   Wallet ID: {new_wallet.get('id')}")
            print(f"   Wallet Address: {new_wallet.get('address')}")
    else:
        print(f"\n❌ Failed to create wallet: {result.get('error')}")


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will create a NEW wallet and abandon the old one!")
    print("   The old wallet address will no longer be accessible.")
    print("   Any funds in the old wallet will need to be transferred manually.\n")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(main())
    else:
        print("\n❌ Cancelled by user")
