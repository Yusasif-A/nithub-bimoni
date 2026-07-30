"""
Test if transfer works for the RECIPIENT user (d87ba93a...) since their 
wallet was created at the same time as their key vault entry.

This will confirm if the signature mismatch is specific to the sender.
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
from key_vault import get_user_address


# Recipient user (who might have correct key-wallet pairing)
SENDER_USER_ID = "d87ba93a-13dc-454b-afab-7269e4d363c8"
SENDER_WALLET_ID = "7d5491fc-4055-4f7c-92f0-04ed58ba6a77"

# Send to the other user who has a wallet
RECIPIENT_USER_ID = "a1a2d2a5-8074-4e92-b515-0d755bbb8e72"


async def main():
    print("="*70)
    print("TEST TRANSFER FROM RECIPIENT USER")
    print("="*70)
    
    # Check key vault address
    print("\n🔐 Checking key vault...")
    sender_key = get_user_address(SENDER_USER_ID)
    print(f"Key vault address: {sender_key}")
    
    # Check balance
    print("\n💰 Checking balance...")
    balance_result = await bmoni_client.get_balance(SENDER_USER_ID)
    if balance_result.get("success"):
        balances = balance_result.get("balances", [])
        for bal in balances:
            currency = bal.get("currency")
            amount = bal.get("balance", 0)
            print(f"   {currency}: {amount}")
    
    # Try a small transfer
    print(f"\n💸 Attempting transfer of 1 CNGN...")
    print(f"   From: {SENDER_USER_ID}")
    print(f"   To: {RECIPIENT_USER_ID}")
    
    result = await bmoni_client.execute_transfer(
        bmoni_user_id=SENDER_USER_ID,
        wallet_id=SENDER_WALLET_ID,
        amount="1",
        currency="CNGN",
        to_user_id=RECIPIENT_USER_ID,
        description="Test transfer to verify signature",
        poll_interval_seconds=2.0,
        poll_timeout_seconds=30.0
    )
    
    if "error" in result:
        print(f"\n❌ Transfer failed: {result['error']}")
        
        if "Signature does not match" in str(result.get('error')):
            print("\n🔍 DIAGNOSIS:")
            print("   This user ALSO has signature mismatch!")
            print("   The wallet was likely created before the key vault entry.")
    else:
        print(f"\n✅ TRANSFER SUCCESSFUL!")
        print(f"   Status: {result.get('status')}")
        print(f"   Proposal ID: {result.get('id')}")
        print("\n🎉 This confirms:")
        print("   - The signature process works correctly")
        print("   - The sender's wallet just needs to be recreated with correct key")


if __name__ == "__main__":
    asyncio.run(main())
