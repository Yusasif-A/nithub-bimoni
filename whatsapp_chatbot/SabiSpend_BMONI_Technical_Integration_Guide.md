# SabiSpend — BMONI Technical Integration Guide

**For:** The engineer building the SabiSpend backend
**Purpose:** How SabiSpend's WhatsApp bot, its AI layer, and BMONI's sandbox API fit together — the exact call order, who calls what, and where signing happens.
**Sandbox base URL:** `https://embedded-dev.bmoni.com` (no trailing `/v1` — paths already include it)

---

## 1. System overview

SabiSpend has four moving parts:

| Component | Role |
|---|---|
| **WhatsApp Business API** (Meta Cloud API / Twilio) | Receives text, photos, voice notes from the user; sends back text/voice replies |
| **SabiSpend backend** | Holds the BMONI `x-api-key`; runs the AI; calls BMONI REST endpoints; never lets the API key reach the user's device |
| **AI layer (LLM + OCR + STT/TTS)** | Interprets photos/voice, decides which BMONI endpoint to call (function/tool calling), narrates results back in the user's language |
| **Signer web page** (lightweight, mobile-friendly) | The *only* piece that touches private keys — used once at wallet creation, and again each time money moves out |

```
User (WhatsApp) ⇄ WhatsApp API ⇄ SabiSpend Backend ⇄ BMONI Sandbox API
                                        │
                                        ├── AI (decides which endpoint to call, reads results, replies by voice)
                                        │
                                        └── Signer web page (opened via a link, only for wallet creation & withdrawals)
```

**Golden rule from BMONI's docs:** *"Calls can fail when this order is not followed."* Every step below must happen in sequence — nothing can be skipped or reordered.

---

## 2. Authentication

Every request to BMONI carries two headers:

```
x-api-key: <BMONI_SANDBOX_API_KEY>
Content-Type: application/json
```

**Rules:**
- The key lives only in the backend's environment variables. It is never sent to WhatsApp, the signer web page, the frontend, or any LLM prompt.
- Store as:
  ```
  BMONI_BASE_URL=https://embedded-dev.bmoni.com
  BMONI_API_KEY=<provided-sandbox-key>
  ```
- All BMONI calls are proxied through the SabiSpend backend. Nothing external calls BMONI directly.

---

## 3. The fixed lifecycle

```
Create user → Create wallet (signing) → KYC → Activate NGN rail → Fund wallet → Read / Move money (signing)
```

| Stage | Who calls it | Needs signing? |
|---|---|---|
| 1. Create user | Backend | No |
| 2. Create smart wallet | Signer web page (+ backend) | **Yes — on-device** |
| 3. KYC wizard | Backend | No |
| 4. Activate NGN rail | Backend | No |
| 5. Fund wallet | User (bank transfer) / Backend reads | No |
| 6. Read balances/transactions | Backend + AI | No |
| 7. Move money out (withdraw) | Signer web page (+ backend) | **Yes — on-device** |

Signing only happens in two places in the entire flow. Everything else is a normal server-to-server REST call.

---

## 4. Step-by-step technical flow

### Step 1 — Create the user

**Caller:** Backend, triggered the first time a new phone number messages the WhatsApp bot.

```
POST /v1/users
x-api-key: <key>
Content-Type: application/json

{
  "firstName": "Test",
  "email": "unique-email@example.com",
  "phoneNumber": "+2348012345678"
}
```

- Use the WhatsApp sender's phone number.
- Generate a unique placeholder email per user if none is collected.
- **Save the returned `bmoniUserId` against that phone number in your own database.** Every later call is scoped to it. Never re-create a user for a returning number — it forks their wallet history.

---

### Step 2 — Create the smart wallet (the signing step)

This is the one part of the flow that cannot happen inside the WhatsApp chat itself, because it requires generating an EVM keypair and signing a challenge with it. BMONI's own SDKs (Flutter, React Native) do this on-device; SabiSpend instead does it on a small web page, since there's no WhatsApp-native equivalent.

**Flow:**

1. Backend sends the user a one-time link via WhatsApp: *"Tap here to set up your secure wallet: [link]"*
2. **Signer web page loads** and generates an EVM keypair client-side (e.g. via `ethers.js` or `viem`). The private key stays in the browser session — it is never sent to the backend.
3. Signer page calls (through the backend, which attaches the API key):

