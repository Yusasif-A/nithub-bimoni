"""
List all wallets for the user and check owner addresses
"""

import sys
import os
import asyncio
import json
from dotenv import load_dotenv
import httpx

env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

BMONI_API_URL = os.getenv("BMONI_BASE_URL")
BMONI_API_KEY = os.getenv("BMONI_API_KEY")
BMONI_USER_ID = "411e7ddb-3e01-4293-8a52-de6132b53ada"


async def main():
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    print("="*70)
    print("LIST ALL WALLETS FOR USER")
    print("="*70)
    print(f"\nUser ID: {BMONI_USER_ID}\n")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Get all wallets
        response = await client.get(
            f"{BMONI_API_URL}/v1/users/{BMONI_USER_ID}/smart-wallets/account/wallets",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"\nRaw response:")
        print(json.dumps(data, indent=2))
        
        # Parse wallets
        if isinstance(data, list):
            wallets = data
        elif isinstance(data, dict):
            wallets = data.get("wallets", data.get("data", {}).get("wallets", []))
        else:
            wallets = []
        
        print(f"\n{'='*70}")
        print(f"FOUND {len(wallets)} WALLET(S)")
        print(f"{'='*70}\n")
        
        for idx, wallet in enumerate(wallets, 1):
            print(f"Wallet #{idx}:")
            print(f"  ID: {wallet.get('id')}")
            print(f"  Address: {wallet.get('walletAddress') or wallet.get('address')}")
            print(f"  Currency: {wallet.get('currency')}")
            print(f"  Status: {wallet.get('status') or 'Active' if wallet.get('isActive') else 'Inactive'}")
            print(f"  Chain: {wallet.get('chainName') or wallet.get('chain') or 'base'}")
            
            # Check for owner
            owner = (wallet.get('userOwnerAddress') or 
                    wallet.get('ownerAddress') or 
                    wallet.get('owner'))
            
            if owner:
                print(f"  Owner: {owner}")
            else:
                print(f"  Owner: ❌ Not found in response")
            
            print()


if __name__ == "__main__":
    asyncio.run(main())
