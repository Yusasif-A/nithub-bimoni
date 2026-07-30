"""
Test account verification manually
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

from bank_account_resolver import verify_recipient_bank_account
from bmoni_store import bmoni_store

WHATSAPP_PHONE = "+2348020812523"
ACCOUNT_NUMBER = "1516131088"
BANK_NAME = "Access"


async def main():
    print("="*70)
    print("TEST ACCOUNT VERIFICATION")
    print("="*70)
    
    # Get user info
    print(f"\n📞 Looking up user: {WHATSAPP_PHONE}")
    account = bmoni_store.get_by_phone(WHATSAPP_PHONE)
    
    if not account:
        print(f"❌ No account found for {WHATSAPP_PHONE}")
        return
    
    bmoni_user_id = account.get("bmoni_user_id")
    if not bmoni_user_id:
        print(f"❌ No BMONI user ID")
        return
    
    print(f"✅ BMONI User ID: {bmoni_user_id}")
    
    # Test verification
    print(f"\n🔍 Verifying account:")
    print(f"   Account: {ACCOUNT_NUMBER}")
    print(f"   Bank: {BANK_NAME}")
    
    try:
        result = await verify_recipient_bank_account(
            bmoni_user_id,
            ACCOUNT_NUMBER,
            BANK_NAME
        )
        
        print(f"\n📋 Result:")
        print(f"   Success: {result.get('success')}")
        
        if result.get("success"):
            print(f"   Account Name: {result.get('account_name')}")
            print(f"   Bank Name: {result.get('bank_name')}")
            print(f"   Account Number: {result.get('account_number')}")
            print(f"   Bank Code: {result.get('bank_code')}")
        else:
            print(f"   Error: {result.get('error')}")
            if result.get('candidates'):
                print(f"   Candidates: {result.get('candidates')}")
        
    except Exception as e:
        print(f"\n❌ Exception occurred:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
