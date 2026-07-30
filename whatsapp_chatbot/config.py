"""
SabiSpend Configuration
All endpoints and API keys are loaded from environment variables.
Update .env file to change API providers.
"""
import os
from dotenv import load_dotenv
load_dotenv()

# ======================================
# Main AI Services
# ======================================
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "")
AI_MODEL = os.getenv("AI_MODEL", "")

# Vision/OCR API (for invoice and receipt recognition)
VISION_API_URL = os.getenv("VISION_API_URL", "")
VISION_API_KEY = os.getenv("VISION_API_KEY", "")

# ======================================
# BMONI Integration
# !! UPDATE THESE IN .env WHEN YOU GET BMONI CREDENTIALS !!
# ======================================
BMONI_API_URL = os.getenv(
    "BMONI_BASE_URL",
    os.getenv("BMONI_API_URL", "https://embedded-dev.bmoni.com")
).rstrip("/")
BMONI_API_KEY = os.getenv("BMONI_API_KEY", "")
BMONI_SECRET_KEY = os.getenv("BMONI_SECRET_KEY", "")
BMONI_WEBHOOK_SECRET = os.getenv("BMONI_WEBHOOK_SECRET", "")

# ======================================
# Speech Services (Hausa)
# ======================================
HAUSA_STT_API_URL = os.getenv("HAUSA_STT_API_URL", "")
HAUSA_STT_FALLBACK_URL = os.getenv("HAUSA_STT_FALLBACK_URL", "")
HAUSA_TTS_BASE_URL = os.getenv("HAUSA_TTS_BASE_URL", "")
HAUSA_TTS_FALLBACK_URL = os.getenv("HAUSA_TTS_FALLBACK_URL", "")
HAUSA_TTS_MODEL = os.getenv("HAUSA_TTS_MODEL", "tts-1")
HAUSA_TTS_VOICE = os.getenv("HAUSA_TTS_VOICE", "female")

# ======================================
# Speech Services (Igbo)
# ======================================
IGBO_STT_API_URL = os.getenv("IGBO_STT_API_URL", "")
IGBO_STT_FALLBACK_URL = os.getenv("IGBO_STT_FALLBACK_URL", "")
IGBO_TTS_BASE_URL = os.getenv("IGBO_TTS_BASE_URL", "")
IGBO_TTS_FALLBACK_URL = os.getenv("IGBO_TTS_FALLBACK_URL", "")
IGBO_TTS_MODEL = os.getenv("IGBO_TTS_MODEL", "igbo-tts-model")
IGBO_TTS_VOICE = os.getenv("IGBO_TTS_VOICE", "female")

# ======================================
# Speech Services (Yoruba)
# ======================================
YORUBA_STT_API_URL = os.getenv("YORUBA_STT_API_URL", "")
YORUBA_STT_FALLBACK_URL = os.getenv("YORUBA_STT_FALLBACK_URL", "")
YORUBA_TTS_BASE_URL = os.getenv("YORUBA_TTS_BASE_URL", "")
YORUBA_TTS_FALLBACK_URL = os.getenv("YORUBA_TTS_FALLBACK_URL", "")
YORUBA_TTS_MODEL = os.getenv("YORUBA_TTS_MODEL", "yoruba-tts-model")
YORUBA_TTS_VOICE = os.getenv("YORUBA_TTS_VOICE", "female")

# ======================================
# Speech Services (English)
# ======================================
ENGLISH_STT_API_URL = os.getenv("ENGLISH_STT_API_URL", "")
ENGLISH_STT_FALLBACK_URL = os.getenv("ENGLISH_STT_FALLBACK_URL", "")
ENGLISH_TTS_BASE_URL = os.getenv("ENGLISH_TTS_BASE_URL", "")
ENGLISH_TTS_FALLBACK_URL = os.getenv("ENGLISH_TTS_FALLBACK_URL", "")
ENGLISH_TTS_MODEL = os.getenv("ENGLISH_TTS_MODEL", "nigerian-english-tts")
ENGLISH_TTS_VOICE = os.getenv("ENGLISH_TTS_VOICE", "female2")
