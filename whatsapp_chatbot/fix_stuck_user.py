#!/usr/bin/env python3
"""
Fix stuck user account
======================

Removes the lock for a stuck user so they can try wallet creation again.
"""

from bmoni_store import bmoni_store

PHONE = "+2348020812523"

print(f"\n🔧 Fixing stuck account for {PHONE}...\n")

# Check current status
account = bmoni_store.get_by_phone(PHONE)

if account:
    print(f"Current status: {account.get('lifecycle_stage')}")
    print(f"BMONI User ID: {account.get('bmoni_user_id')}")
    
    if account.get('lifecycle_stage') == 'user_creation_pending' and not account.get('bmoni_user_id'):
        print("\n⚠️  User is stuck in 'user_creation_pending' with no bmoni_user_id")
        print("   Deleting this entry so wallet creation can be retried...\n")
        
        # Delete the stuck entry
        if bmoni_store.collection is not None:
            result = bmoni_store.collection.delete_one({"phone_number": PHONE})
            if result.deleted_count > 0:
                print(f"✅ Deleted stuck entry for {PHONE}")
                print(f"\n🎯 Now user can tap language button to create wallet fresh!")
            else:
                print(f"❌ Failed to delete entry")
    else:
        print("\n✅ Account looks OK (not stuck)")
else:
    print(f"❌ No account found for {PHONE}")

print()
