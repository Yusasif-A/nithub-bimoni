# BMONI Support Request - Signature Mismatch Issue (URGENT)

**Date:** July 30, 2026  
**Partner:** SabiSpend  
**Environment:** Development (embedded-dev.bmoni.com)  
**API Key:** pk_a025cacbf33a_76fb864113f3540909de5b1da39cc146906e35b1c6d4d1e4

---

## Critical Issue: Signature Mismatch on ALL Wallets

We are experiencing **100% failure rate** on transfer signatures with error:
```json
{
  "code": "E101",
  "message": "Signature does not match your registered owner address",
  "statusCode": 400
}
```

### Test Case: Brand New Wallet (Created Today)

**User ID:** 411e7ddb-3e01-4293-8a52-de6132b53ada  
**Wallet ID:** 85afb1e2-2733-4734-9631-a57943729a22  
**Wallet Address:** 0x59Af28Aa10806d4b1f48a7758CbfC7f4b6ACdB71  
**Owner Key (our key vault):** 0x206FEdaeb5D376a118633Fb7997C1b5e33575dA3

### Wallet Creation Flow (executed today at 11:11 UTC)

1. ✅ Generated EVM keypair: `0x206FEdaeb5D376a118633Fb7997C1b5e33575dA3`
2. ✅ POST `/v1/users/{userId}/smart-wallets/owner-proof-challenges` - got challenge
3. ✅ Signed challenge with private key (EIP-191)
4. ✅ POST `/v1/users/{userId}/smart-wallets/create-managed` with:
   ```json
   {
     "currency": "CNGN",
     "userOwnerAddress": "0x206FEdaeb5D376a118633Fb7997C1b5e33575dA3",
     "ownerProofChallengeId": "7b9816df-faa7-469b-ae9c-8ca04a4b1957",
     "ownerProofSignature": "0x..."
   }
   ```
5. ✅ Response: 201 Created - wallet created successfully

### Transfer Attempt (fails at signature step)

1. ✅ POST `/v1/users/{userId}/smart-wallets/{walletId}/proposals` - proposal created
2. ✅ POST `/v1/users/{userId}/smart-wallets/proposals/{proposalId}/approve` - approved
3. ✅ GET `/v1/users/{userId}/smart-wallets/proposals/{proposalId}/sign-payload` - got EIP-712 data
4. ✅ Signed EIP-712 data with same private key
5. ❌ POST `/v1/users/{userId}/smart-wallets/proposals/{proposalId}/sign` - **SIGNATURE MISMATCH**

### Our Signing Implementation

```python
from eth_account import Account
from eth_account.messages import encode_typed_data

# EIP-712 payload from BMONI
structured_data = {
    "types": types,                    # From BMONI
    "primaryType": "CoinbaseSmartWalletMessage",  # From BMONI
    "domain": domain,                  # From BMONI
    "message": message                 # From BMONI
}

encoded_data = encode_typed_data(full_message=structured_data)
signed_data = account.sign_message(encoded_data)
signature = "0x" + signed_data.signature.hex()
```

### Verification Tests We Ran

✅ **Key vault address matches**: `0x206FEdaeb5D376a118633Fb7997C1b5e33575dA3`  
✅ **Signature recovery works**: Recovered address matches signing address  
✅ **EIP-712 structure correct**: Uses exact structure from BMONI response  
✅ **Primary type correct**: `CoinbaseSmartWalletMessage`  
❌ **BMONI rejects signature**: "does not match your registered owner address"

---

## The Problem

**BMONI must have registered a DIFFERENT owner address** than `0x206FEdaeb5D376a118633Fb7997C1b5e33575dA3`.

We cannot verify this because:
- GET `/v1/users/{userId}/smart-wallets/{walletId}` response does NOT include `userOwnerAddress`
- GET `/v1/users/{userId}/smart-wallets/account/wallets` response does NOT include owner address
- No API endpoint exposes the registered owner address

---

## Questions for BMONI Support

1. **What owner address is actually registered for wallet `85afb1e2-2733-4734-9631-a57943729a22`?**
   - Expected: `0x206FEdaeb5D376a118633Fb7997C1b5e33575dA3`
   - Please confirm what BMONI has

2. **Why doesn't the wallet API response include the owner address?**
   - We need to verify the owner address to debug signature issues
   - Can you add `userOwnerAddress` to wallet responses?

3. **Is there a specific way the signature must be formatted?**
   - We're using `eth_account` library's `sign_message` with `encode_typed_data`
   - Is there a different signing method required?

4. **Could the `create-managed` endpoint be ignoring the `userOwnerAddress` parameter?**
   - We pass it correctly but signatures never match
   - Is there server-side key generation happening?

---

## Additional Context

### Example EIP-712 Payload from BMONI

```json
{
  "domain": {
    "chainId": 84532,
    "name": "Coinbase Smart Wallet",
    "verifyingContract": "0x59Af28Aa10806d4b1f48a7758CbfC7f4b6ACdB71",
    "version": "1"
  },
  "types": {
    "CoinbaseSmartWalletMessage": [
      {"name": "hash", "type": "bytes32"}
    ]
  },
  "primaryType": "CoinbaseSmartWalletMessage",
  "message": {
    "hash": "0x4ee7cbd3058f930ae5188e23832de85fa14960c2db51554ddacfc6993221daa1"
  }
}
```

### Our Library Versions
- `eth-account`: 0.11.0
- Python: 3.11
- We use server-side signing (no SDK/browser)

---

## Impact

- **100% of transfers fail** with signature mismatch
- Cannot test or deploy our application
- Affects all users

## Request

Please urgently:
1. Check what owner address is registered for wallet `85afb1e2-2733-4734-9631-a57943729a22`
2. Explain why there's a mismatch
3. Provide guidance on correct signing implementation OR fix the wallet registration

**Contact:**  
Project: SabiSpend  
Email: support needed urgently

Thank you!
