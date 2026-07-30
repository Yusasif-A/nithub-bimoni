"""
EVM Key Vault for BMONI Wallet Signing
========================================

Generates and stores EVM keypairs (one per user) for BMONI wallet operations.
Private keys are encrypted at rest and NEVER exposed to frontend or LLM.

SECURITY:
- Private keys are encrypted with Fernet (symmetric encryption)
- Encryption key is stored in environment variable
- Keys are only decrypted in-memory during signing operations
- No logging of private keys or signatures
"""

import os
import logging
from typing import Optional, Dict
from eth_account import Account
from eth_account.messages import encode_defunct, encode_typed_data
from cryptography.fernet import Fernet
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Enable eth_account's unaudited HD wallet features (for key generation)
Account.enable_unaudited_hdwallet_features()


def _get_encryption_key() -> bytes:
    """Get or generate encryption key for private keys"""
    key = os.getenv("WALLET_ENCRYPTION_KEY")
    
    if not key:
        # Generate a new key if not set (WARNING: This should be set in production!)
        logger.warning("⚠️ WALLET_ENCRYPTION_KEY not set - generating temporary key (DO NOT USE IN PRODUCTION)")
        key = Fernet.generate_key().decode()
        logger.warning(f"⚠️ Generated key: {key}")
        logger.warning("⚠️ Add this to your .env file as WALLET_ENCRYPTION_KEY")
    
    return key.encode() if isinstance(key, str) else key


def _get_key_vault_collection():
    """Get MongoDB collection for encrypted key storage"""
    uri = os.getenv("MONGO_URI")
    if not uri:
        logger.error("❌ MONGO_URI not set")
        return None
    
    try:
        client = MongoClient(uri, server_api=ServerApi("1"))
        db = client.get_database("SabiSpend")
        col = db.get_collection("evm_key_vault")
        
        # Create unique index on bmoni_user_id
        col.create_index("bmoni_user_id", unique=True)
        
        return col
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return None


