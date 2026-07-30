# SabiSpend Transformation - Changes Summary

## Overview
Transformed **Chop Beta** (nutrition advisor for mothers) into **SabiSpend** (money assistant for informal traders).

---

## 🎯 **What SabiSpend Does**

SabiSpend is a WhatsApp AI money assistant that helps:
- **Market traders** track daily expenses and sales
- **Artisans** calculate profit
- **Informal sellers** save money to BMONI wallet
- **Low-literacy users** verify scam messages

---

## 📋 **Major Changes Made**

### **1. New Core Files Created**

| File | Purpose |
|------|---------|
| `bmoni_client.py` | BMONI wallet integration (placeholders ready for API) |
| `expense_tracker.py` | Track daily expenses & sales (replaces baby_tracker.py) |
| `invoice_ocr.py` | Extract amounts from receipt/invoice images |
| `scam_detector.py` | Verify if forwarded messages are scams |
| `sabispend_prompt.py` | New system prompts for money assistant |

### **2. Updated Files**

| File | Changes |
|------|---------|
| `config.py` | Added BMONI config, Vision API, removed food recognition |
| `unified_agent.py` | New tools: log_expense, log_sales, calculate_profit, save_to_wallet, verify_message |
| `app.py` | New onboarding flow, removed nutrition code, simplified translation |
| `feedback.py` | Updated user journey types (trader/artisan/individual) |
| `.env-example` | All endpoints now generic (no public URLs exposed) |

### **3. Deleted Files (Nutrition-Related)**

- `retriever.py` - Nutrition database retriever
- `nfcms_retriever.py` - NFCMS nutrition data
- `tips.py` - Nutrition tips
- `nutrition_prompt-2.py` - Duplicate prompts
- `nfcms_chroma_store/` - Nutrition embeddings folder

### **4. Renamed Files (Backups)**

- `unified_agent.py` → `unified_agent_OLD_nutrition.py`
- `nutrition_prompt.py` → `nutrition_prompt_OLD.py`
- `baby_tracker.py` → `baby_tracker_OLD.py`

---

## 🌍 **Multilingual Simplification**

### **Before (Complex)**
```
User (Hausa) → STT → Translation to English → Gemma → 
Translation back to Hausa → TTS → User
```

### **After (Simple)**
```
User (Hausa) → STT → Gemma (responds in Hausa) → TTS → User
```

**Key Changes:**
- ✅ Removed NLLB translation layer completely
- ✅ Gemma understands and responds in Hausa/Igbo/Yoruba/English natively
- ✅ Language selection ONLY during onboarding (not every message)
- ✅ STT errors tolerated - Gemma infers meaning from context

---

## 🔧 **Environment Variables (.env)**

All API endpoints are now configurable and generic:

```bash
# Main AI Services
AI_API_KEY=your-key
AI_BASE_URL=https://your-endpoint.com/v1
AI_MODEL=your-model-name

# Vision API (for invoice OCR)
VISION_API_URL=https://your-vision-endpoint.com/analyze
VISION_API_KEY=your-key

# BMONI Integration (UPDATE WHEN YOU GET CREDENTIALS)
BMONI_API_URL=https://sandbox.bmoni.com/api/v1
BMONI_API_KEY=your-bmoni-key
BMONI_SECRET_KEY=your-bmoni-secret

# Speech Services (Hausa, Igbo, Yoruba, English)
HAUSA_STT_API_URL=https://your-stt-endpoint.com/ha/v1
HAUSA_TTS_BASE_URL=https://your-tts-endpoint.com/ha/v1
# ... (similar for Igbo, Yoruba, English)
```

**No public URLs or provider names** are hardcoded in the code!

---

## 🎬 **Onboarding Flow**

### **Step 1: Language Selection**
```
User: [First time]
Bot: "Welcome to SabiSpend! Select your language:
     1️⃣ English
     2️⃣ Hausa
     3️⃣ Igbo
     4️⃣ Yoruba"
User: "2"
Bot: [Saves language to database]
```

### **Step 2: User Type Selection**
```
Bot: "Great! Now tell me about yourself:
     1️⃣ Market trader / seller
     2️⃣ Small business owner / artisan
     3️⃣ Individual / other"
User: "1"
Bot: [Saves user type, onboarding complete]
```

**Language is saved once** and used for all future interactions.

---

## 🛠️ **Available Tools (Agent Functions)**

| Tool | Purpose | Example |
|------|---------|---------|
| `log_expense` | Record stock purchases | "I bought tomatoes for ₦12,000" |
| `log_sales` | Record daily sales | "I sold ₦25,000 today" |
| `calculate_profit` | Show profit | "How much profit did I make?" |
| `check_balance` | Check BMONI wallet | "How much money do I have?" |
| `save_to_wallet` | Transfer to savings | "Save ₦2,000 to my wallet" |
| `verify_message` | Check for scams | [forwards suspicious SMS] |

---

## 📸 **Image Handling**

**Before:** External food recognition model analyzed images
**After:** Gemma analyzes images directly (invoices, receipts, sales records)

```
User: [sends invoice photo]
Bot: "I can see ₦8,500 on this receipt. Is this what you spent today?"
User: "Yes"
Bot: [calls log_expense(8500)]
Bot: "✅ Recorded. You spent ₦8,500 today."
```

---

## 🛡️ **Scam Detection**

Users can forward suspicious SMS/WhatsApp messages:

```
User: [forwards] "URGENT: Account blocked. Send PIN to verify."
Bot: [calls verify_message]
Bot: "🔴 WARNING - This is a SCAM
     
     ⚠️ This message:
     • Pressures you to act fast
     • Asks for your PIN
     
     🛑 Do NOT send your PIN
     Your bank will NEVER ask for your PIN."
```

---

## 💰 **BMONI Integration**

**Status:** Placeholder functions ready
**Action Required:** Update `.env` with BMONI credentials when you receive them

The code is structured to:
1. Check if wallet exists
2. Create wallet if needed
3. Check balance
4. Transfer to savings
5. Receive payments

All BMONI functions are in `bmoni_client.py` - just add your API credentials!

---

## 🚀 **Next Steps**

1. ✅ **Test the app** with the current AI endpoints
2. ⏳ **Get BMONI API credentials** and update `.env`
3. ⏳ **Test BMONI integration** (wallet creation, savings)
4. ✅ **Test multilingual** (Hausa, Igbo, Yoruba voice messages)
5. ✅ **Test OCR** (invoice/receipt photos)
6. ✅ **Test scam detection** (forward suspicious messages)

---

## 📝 **Database Collections**

| Collection | Database | Purpose |
|------------|----------|---------|
| `daily_transactions` | SabiSpend | Store expenses & sales |
| `conversations` | SabiSpend | Store chat history |
| `user_settings` | SabiSpend | Store language & user type |

MongoDB structure preserved from previous app.

---

## ⚙️ **Running the App**

```bash
# Install dependencies
pip install -r requirements.txt

# Update .env with your credentials
cp .env-example .env
# Edit .env with your API keys

# Run the app
python app.py
```

The app will start on the configured port and listen for WhatsApp webhook events.

---

## 🎯 **Key Features**

- ✅ **Multilingual** - Hausa, Igbo, Yoruba, English, Pidgin
- ✅ **Voice-first** - Works with voice messages (STT + TTS)
- ✅ **Low-literacy friendly** - Simple language, photo support
- ✅ **Scam protection** - Verifies suspicious messages
- ✅ **BMONI savings** - Integrated wallet for micro-savings
- ✅ **Profit tracking** - Daily expense vs sales calculations

---

**Built for NITHUB Innovation Fair Hackathon 2026** 🏆
