"""
Standalone test for the send-money flow — bypasses the LLM agent and WhatsApp
entirely, so we can tell whether request_send_money / confirm_send_money /
execute_transfer actually work against BMONI before trusting the agent to
call them correctly.

Usage:
    python test_transfer.py <sender_phone> <recipient_phone> <amount>

Example:
    python test_transfer.py +2348020812523 +2348012345678 10

Run this from the same directory as bmoni_client.py, unified_agent.py,
key_vault.py, bmoni_store.py, and your .env file (same environment your app
runs in), so it can reach the same MongoDB and BMONI sandbox.
"""

import sys
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from bmoni_store import bmoni_store
from bmoni_client import request_send_money, confirm_send_money


def _normalize(phone: str) -> str:
    return phone if phone.startswith("+") else f"+{phone}"


async def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    sender_phone = _normalize(sys.argv[1])
    recipient_phone = _normalize(sys.argv[2])
    amount = float(sys.argv[3])

    print(f"\n=== Step 0: Look up sender's BMONI account ===")
    sender_account = bmoni_store.get_by_phone(sender_phone)
    if not sender_account:
        print(f"❌ No account found in bmoni_store for {sender_phone}. "
              f"Has this number ever messaged the bot / completed onboarding?")
        sys.exit(1)

    bmoni_user_id = sender_account.get("bmoni_user_id")
    wallet = sender_account.get("wallet")
    if not bmoni_user_id or not wallet:
        print(f"❌ Sender account exists but is missing bmoni_user_id or wallet: {sender_account}")
        sys.exit(1)

    wallet_id = wallet.get("id")
    print(f"✅ Sender bmoni_user_id: {bmoni_user_id}")
    print(f"✅ Sender wallet_id: {wallet_id}")

    print(f"\n=== Step 1: request_send_money (sends a confirmation code to {sender_phone} on WhatsApp) ===")
    result = await request_send_money(
        sender_phone=sender_phone,
        sender_bmoni_user_id=bmoni_user_id,
        sender_wallet_id=wallet_id,
        recipient_phone=recipient_phone,
        amount=amount,
    )
    print(f"Result: {result}")

    if not result.get("success"):
        print(f"\n❌ Stopped at step 1 — fix the error above before continuing.")
        sys.exit(1)

    print(f"\n=== Step 2: check WhatsApp on {sender_phone} for the confirmation code ===")
    code = input("Enter the confirmation code you received: ").strip()

    print(f"\n=== Step 3: confirm_send_money (runs the real BMONI proposal -> approve -> sign -> submit flow) ===")
    confirm_result = await confirm_send_money(sender_phone=sender_phone, code=code)
    print(f"Result: {confirm_result}")

    if confirm_result.get("success"):
        print(f"\n✅ Transfer succeeded: ₦{confirm_result['amount']:,.2f} to {confirm_result['recipient_phone']}")
    else:
        print(f"\n❌ Transfer failed: {confirm_result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())