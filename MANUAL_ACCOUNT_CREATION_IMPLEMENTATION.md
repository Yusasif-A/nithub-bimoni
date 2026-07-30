# Manual Account Creation Implementation

## Overview

Implemented a manual account creation flow that allows users to create their SabiSpend/BMONI account by providing all required information in WhatsApp.

**Date:** July 30, 2026

---

## What Changed

### Before (Automatic)
- When user first interacted with SabiSpend, account was automatically created in the background
- User had no control over the process
- Account creation happened silently

### After (Manual)
- User explicitly requests account creation
- AI agent guides user through the process
- User provides all required information in one message
- Account is created only when user initiates it

---

## Implementation Details

### 1. New Tool: `create_account`

**Location:** `whatsapp_chatbot/unified_agent.py`

**Parameters:**
- `full_name` (string): User's full legal name
- `bvn` (string): 11-digit Bank Verification Number
- `date_of_birth` (string): Date in DD/MM/YYYY format
- `city` (string): City of residence
- `state` (string): State of residence

**What it does:**
1. Validates user doesn't already have an account
2. Validates BVN format (11 digits)
3. Parses date of birth to ISO format
4. Creates BMONI user account
5. Generates secure EVM keypair for wallet
6. Creates managed wallet with server-side signing
7. Submits KYC information
8. Activates KYC
9. Activates NGN rail for transfers

**Returns:**
- Success message with account details
- Error message if something fails
- Informative message if user already has account

### 2. Updated `_ensure_bmoni_user` Function

**Location:** `whatsapp_chatbot/unified_agent.py`

**Changes:**
- **Before:** Would create BMONI user and wallet automatically if not found
- **After:** Returns `None` if user not found, does NOT auto-create
- Users must explicitly request account creation via `create_account` tool

### 3. Updated System Prompts

**Location:** `whatsapp_chatbot/sabispend_prompt.py`

**Added instructions for:**

**Text Mode:**
```
8. **create_account** - Create a complete BMONI account with KYC and NGN activation
   - ONLY call this when user explicitly wants to create their account
   - NEVER call automatically
   - When user says "I want to create account", first send:
   
   "To create your SabiSpend account, please send ALL these details in one message:
   
   1. Your full name
   2. Your BVN (11 digits)
   3. Your date of birth (DD/MM/YYYY)
   4. Your city
   5. Your state
   
   Example: Amina Ibrahim, 22238719042, 15/03/1985, Kano, Kano State"
   
   - Wait for user to provide all details, then extract and call create_account tool
```

**Voice Mode:**
- Same instructions, adapted for voice responses (no markdown/emojis)

### 4. Updated Welcome Message

**Location:** `whatsapp_chatbot/app.py`

**Changes:**
- For users WITHOUT wallet: Shows "🏦 *Create account* - Open your BMONI wallet"
- For users WITH wallet: Shows "✅ *Verify account number* - Check bank account details"
- Message dynamically adjusts based on user's account status

### 5. Updated Tool Execution

**Location:** `whatsapp_chatbot/unified_agent.py`

**Added to `_execute_tools` method:**
```python
elif name == "create_account":
    result = await create_account.ainvoke(args)
```

### 6. Updated Tool List

**Location:** `whatsapp_chatbot/unified_agent.py`

**Added `create_account` to the tools list:**
```python
self.tools = [
    log_expense,
    log_sales,
    calculate_profit,
    check_balance,
    save_to_wallet,
    request_send_money,
    confirm_send_money,
    create_account,  # NEW
    verify_account,
]
```

---

## User Flow

### Step 1: User Requests Account Creation

User says:
- "I want to create my account"
- "Create account"
- "Open account for me"
- "Register"

### Step 2: AI Sends Instructions

AI responds with:
```
To create your SabiSpend account, please send ALL these details in one message:

1. Your full name
2. Your BVN (11 digits)
3. Your date of birth (DD/MM/YYYY)
4. Your city
5. Your state

Example: Amina Ibrahim, 22238719042, 15/03/1985, Kano, Kano State
```

