"""
BMONI Wallet Integration Client
================================

Implements BMONI Embedded Finance API for SabiSpend
Based on: https://embedded-dev.bmoni.com

This module handles:
- User creation
- Wallet operations (server-side signing, no separate signer page needed)
- Balance checks
- Transaction history
- Deposit account information
- Peer-to-peer sends (confirmed with a one-time code sent over WhatsApp)
- Withdrawal proposals (signing done separately — not yet wired up)

SECURITY: API key stays in backend only, never sent to client/WhatsApp
"""

import os
import time
import random
import asyncio
import logging
import httpx
from typing import Any, Dict, Optional
from config import BMONI_API_URL, BMONI_API_KEY
from bmoni_store import bmoni_store
from key_vault import ensure_keypair_exists, get_user_address, sign_owner_proof, sign_withdrawal_proposal

logger = logging.getLogger(__name__)


class BMONIClient:
    """Client for BMONI Embedded Finance API"""
    
    def __init__(self):
        # Base URL should NOT include /v1 (paths already include it)
        self.api_url = BMONI_API_URL.rstrip('/')  # Remove trailing slash if any
        self.api_key = BMONI_API_KEY
        
        if not self.api_key:
            logger.warning("⚠️ BMONI_API_KEY not set - BMONI features will be disabled")
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate auth headers for BMONI API"""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> Dict:
        """Call BMONI and preserve the response body on useful HTTP errors."""
        if not self.api_key:
            return {"error": "BMONI API not configured"}
        headers = dict(self._get_headers())
        if "files" in kwargs:
            headers.pop("Content-Type", None)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method, f"{self.api_url}{path}", headers=headers, **kwargs
                )
            response.raise_for_status()
            return response.json() if response.content else {"success": True}
        except httpx.HTTPStatusError as exc:
            try:
                detail = exc.response.json()
            except ValueError:
                detail = exc.response.text
            logger.error("BMONI %s %s failed (%s): %s", method, path, exc.response.status_code, detail)
            return {"error": detail, "status_code": exc.response.status_code}
        except httpx.HTTPError as exc:
            logger.error("BMONI %s %s failed: %s", method, path, exc)
            return {"error": str(exc)}
    
    async def create_user(self, phone_number: str, first_name: str, email: str = None) -> Dict:
        """
        Create a BMONI user account
        
        Args:
            phone_number: User's phone in international format (e.g., "+2348012345678")
            first_name: User's name
            email: User's email (generate unique if not provided)
        
        Returns:
            Dict with bmoniUserId and user info
        """
        if not self.api_key:
            return {"error": "BMONI API not configured", "bmoniUserId": None}
        
        # Generate unique email if not provided
        if not email:
            # Use phone number to create unique email
            phone_clean = phone_number.replace("+", "").replace(" ", "")
            email = f"sabispend+{phone_clean}@example.com"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "firstName": first_name,
                    "email": email,
                    "phoneNumber": phone_number
                }
                
                response = await client.post(
                    f"{self.api_url}/v1/users",
                    headers=self._get_headers(),
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                logger.info(f"📥 BMONI API response: {result}")
                
                # Try different paths for user ID
                user_data = result.get("user", result.get("data", result))
                bmoni_user_id = (
                    user_data.get("bmoniUserId") or 
                    user_data.get("id") or 
                    user_data.get("userId")
                )
                
                if not bmoni_user_id:
                    logger.error(f"❌ No user ID in response. Full response: {result}")
                    return {"error": "BMONI response did not contain a user id", "bmoniUserId": None}
                logger.info(f"✅ BMONI user created: {phone_number} → {bmoni_user_id}")
                return {
                    "success": True,
                    "bmoniUserId": bmoni_user_id,
                    "email": email,
                    "phoneNumber": phone_number
                }
                
        except httpx.HTTPError as e:
            logger.error(f"❌ BMONI user creation failed: {e}")
            return {"error": str(e), "bmoniUserId": None}
        except Exception as e:
            logger.error(f"❌ BMONI user creation error: {e}")
            return {"error": str(e), "bmoniUserId": None}
    
    async def get_balance(self, bmoni_user_id: str) -> Dict:
        """
        Get wallet balance for a user
        
        Args:
            bmoni_user_id: BMONI user ID (from create_user)
        
        Returns:
            Dict with balance info for each currency
        """
        if not self.api_key:
            return {"error": "BMONI API not configured", "balances": []}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.api_url}/v1/users/{bmoni_user_id}/smart-wallets/account/balances",
                    headers=self._get_headers()
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ BMONI balance check for user {bmoni_user_id}")
                return {
                    "success": True,
                    "balances": result.get("balances", [])
                }
                
        except httpx.HTTPError as e:
            logger.error(f"❌ BMONI balance check failed: {e}")
            return {"error": str(e), "balances": []}
        except Exception as e:
            logger.error(f"❌ BMONI balance check error: {e}")
            return {"error": str(e), "balances": []}
    
    async def get_transactions(self, bmoni_user_id: str, limit: int = 10) -> Dict:
        """
        Get recent transactions for a user
        
        Args:
            bmoni_user_id: BMONI user ID
            limit: Number of transactions to retrieve
        
        Returns:
            Dict with transaction history
        """
        if not self.api_key:
            return {"error": "BMONI API not configured", "transactions": []}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.api_url}/v1/users/{bmoni_user_id}/smart-wallets/account/transactions",
                    headers=self._get_headers(),
                    params={"limit": limit}
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ BMONI transactions retrieved for user {bmoni_user_id}")
                return {
                    "success": True,
                    "transactions": result.get("transactions", [])
                }
                
        except httpx.HTTPError as e:
            logger.error(f"❌ BMONI transactions failed: {e}")
            return {"error": str(e), "transactions": []}
        except Exception as e:
            logger.error(f"❌ BMONI transactions error: {e}")
            return {"error": str(e), "transactions": []}
    
    async def get_deposit_account(self, bmoni_user_id: str, currency: str = "NGN") -> Dict:
        """
        Get virtual account number for deposits
        
        Args:
            bmoni_user_id: BMONI user ID
            currency: Currency code (NGN for Nigerian Naira)
        
        Returns:
            Dict with account number and bank details
        """
        if not self.api_key:
            return {"error": "BMONI API not configured", "account_number": None}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.api_url}/v1/users/{bmoni_user_id}/bank-accounts/deposit-accounts/{currency}",
                    headers=self._get_headers()
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ BMONI deposit account retrieved for user {bmoni_user_id}")
                return {
                    "success": True,
                    "account_number": result.get("accountNumber"),
                    "account_name": result.get("accountName"),
                    "bank_name": result.get("bankName"),
                    "bank_code": result.get("bankCode")
                }
                
        except httpx.HTTPError as e:
            logger.error(f"❌ BMONI deposit account failed: {e}")
            return {"error": str(e), "account_number": None}
        except Exception as e:
            logger.error(f"❌ BMONI deposit account error: {e}")
            return {"error": str(e), "account_number": None}
    
    async def get_wallet_status(self, bmoni_user_id: str) -> Dict:
        """
        Check wallet activation status
        
        Args:
            bmoni_user_id: BMONI user ID
        
        Returns:
            Dict with wallet status information
        """
        if not self.api_key:
            return {"error": "BMONI API not configured", "active": False}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.api_url}/v1/users/{bmoni_user_id}/onboarding/status",
                    headers=self._get_headers()
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ BMONI wallet status for user {bmoni_user_id}")
                return {
                    "success": True,
                    "status": result
                }
                
        except httpx.HTTPError as e:
            logger.error(f"❌ BMONI wallet status failed: {e}")
            return {"error": str(e), "active": False}

    async def create_owner_proof_challenge(
        self, bmoni_user_id: str, owner_address: str, currency: str = "CNGN"
    ) -> Dict:
        return await self._request(
            "POST",
            f"/v1/users/{bmoni_user_id}/smart-wallets/owner-proof-challenges",
            json={"currency": currency, "userOwnerAddress": owner_address},
        )

    async def create_managed_wallet(
        self, bmoni_user_id: str, owner_address: str, challenge_id: str,
        signature: str, phone_number: Optional[str] = None, currency: str = "CNGN"
    ) -> Dict:
        result = await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/smart-wallets/create-managed",
            json={
                "currency": currency,
                "userOwnerAddress": owner_address,
                "ownerProofChallengeId": challenge_id,
                "ownerProofSignature": signature,
            },
        )
        if phone_number and "error" not in result:
            wallet = result.get("wallet", result)
            wallet_id = wallet.get("id") or wallet.get("smartWalletId")
            address = wallet.get("address") or wallet.get("walletAddress")
            if wallet_id and address:
                bmoni_store.save_wallet(phone_number, wallet_id, address, currency=currency)
        return result

    async def get_wallets(self, bmoni_user_id: str) -> Dict:
        return await self._request(
            "GET", f"/v1/users/{bmoni_user_id}/smart-wallets/account/wallets"
        )

    async def get_kyc_options(self, bmoni_user_id: str) -> Dict:
        return await self._request("GET", f"/v1/users/{bmoni_user_id}/kyc/options")

    async def search_occupations(self, bmoni_user_id: str, search: str) -> Dict:
        return await self._request(
            "GET", f"/v1/users/{bmoni_user_id}/kyc/occupations", params={"search": search}
        )

    async def upload_kyc_document(
        self, bmoni_user_id: str, document_kind: str, filename: str,
        content: bytes, content_type: str, fields: Dict[str, str]
    ) -> Dict:
        if document_kind not in {"identification", "proof-of-address"}:
            raise ValueError("document_kind must be identification or proof-of-address")
        return await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/kyc/documents/{document_kind}",
            data=fields, files={"file": (filename, content, content_type)},
        )

    async def update_kyc(
        self, bmoni_user_id: str, payload: Dict[str, Any], phone_number: Optional[str] = None
    ) -> Dict:
        result = await self._request("PATCH", f"/v1/users/{bmoni_user_id}/kyc", json=payload)
        if phone_number and "error" not in result:
            bmoni_store.set_kyc_status(phone_number, "submitted")
        return result

    async def get_kyc_readiness(self, bmoni_user_id: str) -> Dict:
        return await self._request("GET", f"/v1/users/{bmoni_user_id}/kyc/readiness")

    async def activate_kyc(
        self, bmoni_user_id: str, phone_number: Optional[str] = None,
        sumsub_level_name: Optional[str] = None
    ) -> Dict:
        payload = {} if sumsub_level_name is None else {"sumsubLevelName": sumsub_level_name}
        result = await self._request("POST", f"/v1/users/{bmoni_user_id}/kyc/activate", json=payload)
        if phone_number and "error" not in result:
            bmoni_store.set_kyc_status(phone_number, "activated")
        return result

    async def start_nigeria(
        self, bmoni_user_id: str, bvn: str, wallet_address: str,
        wallet_index: int = 0, phone_number: Optional[str] = None
    ) -> Dict:
        result = await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/onboarding/start-nigeria",
            json={"bvn": bvn, "ngnWalletAddress": wallet_address, "ngnWalletIndex": wallet_index},
        )
        if phone_number and "error" not in result:
            bmoni_store.set_onboarding_status(phone_number, result)
        return result

    async def get_nigerian_banks(self, bmoni_user_id: str) -> Dict:
        return await self._request(
            "GET", f"/v1/users/{bmoni_user_id}/bank-accounts/nigerian-banks"
        )

    async def verify_nigerian_account(
        self, bmoni_user_id: str, account_number: str, bank_code: str
    ) -> Dict:
        return await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/bank-accounts/verify-nigerian-account",
            json={"accountNumber": account_number, "bankCode": bank_code},
        )

    async def create_withdrawal_account(
        self, bmoni_user_id: str, account: Dict[str, str], phone_number: Optional[str] = None
    ) -> Dict:
        result = await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/bank-accounts/withdrawal-accounts/nigeria",
            json=account,
        )
        if phone_number and "error" not in result:
            bmoni_store.save_bank_account(phone_number, result)
        return result

    async def create_transfer_proposal(
        self, bmoni_user_id: str, wallet_id: str, amount: str, currency: str = "CNGN",
        to_user_id: Optional[str] = None, to_address: Optional[str] = None,
        description: Optional[str] = None, phone_number: Optional[str] = None,
    ) -> Dict:
        if not to_user_id and not to_address:
            return {"error": "Must provide either to_user_id or to_address"}
        proposal_body: Dict[str, Any] = {
            "type": "TRANSFER",
            "amount": str(amount),
            "currency": currency,
        }
        if to_user_id:
            proposal_body["toUserId"] = to_user_id
        else:
            proposal_body["toAddress"] = to_address
        if description:
            proposal_body["description"] = description[:500]

        result = await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/smart-wallets/{wallet_id}/proposals",
            json={"proposal": proposal_body},
        )
        if phone_number and "error" not in result:
            # Extract the proposal object from the response
            proposal = result.get("data", {}).get("proposal", result.get("proposal"))
            if proposal:
                bmoni_store.save_proposal(phone_number, proposal)
        return result

    async def approve_proposal(self, bmoni_user_id: str, proposal_id: str) -> Dict:
        return await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/smart-wallets/proposals/{proposal_id}/approve"
        )

    async def get_proposal_sign_payload(self, bmoni_user_id: str, proposal_id: str) -> Dict:
        return await self._request(
            "GET", f"/v1/users/{bmoni_user_id}/smart-wallets/proposals/{proposal_id}/sign-payload"
        )

    async def sign_proposal(
        self, bmoni_user_id: str, proposal_id: str, payload: Dict[str, Any]
    ) -> Dict:
        return await self._request(
            "POST", f"/v1/users/{bmoni_user_id}/smart-wallets/proposals/{proposal_id}/sign",
            json=payload,
        )

    async def get_proposal(
        self, bmoni_user_id: str, proposal_id: str, phone_number: Optional[str] = None
    ) -> Dict:
        result = await self._request(
            "GET", f"/v1/users/{bmoni_user_id}/smart-wallets/proposals/{proposal_id}"
        )
        if phone_number and "error" not in result and result.get("status"):
            bmoni_store.update_proposal_status(phone_number, proposal_id, result["status"])
        return result

    async def execute_transfer(
        self, bmoni_user_id: str, wallet_id: str, amount: str, currency: str = "CNGN",
        to_user_id: Optional[str] = None, to_address: Optional[str] = None,
        description: Optional[str] = None, phone_number: Optional[str] = None,
        poll_interval_seconds: float = 1.5, poll_timeout_seconds: float = 30.0,
    ) -> Dict:
        """
        Runs the full proposal -> approve -> sign-payload -> sign -> confirm flow
        for a peer-to-peer transfer. Call this only after your own confirmation
        step (e.g. the OTP check in request_send_money/confirm_send_money below)
        has already verified the user actually wants this transfer to happen.
        """
        proposal_result = await self.create_transfer_proposal(
            bmoni_user_id, wallet_id, amount, currency, to_user_id, to_address,
            description, phone_number,
        )
        if "error" in proposal_result:
            return {"error": proposal_result["error"]}
        proposal = proposal_result.get("data", {}).get("proposal", proposal_result.get("proposal", proposal_result))
        proposal_id = proposal.get("id")
        if not proposal_id:
            return {"error": "Proposal creation did not return an id"}

        approve_result = await self.approve_proposal(bmoni_user_id, proposal_id)
        if "error" in approve_result:
            return {"error": f"Approval failed: {approve_result['error']}"}

        # Poll for PENDING_SIGNATURES / the sign payload becoming available.
        # A 404 here means the approval threshold hasn't been met yet, not that
        # the proposal is missing — so poll rather than calling once.
        sign_payload_result = None
        deadline = time.time() + poll_timeout_seconds
        while time.time() < deadline:
            candidate = await self.get_proposal_sign_payload(bmoni_user_id, proposal_id)
            if "error" not in candidate and candidate.get("typedData"):
                sign_payload_result = candidate
                break
            await asyncio.sleep(poll_interval_seconds)
        if not sign_payload_result:
            return {"error": "Timed out waiting for the proposal to reach PENDING_SIGNATURES"}

        typed_data = sign_payload_result["typedData"]
        domain = typed_data.get("domain")
        types = typed_data.get("types")
        message = typed_data.get("message")
        if domain is None or types is None or message is None:
            logger.error(
                f"❌ Unexpected typedData shape for proposal {proposal_id}: "
                f"keys present = {list(typed_data.keys())}"
            )
            return {"error": "Received an unexpected signing payload shape from BMONI"}

        try:
            signature = sign_withdrawal_proposal(bmoni_user_id, domain, types, message)
        except Exception as e:
            logger.error(f"❌ Failed to sign transfer proposal {proposal_id}: {e}")
            return {"error": "Could not sign the transfer"}
        if not signature:
            return {"error": "Signing returned no signature — check the key vault logs"}

        sign_result = await self.sign_proposal(bmoni_user_id, proposal_id, {"signature": signature})
        if "error" in sign_result:
            return {"error": f"Submitting signature failed: {sign_result['error']}"}

        # Poll for a terminal status
        deadline = time.time() + poll_timeout_seconds
        final_status = None
        while time.time() < deadline:
            status_result = await self.get_proposal(bmoni_user_id, proposal_id, phone_number)
            status = status_result.get("status")
            if status in ("COMPLETED", "FAILED", "REJECTED"):
                final_status = status_result
                break
            await asyncio.sleep(poll_interval_seconds)
        if not final_status:
            return {"error": "Timed out waiting for the transfer to complete", "proposal_id": proposal_id}
        if final_status.get("status") != "COMPLETED":
            return {"error": f"Transfer did not complete (status: {final_status.get('status')})"}
        return final_status


# Global client instance
bmoni_client = BMONIClient()


# ===============================================
# Helper functions for easy access from agent
# ===============================================

async def get_or_create_bmoni_user(phone_number: str, user_name: str) -> Optional[str]:
    """
    Get existing BMONI user ID or create new user
    
    Returns:
        bmoniUserId string or None if error
    
    Note: Store the bmoniUserId in your database against phone_number
    """
    existing = bmoni_store.get_by_phone(phone_number)
    if existing and existing.get("bmoni_user_id"):
        logger.info(f"✅ Found existing BMONI user: {existing['bmoni_user_id']}")
        return existing["bmoni_user_id"]

    if not bmoni_store.available:
        logger.error("Refusing to create a BMONI user without persistent storage")
        return None

    if not bmoni_store.claim_user_creation(phone_number):
        logger.warning(
            "BMONI user creation already reserved for %s; refusing a duplicate request",
            phone_number,
        )
        # If locked, check if user was created but lock not cleared
        existing = bmoni_store.get_by_phone(phone_number)
        if existing and existing.get("bmoni_user_id"):
            logger.info(f"✅ Found user after lock check: {existing['bmoni_user_id']}")
            return existing["bmoni_user_id"]
        return None

    result = await bmoni_client.create_user(phone_number, user_name)
    
    # Handle 409 Conflict - user already exists on BMONI side
    if "error" in result:
        error_detail = result.get("error", {})
        status_code = result.get("status_code")
        
        if status_code == 409:
            logger.info(f"⚠️ User already exists on BMONI (409), fetching from API...")
            # Try to get existing user from BMONI API
            try:
                users_result = await bmoni_client._request("GET", "/v1/users")
                if "error" not in users_result:
                    users = users_result.get("users", [])
                    # Find user by phone number
                    for user in users:
                        if user.get("phoneNumber") == phone_number:
                            bmoni_user_id = user.get("bmoniUserId") or user.get("id")
                            if bmoni_user_id:
                                logger.info(f"✅ Retrieved existing user from API: {bmoni_user_id}")
                                # Save to local DB
                                bmoni_store.save_user(
                                    phone_number,
                                    bmoni_user_id,
                                    first_name=user.get("firstName", user_name),
                                    email=user.get("email"),
                                    lifecycle_stage="user_exists",
                                )
                                return bmoni_user_id
            except Exception as e:
                logger.error(f"❌ Failed to retrieve existing user: {e}")
        
        logger.error(f"❌ BMONI user creation failed: {error_detail}")
        return None
    
    if result.get("success"):
        bmoni_user_id = result.get("bmoniUserId")
        if not bmoni_user_id:
            return None
        bmoni_store.save_user(
            phone_number,
            bmoni_user_id,
            first_name=user_name,
            email=result.get("email"),
            lifecycle_stage="user_created",
        )
        return bmoni_user_id
    return None


async def get_user_balance_naira(bmoni_user_id: str) -> float:
    """
    Get user's NGN/CNGN balance
    
    Returns:
        Balance in Naira as float, 0 if error
    """
    result = await bmoni_client.get_balance(bmoni_user_id)
    
    if result.get("success"):
        balances = result.get("balances", [])
        # Find CNGN (Nigerian Naira stablecoin) or NGN balance
        for balance in balances:
            currency = balance.get("currency", "").upper()
            if currency in ["CNGN", "NGN"]:
                # Check both "balance" and "amount" fields (API uses "balance")
                amount_value = balance.get("balance") or balance.get("amount") or "0"
                return float(amount_value)
    
    return 0.0


async def get_deposit_account_details(bmoni_user_id: str) -> Dict:
    """
    Get virtual account number for receiving money
    
    Returns:
        Dict with account_number, bank_name, etc.
    """
    return await bmoni_client.get_deposit_account(bmoni_user_id, "NGN")


async def get_recent_transactions(bmoni_user_id: str, limit: int = 5) -> list:
    """
    Get recent wallet transactions
    
    Returns:
        List of transaction dicts
    """
    result = await bmoni_client.get_transactions(bmoni_user_id, limit)
    
    if result.get("success"):
        return result.get("transactions", [])
    
    return []



async def ensure_wallet_created(phone_number: str, bmoni_user_id: str, currency: str = "CNGN") -> Dict:
    """
    Ensure user has a BMONI wallet, create if needed (server-side signing, no user action required)
    
    This function implements the full 4-step wallet creation flow:
    1. Generate EVM keypair (stored encrypted)
    2. Request owner-proof challenge from BMONI
    3. Sign challenge with user's private key (server-side)
    4. Create managed wallet with signature
    
    Args:
        phone_number: User's phone number
        bmoni_user_id: BMONI user ID
        currency: Currency code (default: CNGN for Nigerian Naira)
    
    Returns:
        Dict with success status, wallet_id, and wallet_address
    
    SECURITY: Private key never exposed to frontend or LLM
    """
    # Check if wallet already exists
    existing = bmoni_store.get_by_phone(phone_number)
    if existing and existing.get("wallet"):
        wallet = existing["wallet"]
        logger.info(f"✅ Wallet already exists for {phone_number}: {wallet.get('address')}")
        return {
            "success": True,
            "wallet_id": wallet.get("id"),
            "wallet_address": wallet.get("address"),
            "already_exists": True
        }
    
    logger.info(f"🔐 Starting wallet creation for {phone_number} (bmoni_user_id: {bmoni_user_id})")
    
    # STEP 1: Generate and store EVM keypair (encrypted)
    logger.info("📝 Step 1: Generating EVM keypair...")
    owner_address = ensure_keypair_exists(bmoni_user_id)
    
    if not owner_address:
        logger.error("❌ Failed to generate EVM keypair")
        return {"success": False, "error": "Failed to generate keypair"}
    
    logger.info(f"✅ Generated keypair with address: {owner_address}")
    
    # STEP 2: Request owner-proof challenge
    logger.info("📝 Step 2: Requesting owner-proof challenge...")
    challenge_result = await bmoni_client.create_owner_proof_challenge(
        bmoni_user_id, owner_address, currency
    )
    
    if "error" in challenge_result:
        logger.error(f"❌ Failed to get challenge: {challenge_result['error']}")
        return {"success": False, "error": f"Challenge request failed: {challenge_result['error']}"}
    
    challenge_id = challenge_result.get("id") or challenge_result.get("challengeId")
    challenge_message = challenge_result.get("message")
    
    if not challenge_id or not challenge_message:
        logger.error("❌ Challenge response missing id or message")
        return {"success": False, "error": "Invalid challenge response"}
    
    logger.info(f"✅ Received challenge: {challenge_id}")
    
    # STEP 3: Sign challenge with user's private key (server-side, no user action)
    logger.info("📝 Step 3: Signing challenge with user's private key...")
    signature = sign_owner_proof(bmoni_user_id, challenge_message)
    
    if not signature:
        logger.error("❌ Failed to sign challenge")
        return {"success": False, "error": "Signature generation failed"}
    
    logger.info("✅ Challenge signed successfully")
    
    # STEP 4: Create managed wallet
    logger.info("📝 Step 4: Creating managed wallet...")
    wallet_result = await bmoni_client.create_managed_wallet(
        bmoni_user_id, owner_address, challenge_id, signature, phone_number, currency
    )
    
    if "error" in wallet_result:
        logger.error(f"❌ Failed to create wallet: {wallet_result['error']}")
        return {"success": False, "error": f"Wallet creation failed: {wallet_result['error']}"}
    
    wallet = wallet_result.get("wallet", wallet_result)
    wallet_id = wallet.get("id") or wallet.get("smartWalletId")
    wallet_address = wallet.get("address") or wallet.get("walletAddress")
    
    if not wallet_id or not wallet_address:
        logger.error("❌ Wallet response missing id or address")
        return {"success": False, "error": "Invalid wallet response"}
    
    logger.info(f"🎉 Wallet created successfully!")
    logger.info(f"   Wallet ID: {wallet_id}")
    logger.info(f"   Wallet Address: {wallet_address}")
    logger.info(f"   Currency: {currency}")
    
    return {
        "success": True,
        "wallet_id": wallet_id,
        "wallet_address": wallet_address,
        "currency": currency
    }


# ===============================================
# Send money — confirmed with a one-time code
# ===============================================
#
# BMONI's own value-moving endpoints (wallet creation, withdrawal) all require
# an owner-key signature. The /smart-wallets/account/send endpoint is called
# directly here with no such signature, matching what BMONI's sandbox accepts
# today. As an extra safety layer on our side — since sending money from a
# WhatsApp conversation has no separate "tap to confirm" step the way a bank
# app would — every send must be confirmed with a one-time code delivered back
# to the sender's own registered WhatsApp number before it executes.
#
# NOTE: this pending-send store is in-memory and per-process. It resets on a
# restart/redeploy, and won't work correctly across multiple server instances.
# Fine for a single-instance hackathon deployment; swap for a persistent store
# (e.g. a bmoni_store collection with a TTL index) before going further than that.

_pending_sends: Dict[str, Dict[str, Any]] = {}  # keyed by sender's normalized phone number
SEND_OTP_TTL_SECONDS = 300  # 5 minutes
SEND_OTP_MAX_ATTEMPTS = 3

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")


def _generate_send_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


async def _send_whatsapp_text_direct(to_number: str, text: str) -> bool:
    """
    Minimal, standalone WhatsApp text sender used only for delivering the
    send-money confirmation code. Kept separate from app.py's send_whatsapp_message
    to avoid a circular import (app.py imports unified_agent, which imports this
    module) — this duplicates just the plain-text-send case.
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("❌ Cannot send confirmation code — WhatsApp credentials not configured")
        return False
    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    json_data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"❌ Failed to send confirmation code via WhatsApp: {e}")
        return False


