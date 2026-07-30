"""
Standalone test for the send-money flow — bypasses the LLM agent and WhatsApp
entirely, so we can tell whether the send_money tool actually works against 
BMONI before trusting the agent to call it correctly.

Usage:
    python test_transfer.py <sender_phone> <recipient_phone> <amount>

Example:
    python test_transfer.py +2348020812523 +23467048439 10

Run this from the nithub-bimoni directory (parent of whatsapp_chatbot).
"""

import sys
import os
import asyncio
import logging

# Add whatsapp_chatbot to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "whatsapp_chatbot"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_store import bmoni_store
from bmoni_client import bmoni_client


def _normalize(phone: str) -> str:
    return phone if phone.startswith("+") else f"+{phone}"


async def main():
    if len(sys.argv) != 4:
        print(__doc__)
        print("\nExample: python test_transfer.py +2348020812523 +23467048439 10")
        sys.exit(1)

    sender_phone = _normalize(sys.argv[1])
    recipient_phone = _normalize(sys.argv[2])
    amount = float(sys.argv[3])

    print(f"\n=== Testing Money Transfer ===")
    print(f"From: {sender_phone}")
    print(f"To: {recipient_phone}")
    print(f"Amount: ₦{amount:,.2f}")

    print(f"\n=== Step 1: Look up sender's BMONI account ===")
    sender_account = bmoni_store.get_by_phone(sender_phone)
    if not sender_account:
        print(f"❌ No account found in bmoni_store for {sender_phone}")
        print(f"Has this number completed onboarding in the WhatsApp bot?")
        sys.exit(1)

    sender_user_id = sender_account.get("bmoni_user_id")
    sender_wallet = sender_account.get("wallet")
    
    if not sender_user_id:
        print(f"❌ Sender account missing bmoni_user_id: {sender_account}")
        sys.exit(1)
    
    if not sender_wallet:
        print(f"❌ Sender account missing wallet: {sender_account}")
        print(f"User needs to complete wallet creation first")
        sys.exit(1)

    print(f"✅ Sender bmoni_user_id: {sender_user_id}")
    print(f"✅ Sender wallet_id: {sender_wallet.get('id')}")

    print(f"\n=== Step 2: Look up recipient's BMONI account ===")
    recipient_account = bmoni_store.get_by_phone(recipient_phone)
    if not recipient_account:
        print(f"❌ No account found for recipient {recipient_phone}")
        print(f"Recipient needs to sign up for SabiSpend first")
        sys.exit(1)

    recipient_user_id = recipient_account.get("bmoni_user_id")
    if not recipient_user_id:
        print(f"❌ Recipient account missing bmoni_user_id")
        sys.exit(1)

    print(f"✅ Recipient bmoni_user_id: {recipient_user_id}")

    print(f"\n=== Step 3: Check sender's balance ===")
    balance_result = await bmoni_client.get_balance(sender_user_id)
    if "error" in balance_result:
        print(f"❌ Failed to get balance: {balance_result['error']}")
        sys.exit(1)
    
    balances = balance_result.get("balances", [])
    sender_balance = 0
    for bal in balances:
        if bal.get("currency") in ["CNGN", "NGN"]:
            sender_balance = float(bal.get("balance", 0))
            break
    
    print(f"✅ Sender balance: ₦{sender_balance:,.2f}")
    
    if sender_balance < amount:
        print(f"❌ Insufficient balance! Need ₦{amount:,.2f} but only have ₦{sender_balance:,.2f}")
        sys.exit(1)

    print(f"\n=== Step 4: Create transfer proposal ===")
    # Check if recipient has a wallet
    recipient_wallet = recipient_account.get("wallet")
    if not recipient_wallet:
        print(f"❌ Recipient doesn't have a wallet yet")
        sys.exit(1)
    
    sender_wallet_id = sender_wallet.get("id")
    
    # Step 4.1: Create the transfer proposal
    proposal_result = await bmoni_client._request(
        "POST",
        f"/v1/users/{sender_user_id}/smart-wallets/{sender_wallet_id}/proposals",
        json={
            "proposal": {
                "type": "TRANSFER",
                "toUserId": recipient_user_id,
                "amount": str(amount),
                "currency": "CNGN",
                "description": "SabiSpend transfer"
            }
        }
    )

    if "error" in proposal_result:
        print(f"❌ Proposal creation failed: {proposal_result.get('error')}")
        sys.exit(1)

    proposal_id = proposal_result.get("data", {}).get("proposal", {}).get("id")
    if not proposal_id:
        # Try alternative path
        proposal_id = proposal_result.get("proposal", {}).get("id")
    
    if not proposal_id:
        print(f"❌ No proposal ID in response: {proposal_result}")
        sys.exit(1)
    
    print(f"✅ Proposal created: {proposal_id}")
    
    print(f"\n=== Step 5: Approve the proposal ===")
    approve_result = await bmoni_client._request(
        "POST",
        f"/v1/users/{sender_user_id}/smart-wallets/proposals/{proposal_id}/approve",
        json={}
    )
    
    if "error" in approve_result:
        print(f"❌ Approval failed: {approve_result.get('error')}")
        sys.exit(1)
    
    print(f"✅ Proposal approved")
    
    print(f"\n=== Step 6: Get signing payload ===")
    # Poll for the sign payload (may need to wait for PENDING_SIGNATURES status)
    import time
    max_retries = 5
    sign_payload = None
    
    for i in range(max_retries):
        payload_result = await bmoni_client._request(
            "GET",
            f"/v1/users/{sender_user_id}/smart-wallets/proposals/{proposal_id}/sign-payload"
        )
        
        if "error" not in payload_result:
            sign_payload = payload_result
            break
        
        if i < max_retries - 1:
            print(f"Waiting for proposal to reach PENDING_SIGNATURES... (attempt {i+1}/{max_retries})")
            time.sleep(2)
    
    if not sign_payload or "error" in payload_result:
        print(f"❌ Could not get sign payload: {payload_result.get('error')}")
        sys.exit(1)
    
    print(f"✅ Sign payload received")
    
    print(f"\n=== Step 7: Sign the proposal ===")
    # Import the key_vault for signing
    from key_vault import sign_owner_proof
    
    typed_data = sign_payload.get("typedData")
    if not typed_data:
        print(f"❌ No typedData in payload")
        sys.exit(1)
    
    # Sign the typed data
    import json as json_lib
    message_to_sign = json_lib.dumps(typed_data, separators=(',', ':'))
    signature = sign_owner_proof(sender_user_id, message_to_sign)
    
    if not signature:
        print(f"❌ Failed to generate signature")
        sys.exit(1)
    
    print(f"✅ Signature generated")
    
    print(f"\n=== Step 8: Submit the signed proposal ===")
    submit_result = await bmoni_client._request(
        "POST",
        f"/v1/users/{sender_user_id}/smart-wallets/proposals/{proposal_id}/sign",
        json={"signature": signature}
    )
    
    if "error" in submit_result:
        print(f"❌ Submit failed: {submit_result.get('error')}")
        sys.exit(1)
    
    print(f"✅ Transfer submitted!")
    
    # Poll for final status
    print(f"\n=== Step 9: Check final status ===")
    for i in range(10):
        status_result = await bmoni_client._request(
            "GET",
            f"/v1/users/{sender_user_id}/smart-wallets/proposals/{proposal_id}"
        )
        
        if "error" in status_result:
            print(f"❌ Status check failed: {status_result.get('error')}")
            break
        
        status = status_result.get("data", {}).get("proposal", {}).get("status")
        print(f"Status: {status}")
        
        if status in ["EXECUTED", "FAILED", "REJECTED"]:
            break
        
        time.sleep(2)
    
    result = status_result

    if "error" in result:
        print(f"❌ Transfer failed: {result.get('error')}")
        print(f"Status code: {result.get('status_code')}")
        sys.exit(1)

    print(f"\n✅ Transfer successful!")
    print(f"Result: {result}")
    print(f"\nTransferred ₦{amount:,.2f} from {sender_phone} to {recipient_phone}")


if __name__ == "__main__":
    asyncio.run(main())