"""
Nigerian bank name resolver — extracted from bmoni_client.py
================================================================

Solves one specific problem: BMONI's /verify-nigerian-account endpoint needs
an exact bankCode ("058"), but no user actually says "Guaranty Trust Bank" —
they say "GTB" or "GT Bank". This resolves loose spoken/typed bank names to
the right bankCode using BMONI's live bank list plus a small alias table.

DEPENDENCIES (already exist elsewhere in bmoni_client.py — not included here):
- `bmoni_client` — an object with two async methods already implemented:
    bmoni_client.get_nigerian_banks(bmoni_user_id) -> dict
        calls GET /v1/users/{userId}/bank-accounts/nigerian-banks
    bmoni_client.verify_nigerian_account(bmoni_user_id, account_number, bank_code) -> dict
        calls POST /v1/users/{userId}/bank-accounts/verify-nigerian-account
        confirmed response shape: {"accountNumber", "accountName", "bankName", "bankCode"}
- `logger` — a standard logging.Logger instance
- stdlib: time, difflib, typing.Dict/Any

USAGE:
    result = await verify_recipient_bank_account(bmoni_user_id, "0123456789", "GT Bank")
    if result["success"]:
        print(result["account_name"], result["bank_name"])
    else:
        print(result["error"], result.get("candidates"))  # candidates present if ambiguous

NOTE ON THE ALIAS TABLE: this only maps spoken names to search terms (e.g.
"gtb" -> "guaranty trust") — it never hardcodes actual bank codes. The real
bankCode always comes live from BMONI's nigerian-banks endpoint (cached for
BANK_LIST_CACHE_TTL_SECONDS), so if BMONI adds/renames/recodes a bank, this
picks it up automatically with no code changes needed.
"""

import time
import difflib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import bmoni_client from the same directory
from bmoni_client import bmoni_client

_bank_list_cache: Dict[str, Any] = {"banks": None, "fetched_at": 0.0}
BANK_LIST_CACHE_TTL_SECONDS = 3600  # 1 hour

# Common aliases for the banks people actually mention in everyday speech.
# Maps a lowercase alias -> a search term that should match the bank's real
# name in BMONI's list. Extend this as you see real user phrasing come in.
_BANK_ALIASES: Dict[str, str] = {
    "gtb": "guaranty trust",
    "gt bank": "guaranty trust",
    "gtbank": "guaranty trust",
    "guaranty trust bank": "guaranty trust",
    "access": "access",
    "access bank": "access",
    "access diamond": "access",
    "zenith": "zenith",
    "zenith bank": "zenith",
    "uba": "united bank for africa",
    "united bank for africa": "united bank for africa",
    "first bank": "first bank",
    "firstbank": "first bank",
    "fbn": "first bank",
    "union bank": "union bank",
    "fidelity": "fidelity",
    "fidelity bank": "fidelity",
    "sterling": "sterling",
    "sterling bank": "sterling",
    "stanbic": "stanbic",
    "stanbic ibtc": "stanbic",
    "wema": "wema",
    "wema bank": "wema",
    "alat": "wema",  # Wema's digital brand
    "polaris": "polaris",
    "polaris bank": "polaris",
    "keystone": "keystone",
    "keystone bank": "keystone",
    "ecobank": "ecobank",
    "fcmb": "first city monument",
    "first city monument bank": "first city monument",
    "opay": "opay",
    "palmpay": "palmpay",
    "moniepoint": "moniepoint",
    "kuda": "kuda",
    "kuda bank": "kuda",
}


def _normalize_bank_text(text: str) -> str:
    text = text.lower().strip()
    for suffix in (" plc", " nigeria", " limited", " ltd", " bank"):
        text = text.replace(suffix, "")
    return text.strip()


async def _get_cached_bank_list(bmoni_user_id: str) -> list:
    now = time.time()
    if _bank_list_cache["banks"] is not None and (now - _bank_list_cache["fetched_at"]) < BANK_LIST_CACHE_TTL_SECONDS:
        return _bank_list_cache["banks"]
    
    result = await bmoni_client.get_nigerian_banks(bmoni_user_id)
    banks = result.get("banks", result.get("data", []))
    
    if not isinstance(banks, list):
        logger.error(f"❌ Unexpected nigerian-banks response shape: {result}")
        return _bank_list_cache["banks"] or []
    
    _bank_list_cache["banks"] = banks
    _bank_list_cache["fetched_at"] = now
    return banks