class KeyVault:
    """Secure storage and signing operations for user EVM keypairs"""
    
    def __init__(self):
        self.fernet = Fernet(_get_encryption_key())
        self.collection = _get_key_vault_collection()
    
    def generate_and_store_keypair(self, bmoni_user_id: str) -> Optional[str]:
        """
        Generate a new EVM keypair and store it encrypted
        
        Args:
            bmoni_user_id: BMONI user ID
        
        Returns:
            Ethereum address (0x...) or None if error
        
        SECURITY: Private key is encrypted before storage
        """
        if self.collection is None:
            logger.error("❌ Key vault not available")
            return None
        
        try:
            # Check if keypair already exists
            existing = self.collection.find_one({"bmoni_user_id": bmoni_user_id})
            if existing:
                logger.info(f"✅ Keypair already exists for {bmoni_user_id}")
                # Decrypt and return address
                encrypted_key = existing["encrypted_private_key"]
                private_key = self.fernet.decrypt(encrypted_key.encode()).decode()
                account = Account.from_key(private_key)
                return account.address
            
            # Generate new keypair
            account = Account.create()
            address = account.address
            private_key = account.key.hex()
            
            # Encrypt private key
            encrypted_key = self.fernet.encrypt(private_key.encode()).decode()
            
            # Store in database
            self.collection.insert_one({
                "bmoni_user_id": bmoni_user_id,
                "ethereum_address": address,
                "encrypted_private_key": encrypted_key
            })
            
            logger.info(f"✅ Generated and stored EVM keypair for {bmoni_user_id}")
            logger.info(f"   Address: {address}")
            
            return address
            
        except Exception as e:
            logger.error(f"❌ Failed to generate keypair: {e}")
            return None
    
    def get_address(self, bmoni_user_id: str) -> Optional[str]:
        """
        Get Ethereum address for a user (without exposing private key)
        
        Args:
            bmoni_user_id: BMONI user ID
        
        Returns:
            Ethereum address (0x...) or None if not found
        """
        if self.collection is None:
            return None
        
        try:
            doc = self.collection.find_one({"bmoni_user_id": bmoni_user_id})
            if doc:
                return doc["ethereum_address"]
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get address: {e}")
            return None
    
    def sign_message(self, bmoni_user_id: str, message: str) -> Optional[str]:
        """
        Sign a message with user's private key (EIP-191 personal_sign)
        
        Args:
            bmoni_user_id: BMONI user ID
            message: Message to sign (plain text)
        
        Returns:
            Hex signature or None if error
        
        SECURITY: Private key is decrypted in-memory only, never logged
        """
        if self.collection is None:
            logger.error("❌ Key vault not available")
            return None
        
        try:
            # Get encrypted private key
            doc = self.collection.find_one({"bmoni_user_id": bmoni_user_id})
            if not doc:
                logger.error(f"❌ No keypair found for {bmoni_user_id}")
                return None
            
            # Decrypt private key (in-memory only)
            encrypted_key = doc["encrypted_private_key"]
            private_key = self.fernet.decrypt(encrypted_key.encode()).decode()
            
            # Create account and sign
            account = Account.from_key(private_key)
            encoded_message = encode_defunct(text=message)
            signed_message = account.sign_message(encoded_message)
            
            # Return hex signature with 0x prefix
            signature = "0x" + signed_message.signature.hex()
            
            logger.info(f"✅ Signed message for {bmoni_user_id}")
            logger.info(f"   Message: {message[:50]}...")
            # NEVER log signature or private key
            
            return signature
            
        except Exception as e:
            logger.error(f"❌ Failed to sign message: {e}")
            return None
    
    def sign_typed_data(self, bmoni_user_id: str, domain: Dict, types: Dict, message: Dict) -> Optional[str]:
        """
        Sign EIP-712 typed data (for withdrawal proposals)
        
        Args:
            bmoni_user_id: BMONI user ID
            domain: EIP-712 domain separator
            types: EIP-712 type definitions
            message: Message to sign
        
        Returns:
            Hex signature or None if error
        
        SECURITY: Private key is decrypted in-memory only, never logged
        """
        if self.collection is None:
            logger.error("❌ Key vault not available")
            return None
        
        try:
            # Get encrypted private key
            doc = self.collection.find_one({"bmoni_user_id": bmoni_user_id})
            if not doc:
                logger.error(f"❌ No keypair found for {bmoni_user_id}")
                return None
            
            # Decrypt private key (in-memory only)
            encrypted_key = doc["encrypted_private_key"]
            private_key = self.fernet.decrypt(encrypted_key.encode()).decode()
            
            # Create account and sign
            account = Account.from_key(private_key)
            
            # Build EIP-712 structured data
            structured_data = {
                "types": types,
                "primaryType": list(types.keys())[0],  # First type is primary
                "domain": domain,
                "message": message
            }
            
            encoded_data = encode_typed_data(full_message=structured_data)
            signed_data = account.sign_message(encoded_data)
            
            # Return hex signature with 0x prefix (matches sign_message's format
            # and BMONI's expected "0x..." signature format)
            signature = "0x" + signed_data.signature.hex()
            
            logger.info(f"✅ Signed EIP-712 data for {bmoni_user_id}")
            # NEVER log signature or private key
            
            return signature
            
        except Exception as e:
            logger.error(f"❌ Failed to sign typed data: {e}")
            return None
    
    def has_keypair(self, bmoni_user_id: str) -> bool:
        """Check if user has a stored keypair"""
        if self.collection is None:
            return False
        
        try:
            return self.collection.count_documents({"bmoni_user_id": bmoni_user_id}, limit=1) > 0
        except Exception as e:
            logger.error(f"❌ Failed to check keypair: {e}")
            return False


# Global key vault instance
key_vault = KeyVault()


# ===============================================
# Public API (safe to call from other modules)
# ===============================================

def ensure_keypair_exists(bmoni_user_id: str) -> Optional[str]:
    """
    Ensure user has an EVM keypair, generate if needed
    
    Returns:
        Ethereum address or None
    """
    return key_vault.generate_and_store_keypair(bmoni_user_id)


def get_user_address(bmoni_user_id: str) -> Optional[str]:
    """Get user's Ethereum address (public, safe to expose)"""
    return key_vault.get_address(bmoni_user_id)


def sign_owner_proof(bmoni_user_id: str, challenge_message: str) -> Optional[str]:
    """Sign BMONI owner-proof challenge (EIP-191)"""
    return key_vault.sign_message(bmoni_user_id, challenge_message)


def sign_withdrawal_proposal(bmoni_user_id: str, domain: Dict, types: Dict, message: Dict) -> Optional[str]:
    """Sign BMONI withdrawal proposal (EIP-712)"""
    return key_vault.sign_typed_data(bmoni_user_id, domain, types, message)