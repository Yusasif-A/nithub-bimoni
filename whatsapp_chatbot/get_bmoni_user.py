#!/usr/bin/env python3
"""
Try to get existing BMONI user info
====================================

BMONI API doesn't officially document a "get user by phone" endpoint,
but we can try common patterns.
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BMONI_API_URL = "https://embedded-dev.bmoni.com"
BMONI_API_KEY = os.getenv("BMONI_API_KEY")
PHONE = "+2348020812523"
EMAIL = "sabispend+2348020812523@example.com"


async def try_get_user():
    """Try different endpoints to get existing user info"""
    
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Trying to find existing BMONI account for {PHONE}...\n")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        
        # Try 1: GET /v1/users (might list all users)
        print("1️⃣ Trying GET /v1/users...")
        try:
            response = await client.get(f"{BMONI_API_URL}/v1/users", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Try 2: GET /v1/users with phone query param
        print("\n2️⃣ Trying GET /v1/users?phoneNumber={phone}...")
        try:
            response = await client.get(
                f"{BMONI_API_URL}/v1/users",
                headers=headers,
                params={"phoneNumber": PHONE}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Try 3: GET /v1/users with email query param
        print("\n3️⃣ Trying GET /v1/users?email={email}...")
        try:
            response = await client.get(
                f"{BMONI_API_URL}/v1/users",
                headers=headers,
                params={"email": EMAIL}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Try 4: POST with same details to see error message
        print("\n4️⃣ Trying POST /v1/users (to see conflict error details)...")
        try:
            response = await client.post(
                f"{BMONI_API_URL}/v1/users",
                headers=headers,
                json={
                    "firstName": "Test User",
                    "email": EMAIL,
                    "phoneNumber": PHONE
                }
            )
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Response: {data}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("📋 CONCLUSION:")
    print("="*60)
    print("If none of the above methods returned user details,")
    print("you need to:")
    print("1. Contact BMONI support to get user ID for this phone, OR")
    print("2. Ask them to delete the existing account, OR")
    print("3. Use a different phone number for testing")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(try_get_user())
