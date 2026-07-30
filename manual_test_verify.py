"""
Manual test of account verification - bypassing agent completely
Test directly with BMONI API to confirm it works for hackathon demo
"""

import sys
import os
import asyncio
import logging
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_client import bmoni_client

# Use the new mapped user
BMONI_USER_ID = "411e7ddb-3e01-4293-8a52-de6132b53ada"

# Test with real Nigerian account numbers
TEST_CASES = [
    {"account": "1516131088", "bank": "Access Bank"},
    {"account": "1516131088", "bank": "Access"},
    {"account": "1516131088", "bank": "GTB"},  # Wrong bank - should fail
]


async def test_get_banks():
    """First, get the list of banks to confirm API works"""
    print("="*70)
    print("TEST 1: GET NIGERIAN BANKS LIST")
    print("="*70)
    
    result = await bmoni_client.get_nigerian_banks(BMONI_USER_ID)
    
    if "error" in result:
        print(f"❌ Failed to get banks: {result['error']}")
        return False
    
    banks = result.get("banks", result.get("data", []))
    print(f"\n✅ Retrieved {len(banks)} banks")
    
    # Show first 10
    print("\nFirst 10 banks:")
    for bank in banks[:10]:
        print(f"  • {bank.get('bankName')} (code: {bank.get('bankCode')})")
    
    # Check if Access Bank is in the list
    access_banks = [b for b in banks if "access" in b.get("bankName", "").lower()]
    if access_banks:
        print(f"\n✅ Found Access Bank(s):")
        for b in access_banks:
            print(f"  • {b.get('bankName')} (code: {b.get('bankCode')})")
    
    return True


async def test_verify_account(account_number: str, bank_code: str, bank_name: str):
    """Test account verification with specific bank code"""
    print(f"\n{'='*70}")
    print(f"VERIFY: {account_number} at {bank_name} (code: {bank_code})")
    print(f"{'='*70}")
    
    result = await bmoni_client.verify_nigerian_account(
        BMONI_USER_ID,
        account_number,
        bank_code
    )
    
    if "error" in result:
        print(f"❌ Verification failed: {result['error']}")
        return False
    
    account_name = result.get("accountName")
    if account_name:
        print(f"✅ Account verified!")
        print(f"   Account Name: {account_name}")
        print(f"   Account Number: {result.get('accountNumber')}")
        print(f"   Bank: {result.get('bankName')}")
        print(f"   Bank Code: {result.get('bankCode')}")
        return True
    else:
        print(f"❌ No account name returned")
        print(f"   Response: {result}")
        return False


async def test_with_resolver():
    """Test using the bank resolver (fuzzy matching)"""
    print(f"\n{'='*70}")
    print(f"TEST 2: VERIFY ACCOUNT WITH BANK RESOLVER")
    print(f"{'='*70}")
    
    from bank_account_resolver import verify_recipient_bank_account
    
    for test in TEST_CASES:
        account = test["account"]
        bank = test["bank"]
        
        print(f"\n🔍 Testing: {account} @ {bank}")
        
        try:
            result = await verify_recipient_bank_account(
                BMONI_USER_ID,
                account,
                bank
            )
            
            if result.get("success"):
                print(f"✅ SUCCESS!")
                print(f"   Name: {result.get('account_name')}")
                print(f"   Bank: {result.get('bank_name')}")
                print(f"   Code: {result.get('bank_code')}")
            else:
                print(f"❌ FAILED: {result.get('error')}")
                if result.get('candidates'):
                    print(f"   Candidates: {result.get('candidates')}")
        
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()


async def main():
    print("\n" + "="*70)
    print("MANUAL VERIFICATION TEST FOR HACKATHON")
    print("="*70)
    print(f"User ID: {BMONI_USER_ID}\n")
    
    # Test 1: Get banks list
    banks_ok = await test_get_banks()
    
    if not banks_ok:
        print("\n❌ Cannot proceed - banks API not working")
        return
    
    # Test 2: Verify with resolver
    await test_with_resolver()
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