async def request_send_money(
    sender_phone: str, sender_bmoni_user_id: str, sender_wallet_id: str,
    recipient_phone: str, amount: float
) -> Dict[str, Any]:
    """
    Step 1 of send money: validate the request, generate a one-time code, and
    deliver it to the sender's own registered WhatsApp number. Does not move
    any money and does not create a BMONI proposal yet — that only happens in
    confirm_send_money() once the code comes back correctly.
    """
    sender_phone = sender_phone if sender_phone.startswith("+") else f"+{sender_phone}"
    recipient_norm = recipient_phone if recipient_phone.startswith("+") else f"+{recipient_phone}"

    recipient_account = bmoni_store.get_by_phone(recipient_norm)
    if not recipient_account or not recipient_account.get("bmoni_user_id"):
        return {
            "success": False,
            "error": f"Recipient {recipient_phone} doesn't have a SabiSpend wallet yet. They need to sign up first.",
        }
    recipient_bmoni_user_id = recipient_account["bmoni_user_id"]

    # Per BMONI's docs: sending CNGN to a user who only holds a different
    # currency's wallet fails with a 400, not a missing-endpoint error. Check
    # the recipient's actual wallets first rather than trusting our own cache.
    wallets_result = await bmoni_client.get_wallets(recipient_bmoni_user_id)
    
    # Handle different response formats
    if isinstance(wallets_result, list):
        recipient_wallets = wallets_result
    elif isinstance(wallets_result, dict):
        recipient_wallets = wallets_result.get("wallets", wallets_result.get("data", {}).get("wallets", []))
    else:
        recipient_wallets = []
    
    has_ngn_wallet = any(
        w.get("currency") in ("CNGN", "NGN") and w.get("status", "active") == "active"
        for w in (recipient_wallets if isinstance(recipient_wallets, list) else [])
    )
    if not has_ngn_wallet:
        return {
            "success": False,
            "error": f"{recipient_phone} doesn't have an active NGN wallet yet, so they can't receive this transfer.",
        }

    sender_balance = await get_user_balance_naira(sender_bmoni_user_id)
    if sender_balance < amount:
        return {
            "success": False,
            "error": f"Insufficient balance. You have ₦{sender_balance:,.2f} but tried to send ₦{amount:,.2f}.",
        }

    code = _generate_send_otp()
    _pending_sends[sender_phone] = {
        "otp": code,
        "attempts": 0,
        "recipient_phone": recipient_norm,
        "recipient_bmoni_user_id": recipient_bmoni_user_id,
        "sender_bmoni_user_id": sender_bmoni_user_id,
        "sender_wallet_id": sender_wallet_id,
        "amount": amount,
        "expires_at": time.time() + SEND_OTP_TTL_SECONDS,
    }

    delivered = await _send_whatsapp_text_direct(
        sender_phone,
        f"Your SabiSpend confirmation code is {code}. "
        f"Reply with this code to confirm sending ₦{amount:,.2f} to {recipient_phone}. "
        f"This code expires in 5 minutes.",
    )
    if not delivered:
        _pending_sends.pop(sender_phone, None)
        return {"success": False, "error": "Could not send a confirmation code right now. Please try again shortly."}

    logger.info(f"📤 Send-money confirmation code issued for {sender_phone} → {recipient_norm} (₦{amount:,.2f})")
    return {"success": True, "status": "code_sent", "recipient_phone": recipient_phone, "amount": amount}