```
POST /v1/users/:userId/smart-wallets/owner-proof-challenges
{
  "currency": "CNGN",
  "userOwnerAddress": "0x..."
}
```

4. BMONI returns an EIP-191 message + `challengeId`. The signer page signs the exact message with the same key that produced `userOwnerAddress`.
5. Signer page (via backend) calls:

```
POST /v1/users/:userId/smart-wallets/create-managed
{
  "currency": "CNGN",
  "userOwnerAddress": "0x...",
  "ownerProofChallengeId": "...",
  "ownerProofSignature": "0x..."
}
```

6. BMONI deploys the smart wallet and returns its ID + address. **Save both** — you'll need them for KYC activation and for every wallet-scoped call afterward.
7. Signer page shows "Wallet ready" and can close; the user returns to WhatsApp.

> **Note:** BMONI only officially documents this signing flow through its Flutter/React Native SDKs. Doing it via a plain web page using a standard EVM signing library should work, since the backend only validates the signature against the address — but it is not something BMONI has explicitly signed off on. Confirm this with BMONI's technical team before relying on it for the demo, and treat browser-held keys as lower-security than a phone's secure element.

---

### Step 3 — KYC wizard (sandbox)

**Caller:** Backend, fully conversational through WhatsApp — user answers questions by text/voice, AI fills the fields.

Fixed order:

1. `GET /v1/users/:userId/kyc/options`
2. `GET /v1/users/:userId/kyc/occupations?search=...`
3. `POST /v1/users/:userId/kyc/documents/identification` (multipart: ID photo + `type`, `documentNumber`, `issuingCountry`)
4. `POST /v1/users/:userId/kyc/documents/proof-of-address` (multipart)
5. `PATCH /v1/users/:userId/kyc` — personal + address + employment + compliance. Use sandbox test values:
   - `bvn`: `22222222222`
   - Country code: `NGA`
