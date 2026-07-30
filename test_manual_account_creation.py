"""
Test manual account creation flow

This tests the new create_account tool that allows users to manually
create their account by providing all required information.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'whatsapp_chatbot'))

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from unified_agent import create_account
from bmoni_store import bmoni_store


async def test_manual_creation():
    """Test the manual account creation tool"""
    
    print("\n" + "="*70)
    print("MANUAL ACCOUNT CREATION TEST")
    print("="*70)
    
    # Test data
    test_phone = "+2348099887766"
    test_data = {
        "full_name": "Fatima Abubakar",
        "bvn": "22238719042",  # Sandbox BVN
        "date_of_birth": "20/05/1992",
        "city": "Abuja",
        "state": "FCT"
    }
    
    print(f"\nTest Phone: {test_phone}")
    print(f"Test Data: {test_data}")
    
    # Set global phone number (simulate tool context)
    from unified_agent import _current_phone_number, _current_user_name
    import unified_agent
    unified_agent._current_phone_number = test_phone
    unified_agent._current_user_name = test_data["full_name"]
    
    # Check if user already exists
    existing = bmoni_store.get_by_phone(test_phone)
    if existing:
        print(f"\n⚠️  User already exists in database")
        print(f"   BMONI User ID: {existing.get('bmoni_user_id')}")
        print(f"   Has Wallet: {existing.get('wallet') is not None}")
        
        response = input("\nDelete existing user and continue? (yes/no): ")
        if response.lower() != "yes":
            print("Test cancelled")
            return
        
        # Delete user from database
        bmoni_store.collection.delete_one({"phone": test_phone})
        print("✅ Deleted existing user")
    
    print(f"\n{'─'*70}")
    print("CALLING create_account TOOL")
    print(f"{'─'*70}")
    
    try:
        # Call the tool
        result = await create_account.ainvoke(test_data)
        
        print(f"\n{'─'*70}")
        print("TOOL RESULT:")
        print(f"{'─'*70}")
        print(result)
        
        # Check database
        print(f"\n{'─'*70}")
        print("DATABASE CHECK:")
        print(f"{'─'*70}")
        
        account = bmoni_store.get_by_phone(test_phone)
        if account:
            print(f"✅ Account found in database")
            print(f"   BMONI User ID: {account.get('bmoni_user_id')}")
            print(f"   Has Wallet: {account.get('wallet') is not None}")
            if account.get('wallet'):
                print(f"   Wallet ID: {account['wallet'].get('id')}")
                print(f"   Wallet Address: {account['wallet'].get('address')}")
            print(f"   KYC Status: {account.get('kyc_status')}")
            print(f"   Onboarding Status: {account.get('onboarding_status')}")
        else:
            print(f"❌ Account NOT found in database")
        
        print(f"\n{'='*70}")
        print("TEST COMPLETE")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_manual_creation())
