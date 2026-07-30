"""Persistent BMONI lifecycle state for SabiSpend users.

Private keys and signatures are deliberately never stored here.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BMONIStore:
    def __init__(self, collection=None):
        self.collection = collection
        if self.collection is None:
            uri = os.getenv("MONGO_URI")
            if not uri:
                logger.warning("MONGO_URI is not set - BMONI persistence is disabled")
                return
            try:
                client = MongoClient(
                    uri,
                    server_api=ServerApi("1"),
                    connectTimeoutMS=5000,
                    serverSelectionTimeoutMS=5000,
                )
                self.collection = client.get_database("SabiSpend").get_collection("bmoni_accounts")
                self.ensure_indexes()
            except Exception as exc:
                logger.error("Could not initialize BMONI persistence: %s", exc)
                self.collection = None

    @property
    def available(self) -> bool:
        return self.collection is not None

    def ensure_indexes(self) -> None:
        if not self.available:
            return
        self.collection.create_index([("phone_number", ASCENDING)], unique=True, name="phone_unique")
        self.collection.create_index(
            [("bmoni_user_id", ASCENDING)], unique=True, sparse=True, name="bmoni_user_unique"
        )
        self.collection.create_index(
            [("wallet.id", ASCENDING)], unique=True, sparse=True, name="wallet_id_unique"
        )

    def get_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        if not self.available:
            return None
        return self.collection.find_one({"phone_number": phone_number}, {"_id": 0})

    def claim_user_creation(self, phone_number: str) -> bool:
        """Atomically reserve a phone number before calling POST /users.

        A timeout from BMONI is ambiguous, so a reservation is intentionally kept
        for manual reconciliation instead of risking a duplicate remote user.
        """
        self._require_available()
        now = datetime.now(timezone.utc)
        try:
            self.collection.insert_one({
                "phone_number": phone_number,
                "lifecycle_stage": "user_creation_pending",
                "created_at": now,
                "updated_at": now,
            })
            return True
        except DuplicateKeyError:
            return False

    def save_user(self, phone_number: str, bmoni_user_id: str, **details: Any) -> None:
        self._require_available()
        now = datetime.now(timezone.utc)
        values = {
            "bmoni_user_id": bmoni_user_id,
            "updated_at": now,
            **{key: value for key, value in details.items() if value is not None},
        }
        self.collection.update_one(
            {"phone_number": phone_number},
            {"$set": values, "$setOnInsert": {"phone_number": phone_number, "created_at": now}},
            upsert=True,
        )

    def save_wallet(self, phone_number: str, wallet_id: str, address: str, **details: Any) -> None:
        self._set(phone_number, {
            "wallet": {"id": wallet_id, "address": address, **details},
            "lifecycle_stage": "wallet_created",
        })

    def set_kyc_status(self, phone_number: str, status: str, **details: Any) -> None:
        self._set(phone_number, {"kyc": {"status": status, **details}})

    def set_onboarding_status(self, phone_number: str, status: Any) -> None:
        self._set(phone_number, {"onboarding_status": status})

    def save_bank_account(self, phone_number: str, account: Dict[str, Any]) -> None:
        account_id = account.get("id") or account.get("bankAccountId")
        if not account_id:
            raise ValueError("A bank account id is required")
        self._require_available()
        now = datetime.now(timezone.utc)
        self.collection.update_one(
            {"phone_number": phone_number},
            {
                "$set": {"updated_at": now},
                "$addToSet": {"withdrawal_accounts": {**account, "id": account_id}},
            },
        )

    def save_proposal(self, phone_number: str, proposal: Dict[str, Any]) -> None:
        proposal_id = proposal.get("id") or proposal.get("proposalId")
        if not proposal_id:
            raise ValueError("A proposal id is required")
        self._set(phone_number, {
            f"withdrawal_proposals.{proposal_id}": {**proposal, "id": proposal_id}
        })

    def update_proposal_status(self, phone_number: str, proposal_id: str, status: str) -> None:
        self._set(phone_number, {
            f"withdrawal_proposals.{proposal_id}.status": status,
            f"withdrawal_proposals.{proposal_id}.checked_at": datetime.now(timezone.utc),
        })

    def _set(self, phone_number: str, values: Dict[str, Any]) -> None:
        self._require_available()
        result = self.collection.update_one(
            {"phone_number": phone_number},
            {"$set": {**values, "updated_at": datetime.now(timezone.utc)}},
        )
        if result.matched_count == 0:
            raise LookupError(f"No BMONI account exists for {phone_number}")

    def _require_available(self) -> None:
        if not self.available:
            raise RuntimeError("BMONI database is unavailable; check MONGO_URI")


bmoni_store = BMONIStore()
