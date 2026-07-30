"""
Test to discover the correct name for sandbox BVN

This script tests different names with the sandbox BVN (22222222222)
to find which name BMONI expects for successful wallet operations.

The hypothesis: BMONI sandbox has a specific test name that matches the BVN.
"""

import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'whatsapp_chatbot'))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

from bmoni_client import bmoni_client
from key_vault import ensure_keypair_exists, get_user_address


# Sandbox BVN from BMONI docs
SANDBOX_BVN = "22222222222"

# Test phone number (unique for this test - use timestamp)
import time
TEST_PHONE = f"+234901{int(time.time()) % 10000000}"  # Unique phone each run


async def test_name_with_bvn(test_name: str):
    """
    Test creating a user with a specific name and see if it works with the sandbox BVN
    
    Args:
        test_name: Name to test
    
    Returns:
        Dict with success status and details
    """
    print(f"\n{'='*70}")
    print(f"TESTING NAME: {test_name}")
    print(f"{'='*70}")
    
    try:
        # Step 1: Create user
        print(f"\n1️⃣  Creating BMONI user with name: {test_name}")
        user_result = await bmoni_client.create_user(
            phone_number=TEST_PHONE,
            first_name=test_name
        )
        
        if "error" in user_result or not user_result.get("bmoniUserId"):
            print(f"❌ User creation failed: {user_result.get('error')}")
            return {"success": False, "stage": "user_creation", "error": user_result.get('error')}
        
        bmoni_user_id = user_result["bmoniUserId"]
        print(f"✅ User created: {bmoni_user_id}")
        
        # Step 2: Generate keypair
        print(f"\n2️⃣  Generating EVM keypair")
        ensure_keypair_exists(TEST_PHONE)
        owner_address = get_user_address(TEST_PHONE)
        print(f"✅ Owner address: {owner_address}")
        
        # Step 3: Get owner proof challenge
        print(f"\n3️⃣  Getting owner proof challenge")
        challenge_result = await bmoni_client.get_owner_proof_challenge(
            bmoni_user_id,
            currency="CNGN",
            user_owner_address=owner_address
        )
        
        if "error" in challenge_result:
            print(f"❌ Challenge failed: {challenge_result.get('error')}")
            return {"success": False, "stage": "challenge", "error": challenge_result.get('error')}
        
        challenge_id = challenge_result["id"]
        challenge_message = challenge_result["message"]
        print(f"✅ Challenge received: {challenge_id}")
        
        # Step 4: Sign challenge
        print(f"\n4️⃣  Signing owner proof challenge")
        from key_vault import sign_owner_proof
        signature = sign_owner_proof(TEST_PHONE, challenge_message)
        print(f"✅ Signature: {signature[:20]}...")
        
        # Step 5: Create wallet
        print(f"\n5️⃣  Creating managed wallet")
        wallet_result = await bmoni_client.create_managed_wallet(
            bmoni_user_id=bmoni_user_id,
            currency="CNGN",
            user_owner_address=owner_address,
            challenge_id=challenge_id,
            signature=signature
        )
        
        if "error" in wallet_result:
            print(f"❌ Wallet creation failed: {wallet_result.get('error')}")
            return {"success": False, "stage": "wallet_creation", "error": wallet_result.get('error')}
        
        wallet_id = wallet_result.get("id")
        wallet_address = wallet_result.get("address")
        print(f"✅ Wallet created!")
        print(f"   Wallet ID: {wallet_id}")
        print(f"   Wallet Address: {wallet_address}")
        
        # Step 6: Submit KYC with sandbox BVN
        print(f"\n6️⃣  Submitting KYC with sandbox BVN: {SANDBOX_BVN}")
        kyc_payload = {
            "address": {
                "line1": "123 Test Street",
                "city": "Lagos",
                "state": "Lagos",
                "postalCode": "100001",
                "country": "NGA"
            },
            "occupation": "Trader",
            "dateOfBirth": "1990-01-01"
        }
        
        kyc_result = await bmoni_client.update_kyc(bmoni_user_id, kyc_payload, TEST_PHONE)
        
        if "error" in kyc_result:
            print(f"⚠️  KYC submission: {kyc_result.get('error')}")
        else:
            print(f"✅ KYC submitted")
        
        # Step 7: Activate KYC
        print(f"\n7️⃣  Activating KYC")
        activate_result = await bmoni_client.activate_kyc(bmoni_user_id, TEST_PHONE)
        
        if "error" in activate_result:
            print(f"⚠️  KYC activation: {activate_result.get('error')}")
        else:
            print(f"✅ KYC activated")
        
        # Step 8: Activate NGN rail with sandbox BVN
        print(f"\n8️⃣  Activating NGN rail with BVN: {SANDBOX_BVN}")
        nigeria_result = await bmoni_client.start_nigeria(
            bmoni_user_id=bmoni_user_id,
            bvn=SANDBOX_BVN,
            wallet_address=wallet_address,
            wallet_index=0,
            phone_number=TEST_PHONE
        )
        
        if "error" in nigeria_result:
            print(f"❌ NGN activation failed: {nigeria_result.get('error')}")
            print(f"   This is the KEY TEST - if this fails, the name doesn't match the BVN!")
            return {
                "success": False,
                "stage": "ngn_activation",
                "error": nigeria_result.get('error'),
                "bmoni_user_id": bmoni_user_id,
                "wallet_id": wallet_id
            }
        
        print(f"✅ NGN ACTIVATION SUCCESSFUL!")
        print(f"   Response: {nigeria_result}")
        
        return {
            "success": True,
            "bmoni_user_id": bmoni_user_id,
            "wallet_id": wallet_id,
            "wallet_address": wallet_address,
            "message": f"SUCCESS! Name '{test_name}' works with sandbox BVN {SANDBOX_BVN}"
        }
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "stage": "exception", "error": str(e)}


