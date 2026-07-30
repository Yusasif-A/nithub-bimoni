"""
Manual test for bank account verification - DEBUG MODE
Shows full response details to diagnose the issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'whatsapp_chatbot'))

import asyncio
import logging
from bmoni_client import bmoni_client
from bank_account_resolver import verify_recipient_bank_account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_verification():
    """Test account verification with detailed debugging"""
    
    # Use the mapped user's BMONI ID
    bmoni_user_id = "411e7ddb-3e01-4293-8a52-de6132b53ada"
    
    print("\n" + "="*70)
    print("BANK ACCOUNT VERIFICATION TEST - DEBUG MODE")
    print("="*70)
    
    # Test cases from user's messages
    test_cases = [
        ("0123456789", "Access", "User's Access Bank account"),
        ("8020812523", "Opay", "User's Opay account"),
        ("2071718004", "UBA", "User's UBA account (testing on different phone)"),
    ]
    
    for account_num, bank, description in test_cases:
        print(f"\n{'─'*70}")
        print(f"TEST: {description}")
        print(f"Account: {account_num}")
        print(f"Bank: {bank}")
        print(f"{'─'*70}")
        
        try:
            # First, resolve bank name to code
            from bank_account_resolver import resolve_bank_code
            
            print(f"\n1️⃣  Resolving bank name '{bank}' to bank code...")
            resolution = await resolve_bank_code(bmoni_user_id, bank)
            
            if not resolution.get("resolved"):
                print(f"❌ Bank resolution failed: {resolution}")
                continue
            
            bank_code = resolution["bank_code"]
            bank_name = resolution["bank_name"]
            print(f"✅ Resolved: {bank_name} (code: {bank_code})")
            
            # Now verify the account
            print(f"\n2️⃣  Verifying account with BMONI API...")
            print(f"    POST /v1/users/{bmoni_user_id}/bank-accounts/verify-nigerian-account")
            print(f"    Body: {{'accountNumber': '{account_num}', 'bankCode': '{bank_code}'}}")
            
            raw_result = await bmoni_client.verify_nigerian_account(
                bmoni_user_id,
                account_num,
                bank_code
            )
            
            print(f"\n3️⃣  BMONI API Response:")
            print(f"    {raw_result}")
            
            # Check for error
            if "error" in raw_result:
                print(f"\n❌ VERIFICATION FAILED")
                print(f"    Error: {raw_result['error']}")
                print(f"    Status: {raw_result.get('status_code', 'unknown')}")
            else:
                # Success - extract account name
                account_name = raw_result.get("accountName")
                if account_name:
                    print(f"\n✅ VERIFICATION SUCCESSFUL")
                    print(f"    Account Name: {account_name}")
                    print(f"    Bank: {bank_name}")
                    print(f"    Account: {account_num}")
                else:
                    print(f"\n⚠️  UNEXPECTED RESPONSE")
                    print(f"    No 'accountName' field in response")
                    print(f"    Response: {raw_result}")
        
        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_verification())
