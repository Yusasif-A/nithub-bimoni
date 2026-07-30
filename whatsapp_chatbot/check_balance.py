#!/usr/bin/env python3
"""
Check BMONI wallet balance for a user
"""

import asyncio
import json
from bmoni_client import bmoni_client, get_user_balance_naira
from bmoni_store import bmoni_store

PHONE = "+2348020812523"

async def main():
    print(f"\n{'='*60}")
    print(f"CHECKING BALANCE FOR {PHONE}")
    print(f"{'='*60}\n")
    
    # Step 1: Get account from database
    print("Step 1: Looking up account in database...")
    account = bmoni_store.get_by_phone(PHONE)
    
    if not account:
        print(f"❌ No account found for {PHONE}")
        print("   User needs to complete onboarding first.")
        return
    
    bmoni_user_id = account.get("bmoni_user_id")
    wallet = account.get("wallet")
    
    print(f"✅ Account found:")
    print(f"   BMONI User ID: {bmoni_user_id}")
    print(f"   Wallet Address: {wallet.get('address') if wallet else 'N/A'}")
    print(f"   Wallet ID: {wallet.get('id') if wallet else 'N/A'}")
    
    if not bmoni_user_id:
        print(f"\n❌ No BMONI user ID found")
        return
    
    # Step 2: Get RAW balance from BMONI API
    print(f"\nStep 2: Checking balance from BMONI API...")
    try:
        result = await bmoni_client.get_balance(bmoni_user_id)
        
        if "error" in result:
            print(f"❌ API Error: {result['error']}")
            return
        
        print(f"\n📥 RAW API RESPONSE:")
        print(json.dumps(result, indent=2))
        
        # Step 3: Parse balance
        print(f"\nStep 3: Parsing balance...")
        balances = result.get("balances", [])
        
        if not balances:
            print("⚠️  No balances found in response")
            return
        
        total_naira = 0
        for bal in balances:
            currency = bal.get("currency")
            # Check both "balance" and "amount" fields
            amount_value = bal.get("balance") or bal.get("amount") or "0"
            amount = float(amount_value)
            
            print(f"   Currency: {currency}, Amount: {amount}")
            
            if currency in ["CNGN", "NGN", "cNGN"]:
                total_naira += amount
        
        print(f"\n{'='*60}")
        print(f"💰 WALLET BALANCE: ₦{total_naira:,.2f}")
        print(f"{'='*60}\n")
        
        if total_naira == 0:
            print("ℹ️  Note: Wallet shows 0 balance")
            print("   Check if BMONI team funded the correct wallet address")
        else:
            print(f"✅ Wallet has been funded with ₦{total_naira:,.2f}!")
            
    except Exception as e:
        print(f"\n❌ Failed to check balance: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
