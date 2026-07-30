# BMONI database implementation status

The BMONI lifecycle database described in the technical integration guide is
implemented in `bmoni_store.py` using MongoDB database `SabiSpend` and collection
`bmoni_accounts`.

## Persisted record

One document is kept per WhatsApp phone number. It can contain:

- `phone_number` and `bmoni_user_id`
- `wallet.id`, `wallet.address`, and wallet currency
- KYC and Nigeria-onboarding status (never raw document images or a BVN)
- registered withdrawal account metadata
- withdrawal proposal IDs and their latest statuses
- lifecycle and audit timestamps

The EVM private key and signatures are never stored by the backend.

## Duplicate protection

Unique indexes protect `phone_number`, `bmoni_user_id`, and `wallet.id`. User
creation first atomically reserves the phone number. If the remote request times
out, the reservation remains for reconciliation rather than risking a second
BMONI user and forked wallet history.

## Configuration

Set:

```env
MONGO_URI=<MongoDB connection string>
BMONI_BASE_URL=https://embedded-dev.bmoni.com
BMONI_API_KEY=<sandbox key>
```

Install `requirements.txt` before starting the application. Startup/import creates
the indexes when MongoDB is reachable.

## Still external to the database

The signer web page must generate and retain the owner key on the user's device.
The backend client now implements the challenge, managed-wallet, KYC, onboarding,
bank-account, offramp proposal, signing, and proposal-status endpoints, but live
end-to-end verification requires BMONI sandbox credentials and a reachable MongoDB.