async def resolve_bank_code(bmoni_user_id: str, spoken_bank_name: str) -> Dict[str, Any]:
    """
    Resolve a loosely-said bank name (e.g. "Access Bank", "GTB", "zenith") to
    BMONI's exact bankCode + bankName, using the live bank list plus a small
    alias table for names people actually use out loud.
    
    Returns one of:
        {"resolved": True, "bank_code": "...", "bank_name": "..."}
        {"resolved": False, "error": "...", "candidates": [...]}  # 2+ close matches
        {"resolved": False, "error": "..."}                        # no match at all
    """
    banks = await _get_cached_bank_list(bmoni_user_id)
    
    if not banks:
        return {
            "resolved": False,
            "error": "Could not load the bank list right now. Please try again shortly."
        }
    
    raw = spoken_bank_name.lower().strip()
    stripped = _normalize_bank_text(spoken_bank_name)
    
    # Check the alias table against both the raw and suffix-stripped forms —
    # stripping " bank" before the lookup would otherwise break multi-word
    # aliases like "gt bank" (which needs to match as a whole, not as "gt").
    query = _BANK_ALIASES.get(raw) or _BANK_ALIASES.get(stripped) or stripped
    
    normalized_banks = [(b, _normalize_bank_text(b.get("bankName", ""))) for b in banks]
    
    # 1. Exact or substring match first — most reliable
    substring_matches = [b for b, norm in normalized_banks if query in norm or norm in query]
    
    # If multiple matches, try to prefer exact match or most common bank
    if len(substring_matches) > 1:
        # Try exact match first
        exact_matches = [b for b, norm in normalized_banks if query == norm]
        if len(exact_matches) == 1:
            b = exact_matches[0]
            return {"resolved": True, "bank_code": b.get("bankCode"), "bank_name": b.get("bankName")}
        
        # Prefer main banks over mobile/microfinance variants
        # e.g., "Access Bank" over "Accessmobile"
        main_banks = [b for b in substring_matches if "mobile" not in b.get("bankName", "").lower() 
                      and "microfinance" not in b.get("bankName", "").lower()]
        if len(main_banks) == 1:
            b = main_banks[0]
            return {"resolved": True, "bank_code": b.get("bankCode"), "bank_name": b.get("bankName")}
        
        # Still ambiguous
        return {"resolved": False,
                "error": f"Found more than one bank matching \"{spoken_bank_name}\".",
                "candidates": [b.get("bankName") for b in substring_matches[:5]]}
    
    if len(substring_matches) == 1:
        b = substring_matches[0]
        return {
            "resolved": True,
            "bank_code": b.get("bankCode"),
            "bank_name": b.get("bankName")
        }
    
    if len(substring_matches) > 1:
        return {
            "resolved": False,
            "error": f"Found more than one bank matching \"{spoken_bank_name}\".",
            "candidates": [b.get("bankName") for b in substring_matches[:5]],
        }
    
    # 2. Fall back to fuzzy matching for typos/mishearings
    names = [norm for _, norm in normalized_banks]
    close = difflib.get_close_matches(query, names, n=3, cutoff=0.6)
    
    if len(close) == 1:
        idx = names.index(close[0])
        b = normalized_banks[idx][0]
        return {
            "resolved": True,
            "bank_code": b.get("bankCode"),
            "bank_name": b.get("bankName")
        }
    
    if len(close) > 1:
        candidates = [normalized_banks[names.index(c)][0].get("bankName") for c in close]
        return {
            "resolved": False,
            "error": f"Not sure which bank you mean by \"{spoken_bank_name}\".",
            "candidates": candidates,
        }
    
    return {
        "resolved": False,
        "error": f"Couldn't find a bank matching \"{spoken_bank_name}\"."
    }


async def verify_recipient_bank_account(
    bmoni_user_id: str,
    account_number: str,
    spoken_bank_name: str
) -> Dict[str, Any]:
    """
    Resolve the bank name and verify the account number in one call — the
    function to actually use from a tool, rather than calling resolve_bank_code
    and verify_nigerian_account separately every time.
    
    Returns:
        {"success": True, "account_name": "...", "bank_name": "...", "account_number": "..."}
        {"success": False, "error": "...", "candidates": [...]}  # if ambiguous
        {"success": False, "error": "..."}                        # if failed
    """
    resolution = await resolve_bank_code(bmoni_user_id, spoken_bank_name)
    
    if not resolution.get("resolved"):
        return {"success": False, **resolution}
    
    result = await bmoni_client.verify_nigerian_account(
        bmoni_user_id,
        account_number,
        resolution["bank_code"]
    )
    
    if "error" in result:
        return {"success": False, "error": result["error"]}
    
    account_name = result.get("accountName")
    if not account_name:
        return {
            "success": False,
            "error": "Could not verify that account number for this bank."
        }
    
    return {
        "success": True,
        "account_name": account_name,
        "bank_name": resolution["bank_name"],
        "account_number": account_number,
        "bank_code": resolution["bank_code"],
    }
