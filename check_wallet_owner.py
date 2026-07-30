"""
Check the actual owner address registered with BMONI for a wallet

This script fetches the wallet details from BMONI to see what owner address
is actually registered, so we can compare it with our key vault address.
"""

import sys
import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load from whatsapp_chatbot/.env
env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

BMONI_API_URL = os.getenv("BMONI_BASE_URL", "https://embedded-dev.bmoni.com")
BMONI_API_KEY = os.getenv("BMONI_API_KEY")


async def get_wallet_details(bmoni_user_id: str, wallet_id: str):
    """Get detailed wallet information from BMONI"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Try to get wallet details
        response = await client.get(
            f"{BMONI_API_URL}/v1/users/{bmoni_user_id}/smart-wallets/{wallet_id}",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== Wallet Details ===")
            print(f"Wallet ID: {data.get('id')}")
            print(f"Wallet Address: {data.get('address')}")
            print(f"Owner Address: {data.get('userOwnerAddress')}")
            print(f"Currency: {data.get('currency')}")
            print(f"Status: {data.get('status')}")
            return data
        else:
            print(f"❌ Failed to get wallet details")
            return None


async def get_all_wallets(bmoni_user_id: str):
    """Get all wallets for user"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{BMONI_API_URL}/v1/users/{bmoni_user_id}/smart-wallets/account/wallets",
            headers=headers
        )
        
        print(f"All Wallets Status: {response.status_code}")
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, list):
            wallets = data
        elif isinstance(data, dict):
            wallets = data.get("wallets", data.get("data", {}).get("wallets", []))
        else:
            wallets = []
        
        print(f"\n=== All Wallets ({len(wallets)}) ===")
        for wallet in wallets:
            print(f"\nWallet ID: {wallet.get('id')}")
            print(f"Address: {wallet.get('address')}")
            print(f"Owner Address: {wallet.get('userOwnerAddress')}")
            print(f"Currency: {wallet.get('currency')}")
            print(f"Status: {wallet.get('status')}")
        
        return wallets


async def main():
    if not BMONI_API_KEY:
        print("❌ BMONI_API_KEY not set in .env")
        sys.exit(1)
    
    bmoni_user_id = "a348e005-bc63-4809-99c8-5ebb9a3aae5b"
    wallet_id = "6f10df23-5174-47cc-b7b0-f0a81f6f5e56"
    
    print(f"Checking wallet for user: {bmoni_user_id}\n")
    
    # Get all wallets first
    await get_all_wallets(bmoni_user_id)
    
    print("\n" + "="*50)
    print("Trying to get specific wallet details...")
    print("="*50 + "\n")
    
    # Try to get specific wallet
    await get_wallet_details(bmoni_user_id, wallet_id)
    
    print("\n" + "="*50)
    print("Key Vault Address (expected owner):")
    print("0x0E5372f3239A9A56dECC758E35164683468d67d8")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
