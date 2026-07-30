# SabiSpend - Quick Start Guide

## 🚀 Setup in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the example file and edit with your credentials:
```bash
copy .env-example .env
```

**Edit `.env` and add:**
- Your AI model credentials (API_KEY, AI_BASE_URL, AI_MODEL)
- WhatsApp credentials (WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID)
- MongoDB connection string (MONGO_URI)
- Speech services (STT/TTS endpoints for each language)

**For BMONI:** Add credentials when you receive them:
```
BMONI_API_URL=https://sandbox.bmoni.com/api/v1
BMONI_API_KEY=your-key
BMONI_SECRET_KEY=your-secret
```

### 3. Run the App
```bash
python app.py
```

---

## 📱 **Testing with WhatsApp**

### **Onboarding (First Time User)**
1. Send "Hi" to your WhatsApp bot
2. Select language (1-4)
3. Select user type (1-3)
4. Start using!

### **Recording Expenses**
- **Text:** "I bought tomatoes for 12000 naira"
- **Voice:** Say the same in any language
- **Photo:** Send receipt/invoice photo

### **Recording Sales**
- **Text:** "I sold 25000 today"
- **Voice:** Say it in your language

### **Check Profit**
- **Text:** "How much profit did I make?"
- Bot shows: Expenses, Sales, Profit, Suggested Savings

### **Save Money**
- **Text:** "Save 2000 to my wallet"
- Bot transfers to BMONI savings

### **Check Scam**
- Forward any suspicious SMS/WhatsApp message
- Bot analyzes and tells you if it's a scam

---

## 🌍 **Multilingual Testing**

The bot responds in the **same language** you speak:

**Hausa Example:**
```
You: "Na sayi tumatur da naira dubu goma sha biyu"
Bot: "✅ An rubuta. Ka kashe naira dubu goma sha biyu..."
```

**Yoruba Example:**
```
You: "Mo ta ẹgbẹrun mẹẹẹdọgbọn loni"
Bot: "🎉 O dara! O ta ẹgbẹrun mẹẹẹdọgbọn..."
```

**English Example:**
```
You: "I bought rice for 15,000"
Bot: "✅ Recorded. You spent ₦15,000 on rice today."
```

---

## 🐛 **Troubleshooting**

### **Bot not responding?**
- Check WhatsApp webhook is configured
- Verify WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env
- Check logs for errors

### **Voice messages not working?**
- Verify STT endpoints in .env
- Check STT_API_URL for each language
- Test with English first (simpler)

### **Images not processing?**
- Verify VISION_API_URL in .env
- Check image download in logs
- Test with clear receipt photos

### **BMONI not working?**
- Check if BMONI_API_KEY is set
- Verify BMONI_API_URL is correct
- Check BMONI API documentation for correct endpoints

---

## 📊 **Monitoring**

### **Check Logs**
The app logs everything:
- `✅` = Success
- `⚠️` = Warning
- `❌` = Error
- `🎙️` = Voice processing
- `📸` = Image processing
- `💰` = Money operations

### **Database Collections**
Check MongoDB:
- `SabiSpend.daily_transactions` - All expenses & sales
- `SabiSpend.conversations` - Chat history
- `SabiSpend.user_settings` - User language & type

---

## 🎯 **Demo Script**

### **For Hackathon Demo:**

1. **Intro** (30 sec)
   "This is SabiSpend - an AI money assistant for market traders who may not read or write well."

2. **Onboarding** (30 sec)
   - Show language selection
   - Show user type selection
   
3. **Track Expense** (1 min)
   - Send receipt photo OR say "I bought stock for 12,000"
   - Show confirmation

4. **Track Sales** (1 min)
   - Say "I sold 25,000 today"
   - Bot calculates profit automatically
   - Bot suggests savings

5. **Scam Detection** (1 min)
   - Forward fake bank alert
   - Bot warns: "This is a SCAM"

6. **Multilingual** (1 min)
   - Switch to Hausa/Yoruba
   - Show it responds in same language

7. **BMONI Integration** (1 min)
   - "Save 2000 to wallet"
   - Show wallet balance

**Total:** 6-7 minutes

---

## 🔗 **Important Files**

| File | What It Does |
|------|--------------|
| `app.py` | Main WhatsApp webhook handler |
| `unified_agent.py` | AI agent with tools |
| `sabispend_prompt.py` | System prompts |
| `bmoni_client.py` | BMONI wallet integration |
| `expense_tracker.py` | Expense & sales tracking |
| `scam_detector.py` | Message verification |
| `invoice_ocr.py` | Receipt/invoice OCR |

---

## 💡 **Tips**

1. **Test locally first** before deploying
2. **Use ngrok** to expose localhost for WhatsApp webhook
3. **Check logs** if something doesn't work
4. **Start with English** before testing other languages
5. **Have clear receipt photos** ready for demo
6. **Prepare fake scam messages** for demo

---

## 📞 **Support**

If you encounter issues:
1. Check the logs for error messages
2. Verify all environment variables are set
3. Test each component individually (STT, TTS, OCR, BMONI)
4. Check MongoDB connection

---

**Good luck with the hackathon!** 🏆
