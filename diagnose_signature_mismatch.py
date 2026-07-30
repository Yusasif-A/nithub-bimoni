"""
Diagnose signature mismatch issue

This script checks:
1. What address is stored in our key vault
2. What address is registered with BMONI for the wallet
3. Verifies if they match

Usage:
    python diagnose_signature_mismatch.py <phone_number>

Example:
    python diagnose_signature_mismatch.py +2348020812523
"""

import sys
import os
import asyncio
import logging

# Add whatsapp_chatbot to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_store import bmoni_store
from bmoni_client import bmoni_client
from key_vault import get_user_address


def _normalize(phone: str) -> str:
    return phone if phone.startswith("+") else f"+{phone}"


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    phone_number = _normalize(sys.argv[1])

    print(f"\n=== Diagnosing Signature Mismatch for {phone_number} ===\n")

    # Step 1: Get user from local database
    account = bmoni_store.get_by_phone(phone_number)
    if not account:
        print(f"❌ No account found for {phone_number}")
        sys.exit(1)

    bmoni_user_id = account.get("bmoni_user_id")
    if not bmoni_user_id:
        print(f"❌ Account missing bmoni_user_id")
        sys.exit(1)

    print(f"✅ BMONI User ID: {bmoni_user_id}")

    wallet = account.get("wallet")
    if not wallet:
        print(f"❌ No wallet in local database")
        sys.exit(1)

    local_wallet_address = wallet.get("address")
    print(f"✅ Wallet stored locally:")
    print(f"   Wallet ID: {wallet.get('id')}")
    print(f"   Wallet Address: {local_wallet_address}")
    print(f"   Currency: {wallet.get('currency')}")

    # Step 2: Get address from key vault
    print(f"\n=== Checking Key Vault ===")
    key_vault_address = get_user_address(bmoni_user_id)
    
    if key_vault_address:
        print(f"✅ Key vault has address: {key_vault_address}")
    else:
        print(f"❌ No address found in key vault")

    # Step 3: Get wallet info from BMONI API
    print(f"\n=== Checking BMONI API ===")
    wallets_result = await bmoni_client.get_wallets(bmoni_user_id)
    
    if "error" in wallets_result:
        print(f"❌ Failed to get wallets from BMONI: {wallets_result['error']}")
    else:
        # Handle different response formats
        if isinstance(wallets_result, list):
            wallets = wallets_result
        elif isinstance(wallets_result, dict):
            wallets = wallets_result.get("wallets", wallets_result.get("data", {}).get("wallets", []))
        else:
            wallets = []
        
        print(f"Found {len(wallets)} wallet(s) in BMONI:")
        for w in wallets:
            bmoni_wallet_address = w.get("address")
            print(f"  Wallet ID: {w.get('id')}")
            print(f"  Address: {bmoni_wallet_address}")
            print(f"  Currency: {w.get('currency')}")
            print(f"  Status: {w.get('status')}")
            
            # Check if this is the user's owner address
            if bmoni_wallet_address:
                print(f"  Owner Address (from userOwnerAddress): {w.get('userOwnerAddress')}")

    # Step 4: Compare addresses
    print(f"\n=== Address Comparison ===")
    print(f"Local DB Address:     {local_wallet_address}")
    print(f"Key Vault Address:    {key_vault_address}")
    
    if local_wallet_address and key_vault_address:
        if local_wallet_address.lower() == key_vault_address.lower():
            print(f"❌ MISMATCH: Local DB and Key Vault addresses don't match!")
            print(f"   The wallet address in local DB is the SMART WALLET address")
            print(f"   The key vault address is the OWNER KEY address")
            print(f"   These should be different!")
        else:
            print(f"✅ CORRECT: These are different addresses (as expected)")
            print(f"   {local_wallet_address} = Smart Wallet Address")
            print(f"   {key_vault_address} = Owner Key Address")

    # Step 5: Try to get the actual owner address from BMONI wallet details
    print(f"\n=== Checking Owner Address Registration ===")
    
    # The smart wallet should have been created with key_vault_address as owner
    # Let's verify this by checking what BMONI has registered
    
    print(f"Expected owner address (from key vault): {key_vault_address}")
    print(f"Smart wallet address (from local DB):    {local_wallet_address}")
    
    print(f"\n=== Diagnosis ===")
    if not key_vault_address:
        print(f"❌ PROBLEM: No key in key vault for user {bmoni_user_id}")
        print(f"   Solution: Regenerate wallet with proper key storage")
    else:
        print(f"✅ Key vault has a key for this user")
        print(f"\nThe signature mismatch could be caused by:")
        print(f"1. Wrong 'primaryType' in EIP-712 signing")
        print(f"2. Wallet was created with a different key (not from key vault)")
        print(f"3. Key was regenerated after wallet creation")
        
        print(f"\n💡 Next Steps:")
        print(f"1. Check BMONI console to see registered owner address")
        print(f"2. Compare with key vault address: {key_vault_address}")
        print(f"3. If they don't match, wallet needs to be recreated")


if __name__ == "__main__":
    asyncio.run(main())