6. `GET /v1/users/:userId/kyc/readiness`
7. `POST /v1/users/:userId/kyc/activate` — **omit `sumsubLevelName` for Nigeria** (it's required for USD/EUR only)

> Never submit a real BVN, NIN, or passport in sandbox testing — always the test BVN above.

---

### Step 4 — Activate the NGN rail

```
POST /v1/users/:userId/onboarding/start-nigeria
{
  "bvn": "22222222222",
  "ngnWalletAddress": "0x...",   // from Step 2
  "ngnWalletIndex": 0
}
```

Confirm activation:

```
GET /v1/users/:userId/onboarding/status
```

Wait for the NGN currency to report `active` before funding or reading balances.

---

### Step 5 — Fund the wallet

```
GET /v1/users/:userId/bank-accounts/deposit-accounts/NGN
```

Returns the virtual account number. The bot sends this to the user by WhatsApp text/voice ("send your savings to this account number") — a normal bank transfer lands here and is credited to the wallet as CNGN automatically. No signing involved.

For sandbox test funds: give BMONI's team the same phone number used in Step 1; they credit ₦1,000 / $10 test funds manually during the hackathon.

---

### Step 6 — Read wallet data (the AI's main job)

These are safe, no-signing GET calls the AI calls directly in response to natural-language requests:

| User says (voice/text) | AI calls | 
|---|---|
| "How much do I have?" | `GET /v1/users/:userId/smart-wallets/account/balances` |
| "Show my recent activity" | `GET /v1/users/:userId/smart-wallets/account/transactions` |
| "What's my wallet number?" | `GET /v1/users/:userId/smart-wallets/account/wallets` |

The AI receives the JSON, converts it into a short, plain-language sentence in the user's chosen language (English/Pidgin/Hausa/Igbo/Yoruba), and sends it back as a voice note via WhatsApp.

This is where "AI + BMONI" is most visible: the AI is not decorative — it is the thing deciding which endpoint to call and turning raw JSON into something a low-literacy user can actually understand and act on.

---

### Step 7 — Move money out (withdrawal — the second signing step)

1. User (or AI, acting on a stated intent like "send ₦5,000 to my GTBank account") triggers withdrawal setup:
   ```
   GET /v1/users/:userId/bank-accounts/nigerian-banks
   POST /v1/users/:userId/bank-accounts/verify-nigerian-account
   { "accountNumber": "0123456789", "bankCode": "058" }
   POST /v1/users/:userId/bank-accounts/withdrawal-accounts/nigeria
   { "accountNumber": "...", "bankCode": "...", "bankName": "...", "accountHolderName": "..." }
   ```
   None of this needs signing — it's just registering the destination account. Save the returned `id` as `bankAccountId`.

2. Create the offramp proposal:
   ```
   POST /v1/users/:userId/smart-wallets/:smartWalletId/offramp/nigeria
   { "bankAccountId": "...", "fromAmount": "100.00" }
   ```
   This returns a **proposal**, not a completed payout (`status: "PENDING_APPROVALS"`).

3. Backend sends the user a signing link via WhatsApp (same signer web page as Step 2, same stored key).

4. Signer page fetches and signs:
   ```
   GET  /v1/users/:userId/smart-wallets/proposals/:proposalId/sign-payload
   POST /v1/users/:userId/smart-wallets/proposals/:proposalId/sign
   ```
   Signed with the **same owner key** created in Step 2 — this is why that key must be kept around (in the browser session or wherever your signer page persists it), not thrown away after wallet creation.

5. Backend polls:
   ```
   GET /v1/users/:userId/smart-wallets/proposals/:proposalId
   ```
   until `status` becomes `COMPLETED`, then the AI voice-replies "Done — ₦5,000 sent to your GTBank account."

---

## 5. Where the AI plugs in (function-calling layer)

Give the LLM a small, fixed toolset — do not let it construct arbitrary API calls:

```
get_balance(userId)
get_transactions(userId)
get_deposit_account(userId)
start_withdrawal(userId, bankAccountId, amount)
check_withdrawal_status(userId, proposalId)
check_message_for_scam(messageText)      // pure AI, no BMONI call
estimate_profit(costPhoto, salesPhoto)   // pure AI, no BMONI call
```

The backend implements each function as a thin wrapper around the corresponding BMONI endpoint (attaching the API key, handling errors). The LLM only ever sees function names, parameters, and results — never the raw API key or endpoint URLs.

---

## 6. Error handling & gotchas (from BMONI's docs)

- **Never add `/v1` to `BMONI_BASE_URL`** — paths already include it; doing so causes `/v1/v1/...` 404s.
- **Smart-wallet calls use the stablecoin code, not the fiat code** — `CNGN` for NGN, not `NGN`.
- **KYC submit order is fixed** — uploads → `PATCH /kyc` → `/readiness` → `/activate` → `start-nigeria`. Reordering returns validation errors.
- **NGN and CAD omit `sumsubLevelName`** on `/kyc/activate`; USD/EUR require it.
- **`verify-nigerian-account` returning 404** means the account number doesn't match that bank code — surface this to the user and let them re-enter it, don't retry silently.
- **Persist `bmoniUserId` and the wallet address/ID** the moment you get them — recreating a user or wallet forks history.
- **Signature must come from the same key** used at wallet creation — if your signer page ever regenerates a fresh keypair for the same user, subsequent signed actions will fail.

---

## 7. Security notes

- BMONI API key: backend environment variable only. Never in the signer page's client-side code, never in WhatsApp message content, never in logs shown to users.
- Sandbox BVN `22222222222` only — never a real participant's identity document.
- Don't pass BVNs, document images, or the API key into any LLM prompt — the AI only needs the *results* of BMONI calls (balances, statuses), never the credentials used to fetch them.
- Treat the signer page's in-browser key as demo-grade. For anything beyond the hackathon, this is the piece to redesign properly (e.g. migrating to BMONI's native SDK inside a real companion app, or a hardened key-custody approach).

---

## 8. Minimum build order (suggested week-by-week)

1. Backend skeleton + WhatsApp webhook (text/image/voice in and out)
2. `POST /v1/users` wired up, phone number → `bmoniUserId` mapping stored
3. Signer web page: keypair generation + owner-proof-challenge + create-managed
4. KYC wizard wired end-to-end with sandbox BVN
5. `start-nigeria` + deposit account read-back → confirm test funds land
6. AI function-calling layer: balance/transactions read + voice reply
7. Profit estimation + scam-check AI features (no BMONI dependency, can be built in parallel with anything above)
8. Withdrawal flow: registration → proposal → signer page → status polling
