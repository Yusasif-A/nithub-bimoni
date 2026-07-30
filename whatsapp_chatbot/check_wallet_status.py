#!/usr/bin/env python3
"""
Check wallet status for a user
"""

from bmoni_store import bmoni_store

PHONE = "+2348020812523"

print(f"\n🔍 Checking wallet status for {PHONE}...\n")

account = bmoni_store.get_by_phone(PHONE)

if account:
    print("✅ Account found in database:")
    print(f"   Phone: {account.get('phone_number')}")
    print(f"   BMONI User ID: {account.get('bmoni_user_id')}")
    print(f"   Lifecycle Stage: {account.get('lifecycle_stage')}")
    
    if account.get('wallet'):
        wallet = account['wallet']
        print(f"\n💰 Wallet Info:")
        print(f"   Wallet ID: {wallet.get('id')}")
        print(f"   Wallet Address: {wallet.get('address')}")
        print(f"   Currency: {wallet.get('currency')}")
    else:
        print(f"\n⚠️  No wallet created yet")
    
    print("\n" + "="*60)
    if account.get('bmoni_user_id') and account.get('wallet'):
        print("📋 SEND TO BMONI TEAM FOR FUNDING:")
        print("="*60)
        print(f"Phone: {PHONE}")
        print(f"BMONI User ID: {account.get('bmoni_user_id')}")
        print(f"Wallet ID: {account['wallet'].get('id')}")
        print(f"Wallet Address: {account['wallet'].get('address')}")
        print("="*60)
else:
    print("❌ No account found in database")
    print(f"\nUser needs to tap language button to create account.")
