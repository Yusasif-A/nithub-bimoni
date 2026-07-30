"""
Test BMONI API access
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "whatsapp_chatbot", ".env")
load_dotenv(env_path)

BMONI_API_URL = os.getenv("BMONI_BASE_URL")
BMONI_API_KEY = os.getenv("BMONI_API_KEY")


async def test_get_users():
    """Try to get list of users"""
    headers = {
        "x-api-key": BMONI_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Try to get specific user
        print("Testing GET /v1/users/a348e005-bc63-4809-99c8-5ebb9a3aae5b...")
        response = await client.get(
            f"{BMONI_API_URL}/v1/users/a348e005-bc63-4809-99c8-5ebb9a3aae5b",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        # Try to create a new user
        print("Testing POST /v1/users...")
        response = await client.post(
            f"{BMONI_API_URL}/v1/users",
            headers=headers,
            json={
                "firstName": "Test User",
                "email": "sabispend+2348020812523@example.com",
                "phoneNumber": "+2348020812523"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}\n")


if __name__ == "__main__":
    print(f"API URL: {BMONI_API_URL}")
    print(f"API Key: {BMONI_API_KEY[:20]}...\n")
    asyncio.run(test_get_users())