async def confirm_send_money(sender_phone: str, code: str) -> Dict[str, Any]:
    """
    Step 2 of send money: verify the code the user replied with, and if valid,
    run the real proposal -> approve -> sign-payload -> sign flow via BMONI.
    Consumes the pending request either way (a wrong code counts as an attempt;
    too many wrong attempts cancels it).
    """
    sender_phone = sender_phone if sender_phone.startswith("+") else f"+{sender_phone}"
    pending = _pending_sends.get(sender_phone)

    if not pending:
        return {"success": False, "error": "There's no pending transfer to confirm. Please start a new send request."}

    if time.time() > pending["expires_at"]:
        _pending_sends.pop(sender_phone, None)
        return {"success": False, "error": "That confirmation code has expired. Please start the send again."}

    if code.strip() != pending["otp"]:
        pending["attempts"] += 1
        if pending["attempts"] >= SEND_OTP_MAX_ATTEMPTS:
            _pending_sends.pop(sender_phone, None)
            return {"success": False, "error": "Too many incorrect codes. Please start the send again."}
        return {"success": False, "error": "That code doesn't match. Please check and reply with the correct code."}

    # Code is correct — consume it and run the real BMONI transfer flow
    _pending_sends.pop(sender_phone, None)
    result = await bmoni_client.execute_transfer(
        bmoni_user_id=pending["sender_bmoni_user_id"],
        wallet_id=pending["sender_wallet_id"],
        amount=str(pending["amount"]),
        currency="CNGN",
        to_user_id=pending["recipient_bmoni_user_id"],
        description="SabiSpend transfer",
        phone_number=sender_phone,
    )

    if "error" in result:
        return {"success": False, "error": f"Transfer failed: {result['error']}"}

    logger.info(
        f"✅ Confirmed transfer executed: {sender_phone} → {pending['recipient_phone']} "
        f"(₦{pending['amount']:,.2f})"
    )
    return {
        "success": True,
        "amount": pending["amount"],
        "recipient_phone": pending["recipient_phone"],
    }