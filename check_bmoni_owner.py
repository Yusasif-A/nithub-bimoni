"""
Check what owner address BMONI actually has registered for the new wallet
"""

import sys
import os
import asyncio
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

from bmoni_client import bmoni_client
from key_vault import get_user_address

BMONI_USER_ID = "411e7ddb-3e01-4293-8a52-de6132b53ada"
WALLET_ID = "85afb1e2-2733-4734-9631-a57943729a22"


async def main():
    print("="*70)
    print("CHECK BMONI REGISTERED OWNER ADDRESS")
    print("="*70)
    
    # Get from key vault
    key_vault_address = get_user_address(BMONI_USER_ID)
    print(f"\n🔑 Key Vault Address: {key_vault_address}")
    
    # Get wallet details from BMONI
    print(f"\n📋 Fetching wallet from BMONI...")
    result = await bmoni_client._request("GET", f"/v1/users/{BMONI_USER_ID}/smart-wallets/{WALLET_ID}")
    
    print(f"\nFull response:")
    print(json.dumps(result, indent=2))
    
    # Check for owner address fields
    print(f"\n🔍 Looking for owner address...")
    
    if "userOwnerAddress" in result:
        bmoni_owner = result["userOwnerAddress"]
        print(f"✅ Found userOwnerAddress: {bmoni_owner}")
    else:
        print(f"❌ No userOwnerAddress in response")
        print(f"   Available fields: {list(result.keys())}")
    
    # Get all wallets to see if owner is there
    print(f"\n📋 Checking all wallets...")
    wallets_result = await bmoni_client.get_wallets(BMONI_USER_ID)
    
    if isinstance(wallets_result, list):
        wallets = wallets_result
    elif isinstance(wallets_result, dict):
        wallets = wallets_result.get("wallets", wallets_result.get("data", {}).get("wallets", []))
    else:
        wallets = []
    
    for wallet in wallets:
        print(f"\nWallet ID: {wallet.get('id')}")
        print(f"  Address: {wallet.get('walletAddress') or wallet.get('address')}")
        print(f"  Currency: {wallet.get('currency')}")
        
        if "userOwnerAddress" in wallet:
            print(f"  Owner: {wallet['userOwnerAddress']}")
        elif "ownerAddress" in wallet:
            print(f"  Owner: {wallet['ownerAddress']}")
        else:
            print(f"  Owner: Not found in response")
    
    # Try to get from owner-proof-challenges endpoint
    print(f"\n🔍 Checking owner-proof-challenges...")
    challenges_result = await bmoni_client._request(
        "GET",
        f"/v1/users/{BMONI_USER_ID}/smart-wallets/owner-proof-challenges"
    )
    
    if "error" not in challenges_result:
        print(json.dumps(challenges_result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
