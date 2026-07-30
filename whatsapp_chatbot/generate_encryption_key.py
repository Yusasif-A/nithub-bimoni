#!/usr/bin/env python3
"""
Generate Fernet Encryption Key for Wallet Security
===================================================

Run this script to generate a secure encryption key for storing EVM private keys.

Usage:
    python generate_encryption_key.py

Then add the output to your .env file as WALLET_ENCRYPTION_KEY
"""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key().decode()
    print("\n" + "="*60)
    print("🔐 Generated Wallet Encryption Key")
    print("="*60)
    print(f"\nWALLET_ENCRYPTION_KEY={key}")
    print("\n" + "="*60)
    print("⚠️  IMPORTANT:")
    print("   1. Add this to your .env file")
    print("   2. Keep this key SECRET and SECURE")
    print("   3. Back it up in a safe location")
    print("   4. If lost, user wallets cannot be accessed")
    print("="*60 + "\n")