async def main():
    """Test different names to find the one that matches sandbox BVN"""
    
    print("\n" + "="*70)
    print("SANDBOX BVN NAME DISCOVERY TEST")
    print("="*70)
    print(f"Sandbox BVN: {SANDBOX_BVN}")
    print(f"Test Phone: {TEST_PHONE}")
    print("="*70)
    
    # List of names to test (common sandbox test names)
    test_names = [
        "Test User",
        "Sandbox User",
        "Demo User",
        "John Doe",
        "Test Account",
        "BMONI Test",
        "Nigeria Test",
        "Sample User",
    ]
    
    print(f"\nWill test {len(test_names)} different names...")
    input("\nPress ENTER to start testing (or Ctrl+C to cancel): ")
    
    results = []
    
    for i, name in enumerate(test_names, 1):
        print(f"\n\n{'#'*70}")
        print(f"TEST {i}/{len(test_names)}")
        print(f"{'#'*70}")
        
        result = await test_name_with_bvn(name)
        results.append({"name": name, **result})
        
        if result["success"]:
            print(f"\n🎉🎉🎉 FOUND IT! 🎉🎉🎉")
            print(f"The sandbox BVN {SANDBOX_BVN} matches the name: {name}")
            break
        else:
            print(f"\n❌ Name '{name}' did not work")
            print(f"   Failed at stage: {result.get('stage')}")
            print(f"   Error: {result.get('error')}")
        
        # Wait a bit between tests to avoid rate limiting
        if i < len(test_names):
            print(f"\nWaiting 3 seconds before next test...")
            await asyncio.sleep(3)
    
    # Summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    successful = [r for r in results if r["success"]]
    
    if successful:
        print(f"\n✅ SUCCESSFUL NAME FOUND:")
        for r in successful:
            print(f"   Name: {r['name']}")
            print(f"   BMONI User ID: {r['bmoni_user_id']}")
            print(f"   Wallet ID: {r['wallet_id']}")
    else:
        print(f"\n❌ No successful names found")
        print(f"\nFailed tests:")
        for r in results:
            print(f"   - {r['name']}: {r.get('stage')} - {r.get('error')}")
    
    print(f"\n{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
