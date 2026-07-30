#!/usr/bin/env python3
"""
Test phone number normalization
"""

from bmoni_store import bmoni_store

# Test both formats
test_numbers = [
    "2348020812523",      # Without +
    "+2348020812523",     # With +
]

print("\n" + "="*60)
print("PHONE NUMBER NORMALIZATION TEST")
print("="*60)

for phone in test_numbers:
    print(f"\nTesting: {phone}")
    normalized = phone if phone.startswith("+") else f"+{phone}"
    print(f"Normalized: {normalized}")
    
    account = bmoni_store.get_by_phone(normalized)
    if account:
        print(f"✅ Found account:")
        print(f"   BMONI User ID: {account.get('bmoni_user_id')}")
        print(f"   Wallet: {account.get('wallet', {}).get('address', 'N/A')}")
    else:
        print(f"❌ No account found")

print("\n" + "="*60)
print("CONCLUSION:")
print("Both '2348020812523' and '+2348020812523' should find the same account")
print("="*60 + "\n")
