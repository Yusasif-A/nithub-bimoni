"""
Complete KYC and activate NGN for a user

This script completes the full onboarding flow:
1. Complete KYC with test data
2. Activate KYC
3. Start Nigeria onboarding with BVN
4. Verify activation

Usage:
    python complete_kyc_and_activate_ngn.py <phone_number> <bvn>

Example:
    python complete_kyc_and_activate_ngn.py +2348142392322 22238719042
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
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    phone_number = _normalize(sys.argv[1])
    bvn = sys.argv[2]

    print(f"\n=== Completing KYC and NGN Activation for {phone_number} ===\n")

    # Get user from database
    account = bmoni_store.get_by_phone(phone_number)
    if not account:
        print(f"❌ No account found for {phone_number}")
        sys.exit(1)

    bmoni_user_id = account.get("bmoni_user_id")
    if not bmoni_user_id:
        print(f"❌ Account missing bmoni_user_id")
        sys.exit(1)

    wallet = account.get("wallet")
    if not wallet:
        print(f"❌ User doesn't have a wallet yet")
        sys.exit(1)

    wallet_address = wallet.get("address")
    if not wallet_address:
        print(f"❌ Wallet missing address")
        sys.exit(1)

    print(f"✅ BMONI User ID: {bmoni_user_id}")
    print(f"✅ Wallet Address: {wallet_address}")
    print(f"✅ BVN: {bvn}")

    # Step 1: Check KYC options
    print(f"\n=== Step 1: Checking KYC options ===")
    kyc_options = await bmoni_client.get_kyc_options(bmoni_user_id)
    if "error" in kyc_options:
        print(f"❌ Failed to get KYC options: {kyc_options['error']}")
    else:
        print(f"✅ KYC options retrieved")

    # Step 2: Submit KYC data (sandbox test values)
    print(f"\n=== Step 2: Submitting KYC data ===")
    kyc_payload = {
        "bvn": bvn,
        "address": {
            "line1": "123 Market Street",
            "city": "Lagos",
            "state": "Lagos",
            "postalCode": "100001",
            "country": "NGA"
        },
        "occupation": "Trader",
        "dateOfBirth": "1990-01-01"
    }
    
    kyc_result = await bmoni_client.update_kyc(bmoni_user_id, kyc_payload, phone_number)
    if "error" in kyc_result:
        print(f"❌ KYC submission failed: {kyc_result['error']}")
        print(f"   This might be okay if KYC was already submitted")
    else:
        print(f"✅ KYC data submitted")

    # Step 3: Check KYC readiness
    print(f"\n=== Step 3: Checking KYC readiness ===")
    readiness = await bmoni_client.get_kyc_readiness(bmoni_user_id)
    if "error" in readiness:
        print(f"⚠️ Could not check readiness: {readiness['error']}")
    else:
        print(f"✅ KYC readiness: {readiness}")

    # Step 4: Activate KYC (no sumsubLevelName for Nigeria)
    print(f"\n=== Step 4: Activating KYC ===")
    activate_result = await bmoni_client.activate_kyc(bmoni_user_id, phone_number)
    if "error" in activate_result:
        print(f"⚠️ KYC activation: {activate_result['error']}")
        print(f"   This might be okay if already activated")
    else:
        print(f"✅ KYC activated")

    # Step 5: Start Nigeria onboarding
    print(f"\n=== Step 5: Starting Nigeria onboarding ===")
    nigeria_result = await bmoni_client.start_nigeria(
        bmoni_user_id=bmoni_user_id,
        bvn=bvn,
        wallet_address=wallet_address,
        wallet_index=0,
        phone_number=phone_number
    )

    if "error" in nigeria_result:
        print(f"❌ Nigeria onboarding failed: {nigeria_result['error']}")
        sys.exit(1)

    print(f"✅ Nigeria onboarding started")
    print(f"   Response: {nigeria_result}")

    # Step 6: Check onboarding status
    print(f"\n=== Step 6: Checking final onboarding status ===")
    await asyncio.sleep(3)  # Wait for activation to process
    
    status_result = await bmoni_client.get_wallet_status(bmoni_user_id)
    if "error" in status_result:
        print(f"❌ Failed to get status: {status_result['error']}")
    else:
        status = status_result.get("status", {})
        print(f"Final onboarding status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    # Step 7: Check wallet status via wallets endpoint
    print(f"\n=== Step 7: Checking wallet status ===")
    wallets_result = await bmoni_client.get_wallets(bmoni_user_id)
    
    if "error" not in wallets_result:
        if isinstance(wallets_result, list):
            wallets = wallets_result
        elif isinstance(wallets_result, dict):
            wallets = wallets_result.get("wallets", wallets_result.get("data", {}).get("wallets", []))
        else:
            wallets = []
        
        print(f"Wallet status:")
        for w in wallets:
            print(f"  Currency: {w.get('currency')}")
            print(f"  Status: {w.get('status')}")
            print(f"  Active: {w.get('status') == 'active'}")

    print(f"\n🎉 KYC and NGN activation process complete!")
    print(f"\nUser {phone_number} should now be able to:")
    print(f"   ✅ Receive NGN transfers")
    print(f"   ✅ Send NGN transfers")
    print(f"   ✅ Use full BMONI wallet features")


if __name__ == "__main__":
    asyncio.run(main())
