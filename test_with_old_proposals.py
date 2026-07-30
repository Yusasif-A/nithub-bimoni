"""
Check old proposals to see if they contain owner address information
"""

import sys
import os
import asyncio
import httpx
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

BMONI_API_URL = os.getenv("BMONI_BASE_URL")
BMONI_API_KEY = os.getenv("BMONI_API_KEY")


async def get_all_proposals(bmoni_user_id: str):
    """Get all proposals for the user"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{BMONI_API_URL}/v1/users/{bmoni_user_id}/smart-wallets/proposals",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"\nRaw response:\n{json.dumps(data, indent=2)}\n")
            
            # Parse proposals
            proposals = data.get("proposals", data.get("data", {}).get("proposals", []))
            
            print(f"Found {len(proposals)} proposals:\n")
            for prop in proposals[:5]:  # Show first 5
                print(f"Proposal ID: {prop.get('id')}")
                print(f"  Type: {prop.get('type')}")
                print(f"  Status: {prop.get('status')}")
                print(f"  Amount: {prop.get('amount')} {prop.get('currency')}")
                print(f"  Created: {prop.get('createdAt')}")
                
                # Check if there's any owner address info
                if 'signer' in prop:
                    print(f"  Signer: {prop.get('signer')}")
                if 'signature' in prop:
                    print(f"  Has signature: True")
                print()
            
            return proposals
        else:
            print(f"Error: {response.text}")
            return []


async def get_specific_proposal(bmoni_user_id: str, proposal_id: str):
    """Get detailed info for a specific proposal"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{BMONI_API_URL}/v1/users/{bmoni_user_id}/smart-wallets/proposals/{proposal_id}",
            headers=headers
        )
        
        print(f"\nDetailed Proposal {proposal_id}:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(response.text)


async def main():
    bmoni_user_id = "a348e005-bc63-4809-99c8-5ebb9a3aae5b"
    
    print("="*60)
    print("Checking all proposals for user")
    print("="*60)
    
    proposals = await get_all_proposals(bmoni_user_id)
    
    # If there are recent failed proposals, check the details
    if proposals:
        recent_failed = [p for p in proposals if p.get('status') != 'COMPLETED']
        if recent_failed:
            print("\n" + "="*60)
            print("Checking failed proposal details...")
            print("="*60)
            await get_specific_proposal(bmoni_user_id, recent_failed[0].get('id'))


if __name__ == "__main__":
    asyncio.run(main())
