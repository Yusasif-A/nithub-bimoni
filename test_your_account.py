"""
Test your actual Opay account
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

from bank_account_resolver import verify_recipient_bank_account

BMONI_USER_ID = "411e7ddb-3e01-4293-8a52-de6132b53ada"
ACCOUNT = "2071718004"
BANK = "UBA"


async def main():
    print("="*70)
    print(f"VERIFYING YOUR OPAY ACCOUNT: {ACCOUNT}")
    print("="*70)
    
    result = await verify_recipient_bank_account(
        BMONI_USER_ID,
        ACCOUNT,
        BANK
    )
    
    if result.get("success"):
        print(f"\n✅ Account verified!")
        print(f"   Account Name: {result.get('account_name')}")
        print(f"   Account Number: {result.get('account_number')}")
        print(f"   Bank: {result.get('bank_name')}")
        print(f"   Bank Code: {result.get('bank_code')}")
    else:
        print(f"\n❌ Verification failed")
        print(f"   Error: {result.get('error')}")
        if result.get('candidates'):
            print(f"   Candidates: {result.get('candidates')}")


if __name__ == "__main__":
    asyncio.run(main())
