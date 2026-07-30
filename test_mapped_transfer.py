"""
Test transfer with the NEW mapped phone setup

WhatsApp: +2348020812523 (mapped)
BMONI:    +2348134232353 (real account)
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
from bmoni_store import bmoni_store
from phone_mapper import get_bmoni_phone, get_mapping_info

WHATSAPP_PHONE = "+2348020812523"
RECIPIENT_PHONE = "+2348142392322"


async def main():
    print("="*70)
    print("TEST TRANSFER WITH MAPPED PHONE")
    print("="*70)
    
    # Step 1: Verify mapping
    print(f"\n📞 Step 1: Verifying phone mapping...")
    mapping = get_mapping_info(WHATSAPP_PHONE)
    if mapping:
        print(f"✅ Mapping found:")
        print(f"   WhatsApp: {mapping['whatsapp_phone']}")
        print(f"   BMONI: {mapping['bmoni_phone']}")
        print(f"   User ID: {mapping['bmoni_user_id']}")
    else:
        print(f"❌ No mapping found for {WHATSAPP_PHONE}")
        return
    
    bmoni_phone = mapping['bmoni_phone']
    bmoni_user_id = mapping['bmoni_user_id']
    
    # Step 2: Check account in database
    print(f"\n💾 Step 2: Checking database...")
    account = bmoni_store.get_by_phone(WHATSAPP_PHONE)  # Should use mapping
    if account:
        print(f"✅ Account found:")
        print(f"   BMONI User ID: {account.get('bmoni_user_id')}")
        wallet = account.get('wallet', {})
        print(f"   Wallet ID: {wallet.get('id')}")
        print(f"   Wallet Address: {wallet.get('address')}")
    else:
        print(f"❌ No account found")
        return
    
    wallet_id = account['wallet']['id']
    
    # Step 3: Check balance
    print(f"\n💰 Step 3: Checking balance...")
    balance_result = await bmoni_client.get_balance(bmoni_user_id)
    if balance_result.get("success"):
        balances = balance_result.get("balances", [])
        for bal in balances:
            currency = bal.get("currency")
            amount = bal.get("balance", 0)
            print(f"   {currency}: {amount}")
            
            if currency == "NGN" and float(amount) == 0:
                print("\n⚠️  NGN balance is 0. Need to fund this wallet first.")
                print(f"   You can deposit to this wallet or test with CNGN")
    
    # Step 4: Check recipient
    print(f"\n👤 Step 4: Checking recipient...")
    recipient_account = bmoni_store.get_by_phone(RECIPIENT_PHONE)
    if recipient_account:
        recipient_user_id = recipient_account.get('bmoni_user_id')
        print(f"✅ Recipient found: {recipient_user_id}")
    else:
        print(f"❌ Recipient not found")
        return
    
    # Step 5: Test transfer (small amount)
    print(f"\n💸 Step 5: Testing transfer of 1 CNGN...")
    print(f"   From: {WHATSAPP_PHONE} (mapped to {bmoni_phone})")
    print(f"   To: {RECIPIENT_PHONE}")
    
    result = await bmoni_client.execute_transfer(
        bmoni_user_id=bmoni_user_id,
        wallet_id=wallet_id,
        amount="1",
        currency="CNGN",
        to_user_id=recipient_user_id,
        description="Test transfer with phone mapping",
        poll_interval_seconds=2.0,
        poll_timeout_seconds=30.0
    )
    
    if "error" in result:
        print(f"\n❌ Transfer failed: {result['error']}")
        
        if "Signature does not match" in str(result.get('error')):
            print("\n❌ STILL GETTING SIGNATURE MISMATCH!")
            print("   This means the wallet-key pairing issue persists.")
        elif "does not have an active NGN account" in str(result.get('error')):
            print("\n⚠️  Recipient doesn't have NGN activated.")
            print("   Try with CNGN currency instead.")
    else:
        print(f"\n✅ TRANSFER SUCCESSFUL!")
        print(f"   Status: {result.get('status')}")
        print(f"   Proposal ID: {result.get('id')}")
        print("\n🎉 PHONE MAPPING WORKS!")
        print(f"   WhatsApp number {WHATSAPP_PHONE} successfully mapped")
        print(f"   to BMONI account {bmoni_phone}")


if __name__ == "__main__":
    asyncio.run(main())
