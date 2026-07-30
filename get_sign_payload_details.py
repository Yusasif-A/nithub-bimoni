"""
Check the sign payload to see what address BMONI expects

When we request the sign payload for a proposal, BMONI tells us what
data to sign. This payload should reveal what owner address it expects.
"""

import sys
import os
import asyncio
import httpx
import json
from dotenv import load_dotenv

# Load from whatsapp_chatbot/.env
env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

BMONI_API_URL = os.getenv("BMONI_BASE_URL", "https://embedded-dev.bmoni.com")
BMONI_API_KEY = os.getenv("BMONI_API_KEY")


async def create_test_proposal(bmoni_user_id: str, wallet_id: str):
    """Create a test transfer proposal"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    proposal_body = {
        "proposal": {
            "type": "TRANSFER",
            "toUserId": "d87ba93a-13dc-454b-afab-7269e4d363c8",  # Recipient
            "amount": "1",  # 1 Naira test
            "currency": "NGN"
        }
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{BMONI_API_URL}/v1/users/{bmoni_user_id}/smart-wallets/{wallet_id}/proposals",
            headers=headers,
            json=proposal_body
        )
        
        print(f"Create Proposal Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        
        if response.status_code == 201:
            data = response.json()
            # Extract proposal ID from different possible locations
            proposal = data.get("data", {}).get("proposal", data.get("proposal", data))
            proposal_id = proposal.get("id")
            return proposal_id
        return None


async def approve_proposal(bmoni_user_id: str, proposal_id: str):
    """Approve the proposal"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{BMONI_API_URL}/v1/users/{bmoni_user_id}/smart-wallets/proposals/{proposal_id}/approve",
            headers=headers
        )
        
        print(f"Approve Proposal Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        
        return response.status_code == 200


async def get_sign_payload(bmoni_user_id: str, proposal_id: str):
    """Get the signing payload - this should reveal the expected owner address"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{BMONI_API_URL}/v1/users/{bmoni_user_id}/smart-wallets/proposals/{proposal_id}/sign-payload",
            headers=headers
        )
        
        print(f"Get Sign Payload Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}\n")
            
            # Extract typed data
            typed_data = data.get("typedData", {})
            
            print("="*60)
            print("IMPORTANT ADDRESSES IN SIGN PAYLOAD:")
            print("="*60)
            
            # Check domain
            domain = typed_data.get("domain", {})
            print(f"\nDomain:")
            print(f"  verifyingContract: {domain.get('verifyingContract')}")
            print(f"  chainId: {domain.get('chainId')}")
            
            # Check message
            message = typed_data.get("message", {})
            print(f"\nMessage:")
            for key, value in message.items():
                print(f"  {key}: {value}")
            
            # Check types
            types = typed_data.get("types", {})
            print(f"\nTypes: {list(types.keys())}")
            print(f"Primary Type: {list(types.keys())[0] if types else 'None'}")
            
            print("\n" + "="*60)
            print("KEY VAULT ADDRESS (what we're signing with):")
            print("0x0E5372f3239A9A56dECC758E35164683468d67d8")
            print("="*60)
            
            return data
        else:
            print(f"Response: {response.text}\n")
            return None


async def main():
    if not BMONI_API_KEY:
        print("❌ BMONI_API_KEY not set")
        sys.exit(1)
    
    bmoni_user_id = "a348e005-bc63-4809-99c8-5ebb9a3aae5b"
    wallet_id = "6f10df23-5174-47cc-b7b0-f0a81f6f5e56"
    
    print("Creating test transfer proposal...\n")
    proposal_id = await create_test_proposal(bmoni_user_id, wallet_id)
    
    if not proposal_id:
        print("❌ Failed to create proposal")
        sys.exit(1)
    
    print(f"✅ Proposal created: {proposal_id}\n")
    
    print("Approving proposal...\n")
    approved = await approve_proposal(bmoni_user_id, proposal_id)
    
    if not approved:
        print("❌ Failed to approve proposal")
        sys.exit(1)
    
    print("✅ Proposal approved\n")
    
    # Wait a moment for BMONI to process
    await asyncio.sleep(2)
    
    print("Getting sign payload...\n")
    await get_sign_payload(bmoni_user_id, proposal_id)


if __name__ == "__main__":
    asyncio.run(main())
