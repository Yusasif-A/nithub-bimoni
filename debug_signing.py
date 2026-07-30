"""
Debug EIP-712 signing to find the issue
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
from key_vault import get_user_address, key_vault
from eth_account import Account
from eth_account.messages import encode_typed_data

BMONI_USER_ID = "411e7ddb-3e01-4293-8a52-de6132b53ada"
WALLET_ID = "85afb1e2-2733-4734-9631-a57943729a22"
RECIPIENT_USER_ID = "d87ba93a-13dc-454b-afab-7269e4d363c8"


async def main():
    print("="*70)
    print("DEBUG EIP-712 SIGNING")
    print("="*70)
    
    # Get owner address from key vault
    owner_address = get_user_address(BMONI_USER_ID)
    print(f"\n🔑 Owner address from key vault: {owner_address}")
    
    # Create a test proposal
    print(f"\n📝 Creating test proposal...")
    proposal_result = await bmoni_client.create_transfer_proposal(
        bmoni_user_id=BMONI_USER_ID,
        wallet_id=WALLET_ID,
        amount="1",
        currency="CNGN",
        to_user_id=RECIPIENT_USER_ID,
        description="Debug test"
    )
    
    if "error" in proposal_result:
        print(f"❌ Failed to create proposal: {proposal_result['error']}")
        return
    
    proposal = proposal_result.get("data", {}).get("proposal", proposal_result.get("proposal", proposal_result))
    proposal_id = proposal.get("id")
    print(f"✅ Proposal created: {proposal_id}")
    
    # Approve
    print(f"\n✅ Approving proposal...")
    await bmoni_client.approve_proposal(BMONI_USER_ID, proposal_id)
    
    # Get sign payload
    print(f"\n📋 Getting sign payload...")
    await asyncio.sleep(2)  # Wait for approval
    sign_payload = await bmoni_client.get_proposal_sign_payload(BMONI_USER_ID, proposal_id)
    
    if "error" in sign_payload:
        print(f"❌ Failed to get sign payload: {sign_payload['error']}")
        return
    
    typed_data = sign_payload.get("typedData", {})
    print(f"\n📄 Typed Data:")
    print(json.dumps(typed_data, indent=2))
    
    domain = typed_data.get("domain")
    types = typed_data.get("types")
    message = typed_data.get("message")
    
    print(f"\n🔍 Analysis:")
    print(f"   Domain keys: {list(domain.keys())}")
    print(f"   Types keys: {list(types.keys())}")
    print(f"   Message keys: {list(message.keys())}")
    
    # Check primaryType detection
    primary_type_auto = list(types.keys())[0] if types else None
    print(f"\n🎯 Primary Type Detection:")
    print(f"   Auto-detected (first key): {primary_type_auto}")
    
    # Check if there's an EIP712Domain in types
    if "EIP712Domain" in types:
        print(f"   ⚠️  Types contains EIP712Domain - this should be excluded!")
        types_without_domain = {k: v for k, v in types.items() if k != "EIP712Domain"}
        primary_type_fixed = list(types_without_domain.keys())[0] if types_without_domain else None
        print(f"   Corrected primary type: {primary_type_fixed}")
    
    # Try to sign with current implementation
    print(f"\n🔐 Testing current signing implementation...")
    try:
        signature = key_vault.sign_typed_data(BMONI_USER_ID, domain, types, message)
        print(f"✅ Signature generated: {signature[:20]}...")
        
        # Try to recover the signer
        structured_data = {
            "types": types,
            "primaryType": list(types.keys())[0],
            "domain": domain,
            "message": message
        }
        
        encoded_data = encode_typed_data(full_message=structured_data)
        
        # Get the private key to test recovery
        doc = key_vault.collection.find_one({"bmoni_user_id": BMONI_USER_ID})
        if doc:
            encrypted_key = doc["encrypted_private_key"]
            private_key = key_vault.fernet.decrypt(encrypted_key.encode()).decode()
            account = Account.from_key(private_key)
            
            print(f"\n🔍 Address verification:")
            print(f"   Expected (key vault): {account.address}")
            print(f"   Wallet owner: {owner_address}")
            
            if account.address.lower() != owner_address.lower():
                print(f"   ❌ MISMATCH IN KEY VAULT!")
            else:
                print(f"   ✅ Key vault address matches")
            
            # Try to recover from signature
            signed_message = account.sign_message(encoded_data)
            recovered_address = Account.recover_message(encoded_data, signature=signed_message.signature)
            print(f"   Recovered from sig: {recovered_address}")
            
            if recovered_address.lower() == account.address.lower():
                print(f"   ✅ Signature recovery works!")
            else:
                print(f"   ❌ Signature recovery failed!")
                
    except Exception as e:
        print(f"❌ Signing error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
