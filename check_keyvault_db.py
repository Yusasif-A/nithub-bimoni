"""
Check what's actually stored in the key vault database
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import json

# Load environment
env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ MONGO_URI not set")
    exit(1)

# Connect to MongoDB
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client.get_database("SabiSpend")

# Check evm_key_vault collection
key_vault_col = db.get_collection("evm_key_vault")

print("="*60)
print("EVM KEY VAULT - All Records")
print("="*60)

all_keys = list(key_vault_col.find({}))
print(f"\nFound {len(all_keys)} keypair(s) in vault:\n")

for record in all_keys:
    print(f"BMONI User ID: {record.get('bmoni_user_id')}")
    print(f"Ethereum Address: {record.get('ethereum_address')}")
    print(f"Has Encrypted Key: {'encrypted_private_key' in record}")
    print(f"Created/Updated: {record.get('_id').generation_time if '_id' in record else 'Unknown'}")
    print("-" * 60)

# Check the specific user
bmoni_user_id = "a348e005-bc63-4809-99c8-5ebb9a3aae5b"
user_key = key_vault_col.find_one({"bmoni_user_id": bmoni_user_id})

print("\n" + "="*60)
print(f"KEY FOR USER: {bmoni_user_id}")
print("="*60)

if user_key:
    print(f"✅ Found in vault:")
    print(f"   Address: {user_key.get('ethereum_address')}")
    print(f"   Has encrypted key: {'encrypted_private_key' in user_key}")
    print(f"   Record ID: {user_key.get('_id')}")
else:
    print(f"❌ No key found for this user")

# Check bmoni_accounts to see wallet address
accounts_col = db.get_collection("bmoni_accounts")
account = accounts_col.find_one({"phone_number": "+2348020812523"})

print("\n" + "="*60)
print("WALLET INFO FROM ACCOUNTS COLLECTION")
print("="*60)

if account:
    wallet = account.get("wallet", {})
    print(f"Smart Wallet ID: {wallet.get('id')}")
    print(f"Smart Wallet Address: {wallet.get('address')}")
    print(f"Currency: {wallet.get('currency')}")
    print(f"Created: {account.get('created_at')}")
    
    # Check if there's an owner address field
    if 'owner_address' in wallet:
        print(f"Owner Address (from DB): {wallet.get('owner_address')}")
else:
    print("❌ No account found")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Key Vault Address:    0x0E5372f3239A9A56dECC758E35164683468d67d8")
print(f"Smart Wallet Address: 0xE364b87F5Bd7ab2031c9BcA452F898CbEF1045F1")
print("\nThe key vault address should have been used as the 'owner' when")
print("creating the smart wallet on BMONI. If BMONI has a DIFFERENT owner")
print("address registered, that's the source of the signature mismatch.")

client.close()
