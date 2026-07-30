"""
Activate NGN rail for a BMONI user

This script activates the Nigerian Naira (NGN) rail which is required
before the user can send or receive money.

Usage:
    python activate_ngn.py <phone_number>

Example:
    python activate_ngn.py +2348142392322
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

    print(f"\n=== Activating NGN rail for {phone_number} ===\n")

    # Get user from database
    account = bmoni_store.get_by_phone(phone_number)
    if not account:
        print(f"❌ No account found for {phone_number}")
        print(f"Run: python setup_new_user.py {phone_number} 'User Name'")
        sys.exit(1)

    bmoni_user_id = account.get("bmoni_user_id")
    if not bmoni_user_id:
        print(f"❌ Account missing bmoni_user_id")
        sys.exit(1)

    wallet = account.get("wallet")
    if not wallet:
        print(f"❌ User doesn't have a wallet yet")
        print(f"Run: python setup_new_user.py {phone_number} 'User Name'")
        sys.exit(1)

    wallet_address = wallet.get("address")
    if not wallet_address:
        print(f"❌ Wallet missing address")
        sys.exit(1)

    print(f"✅ BMONI User ID: {bmoni_user_id}")
    print(f"✅ Wallet Address: {wallet_address}")

    # Check current onboarding status
    print(f"\n=== Checking current onboarding status ===")
    status_result = await bmoni_client.get_wallet_status(bmoni_user_id)
    
    if "error" in status_result:
        print(f"❌ Failed to get status: {status_result['error']}")
    else:
        status = status_result.get("status", {})
        print(f"Current status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    # Activate NGN rail
    print(f"\n=== Activating NGN rail ===")
    print(f"Using sandbox BVN: 22222222222")
    
    activate_result = await bmoni_client.start_nigeria(
        bmoni_user_id=bmoni_user_id,
        bvn="22222222222",  # Sandbox test BVN
        wallet_address=wallet_address,
        wallet_index=0,
        phone_number=phone_number
    )

    if "error" in activate_result:
        print(f"❌ NGN activation failed: {activate_result['error']}")
        sys.exit(1)

    print(f"✅ NGN rail activation request submitted!")
    print(f"Response: {activate_result}")

    # Check status again
    print(f"\n=== Verifying activation ===")
    await asyncio.sleep(2)  # Wait a bit for activation to process
    
    status_result = await bmoni_client.get_wallet_status(bmoni_user_id)
    
    if "error" in status_result:
        print(f"❌ Failed to get status: {status_result['error']}")
    else:
        status = status_result.get("status", {})
        print(f"Updated status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    print(f"\n🎉 NGN rail activation complete for {phone_number}!")
    print(f"\nUser can now:")
    print(f"   - Receive money transfers from other users")
    print(f"   - Send money to other users")
    print(f"   - Get deposit account details to receive bank transfers")


if __name__ == "__main__":
    asyncio.run(main())
