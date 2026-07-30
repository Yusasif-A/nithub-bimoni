"""
Check BMONI user and wallet status

Usage:
    python check_user_status.py <phone_number>

Example:
    python check_user_status.py +2348142392322
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


def _normalize(phone: str) -> str:
    return phone if phone.startswith("+") else f"+{phone}"


async def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    phone_number = _normalize(sys.argv[1])

    print(f"\n=== Checking user status for {phone_number} ===\n")

    # Check local database
    account = bmoni_store.get_by_phone(phone_number)
    if not account:
        print(f"❌ No account found in local database")
        sys.exit(1)

    bmoni_user_id = account.get("bmoni_user_id")
    print(f"✅ BMONI User ID: {bmoni_user_id}")

    if account.get("wallet"):
        wallet = account["wallet"]
        print(f"✅ Wallet ID: {wallet.get('id')}")
        print(f"✅ Wallet Address: {wallet.get('address')}")
        print(f"✅ Currency: {wallet.get('currency', 'CNGN')}")
    else:
        print(f"❌ No wallet in local database")

    # Check BMONI API for wallets
    print(f"\n=== Checking BMONI API for wallets ===")
    wallets_result = await bmoni_client.get_wallets(bmoni_user_id)
    
    if "error" in wallets_result:
        print(f"❌ Failed to get wallets: {wallets_result['error']}")
    else:
        # Handle different response formats
        if isinstance(wallets_result, list):
            wallets = wallets_result
        elif isinstance(wallets_result, dict):
            wallets = wallets_result.get("wallets", wallets_result.get("data", {}).get("wallets", []))
        else:
            wallets = []
        
        print(f"Found {len(wallets)} wallet(s):")
        for w in wallets:
            print(f"  - ID: {w.get('id')}")
            print(f"    Address: {w.get('address')}")
            print(f"    Currency: {w.get('currency')}")
            print(f"    Status: {w.get('status')}")
            print()

    # Check onboarding status
    print(f"=== Checking onboarding status ===")
    status_result = await bmoni_client.get_wallet_status(bmoni_user_id)
    
    if "error" in status_result:
        print(f"❌ Failed to get status: {status_result['error']}")
    else:
        status = status_result.get("status", {})
        print(f"Onboarding status:")
        print(f"  {status}")


if __name__ == "__main__":
    asyncio.run(main())