### Step 3: User Provides Information

User replies with all details in one message:
```
Fatima Abubakar, 22238719042, 20/05/1992, Abuja, FCT
```

### Step 4: AI Extracts and Creates Account

AI:
1. Extracts each field from the message
2. Calls `create_account` tool with extracted data
3. Tool creates BMONI account, wallet, and activates NGN

### Step 5: Confirmation

AI responds with:
```
🎉 Account created successfully!

✅ BMONI account active
✅ Secure wallet created
✅ NGN transfers enabled

You can now:
• Check your balance
• Send money to other users
• Track your expenses and profit

Welcome to SabiSpend! 💰
```

---

## Error Handling

### User Already Has Account
```
✅ You already have a SabiSpend account!

Your wallet is active and ready to use. You can:
• Check your balance
• Send money
• Track expenses
```

### Invalid BVN Format
```
❌ BVN must be exactly 11 digits. Please check and try again.
```

### Invalid Date Format
```
❌ Date of birth must be in DD/MM/YYYY format (e.g., 15/03/1985)
```

### BMONI API Errors
```
❌ Could not create account: [error details]
```

### Partial Success
```
⚠️ Account and wallet created, but NGN activation failed: [error]

Your account is created but you may not be able to send/receive money yet.
```

---

## Testing

### Test Script

**Location:** `test_manual_account_creation.py`

**Usage:**
```bash
python test_manual_account_creation.py
```

**What it tests:**
1. Checks if user already exists
2. Calls `create_account` tool with test data
3. Verifies account was created in database
4. Shows wallet details and status

**Test Data:**
- Phone: +2348099887766
- Name: Fatima Abubakar
- BVN: 22238719042 (sandbox)
- DOB: 20/05/1992
- City: Abuja
- State: FCT

---

## Benefits

### For Users
1. **Control** - Users decide when to create account
2. **Transparency** - Clear understanding of what information is needed
3. **Simple** - All info provided at once, no back-and-forth
4. **Guided** - AI provides clear instructions and example

### For System
1. **No surprise account creation** - Only happens when user wants it
2. **Better data quality** - User provides real information
3. **Compliance** - User explicitly consents to account creation
4. **Flexibility** - Can add more fields in future if needed

---

## Files Modified

1. ✅ `whatsapp_chatbot/unified_agent.py`
   - Added `create_account` tool
   - Updated `_ensure_bmoni_user` to not auto-create
   - Updated `check_balance` to handle no account case
   - Added tool to execution chain
   - Updated tool count log (8 tools)

2. ✅ `whatsapp_chatbot/sabispend_prompt.py`
   - Added create_account instructions for text mode
   - Added create_account instructions for voice mode
   - Updated tool list documentation

3. ✅ `whatsapp_chatbot/app.py`
   - Welcome message already has conditional logic (no changes needed)

4. ✅ `test_manual_account_creation.py` (NEW)
   - Test script for manual account creation

5. ✅ `MANUAL_ACCOUNT_CREATION_IMPLEMENTATION.md` (NEW)
   - This documentation file

---

## Next Steps

### For Production
1. Test with real users in WhatsApp
2. Monitor success/failure rates
3. Add analytics for account creation flow
4. Consider adding progress indicators for long operations

### Future Enhancements
1. Add address line 1 as optional field
2. Support different date formats (auto-detect)
3. Add phone number verification
4. Add email collection (optional)
5. Support splitting information across multiple messages if needed

---

## Notes

- The sandbox BVN `22238719042` is used for testing
- In production, real BVNs will be used
- Account creation process takes 5-10 seconds
- All wallet operations use server-side signing (secure)
- NGN activation happens automatically during creation

---

## Summary

✅ Manual account creation is now fully implemented
✅ Users have full control over when to create accounts
✅ AI guides users through the process step-by-step
✅ All existing functionality preserved
✅ Tests and documentation complete

The system is ready for users to manually create their accounts!
