import base64
import re
import glob
import shutil
import httpx
from io import BytesIO
from typing import Dict, List, Any
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from hmac_validator import validate_whatsapp_hmac
import os
import logging
from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager
import tempfile
import json


_ffmpeg_cache = None

def _find_ffmpeg():
    """Find ffmpeg/ffprobe including winget installations. Result is cached after first call."""
    global _ffmpeg_cache
    if _ffmpeg_cache is not None:
        return _ffmpeg_cache
    # 1. Try process PATH
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg:
        _ffmpeg_cache = (ffmpeg, ffprobe)
        return _ffmpeg_cache
    # 2. Deep search all winget Packages (handles any package ID suffix)
    appdata = os.environ.get("LOCALAPPDATA", "C:\\Users\\USER\\AppData\\Local")
    packages_dir = os.path.join(appdata, "Microsoft", "WinGet", "Packages")
    for ff in glob.glob(os.path.join(packages_dir, "**", "ffmpeg.exe"), recursive=True):
        probe = ff.replace("ffmpeg.exe", "ffprobe.exe")
        ff_dir = os.path.dirname(ff)
        os.environ['PATH'] = os.environ.get('PATH', '') + os.pathsep + ff_dir
        logger.info(f"Found ffmpeg at: {ff}")
        _ffmpeg_cache = (ff, probe if os.path.exists(probe) else None)
        return _ffmpeg_cache
    logger.warning("ffmpeg not found — MP3 concat will fall back to raw join")
    _ffmpeg_cache = (None, None)
    return _ffmpeg_cache


def _concat_mp3_chunks(chunks: list) -> bytes:
    """Concatenate MP3 chunks into a single valid MP3 using pydub."""
    if not chunks:
        return b""
    if len(chunks) == 1:
        return chunks[0]
    try:
        from pydub import AudioSegment
        ffmpeg_path, ffprobe_path = _find_ffmpeg()
        if ffmpeg_path:
            AudioSegment.converter = ffmpeg_path
            if ffprobe_path:
                AudioSegment.ffprobe = ffprobe_path
        combined = AudioSegment.empty()
        for chunk in chunks:
            combined += AudioSegment.from_mp3(BytesIO(chunk))
        out = BytesIO()
        combined.export(out, format="mp3")
        return out.getvalue()
    except Exception as e:
        logger.warning(f"⚠️ pydub concat failed ({e}), using raw join")
        return b"".join(chunks)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

from services import get_stt_service, get_tts_service, get_translator
from nllb_translator import yoruba_numbers_to_words

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.error_alerter import send_error_alert

AGENT_MICROSERVICE_URL = os.getenv("AGENT_MICROSERVICE_URL", "http://localhost:8003")

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")

from config import (
    HAUSA_TTS_VOICE, IGBO_TTS_VOICE, YORUBA_TTS_VOICE, ENGLISH_TTS_VOICE
)

if not all([WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN]):
    logger.error("Missing one or more required WhatsApp environment variables.")
    exit(1)

from feedback import (
    store_feedback, store_pending_response, get_pending_response,
    get_user_language, set_user_language
)

logger.info("🚀 Starting WhatsApp Voice Retriever Agent")
_find_ffmpeg()  # Cache ffmpeg path at startup

from redis_dedup import is_duplicate as _is_duplicate

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the FastAPI app and initialize components."""
    
    logger.info("=" * 60)
    logger.info("🚀 Starting WhatsApp Agent")
    logger.info("=" * 60)
    
    try:
        # ✅ NEW: Test agent microservice connection
        logger.info(f"Testing connection to agent microservice: {AGENT_MICROSERVICE_URL}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                health = await client.get(f"{AGENT_MICROSERVICE_URL}/health")
                if health.status_code == 200:
                    health_data = health.json()
                    logger.info(f"✅ Agent microservice connected!")
                    logger.info(f"   Status: {health_data.get('status')}")
                    logger.info(f"   Agent: {health_data.get('agent_status')}")
                else:
                    logger.warning(f"⚠️ Agent microservice returned status {health.status_code}")
            except Exception as e:
                logger.error(f"❌ Cannot connect to agent microservice: {e}")
                logger.error(f"   Make sure agent_microservice.py is running on {AGENT_MICROSERVICE_URL}")
                raise Exception("Agent microservice not available")
        
        # The speech modules are now handled via the services.py layer
        
        logger.info("=" * 60)
        logger.info("✅ WhatsApp Agent Ready!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        raise

    yield

    # Shutdown
    logger.info("Cleaning up components...")
    logger.info("✅ Cleanup completed!")


# FastAPI app with lifespan management
app = FastAPI(
    title="WhatsApp Voice Retriever Agent",
    lifespan=lifespan
)

async def download_media(media_id: str) -> bytes:
    """Download media from WhatsApp."""
    media_metadata_url = f"https://graph.facebook.com/v20.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

        if not download_url:
            raise HTTPException(status_code=404, detail="Media URL not found.")

        media_response = await client.get(download_url, headers=headers)
        media_response.raise_for_status()
        return media_response.content

def convert_to_data_uri(media_bytes: bytes, mime_type: str) -> str:
    """Convert media bytes to data URI for the agent."""
    b64_data = base64.b64encode(media_bytes).decode()
    return f"data:{mime_type};base64,{b64_data}"

def clean_whatsapp_message(text: str) -> str:
    """Clean up markdown formatting for WhatsApp display."""
    if not text:
        return text
        
    # 1. Convert headers (### Header) to bold (*Header*)
    # Standardize headers to WhatsApp bold
    text = re.sub(r'^#+\s+(.*)$', r'*\1*', text, flags=re.MULTILINE)
    
    # 2. Convert standard markdown bold (**text**) to WhatsApp bold (*text*)
    text = text.replace('**', '*')
    
    # 3. Handle bullet points - convert '*' or '-' at start of line to '•'
    # This prevents them from being interpreted as the start of a bold tag
    text = re.sub(r'^[*-]\s+', r'• ', text, flags=re.MULTILINE)
    
    # 4. Handle horizontal rules
    text = re.sub(r'^---+$', r'────────────────', text, flags=re.MULTILINE)
    
    return text.strip()

async def upload_media_to_whatsapp(media_content: bytes, mime_type: str) -> str:
    """Upload media to WhatsApp servers and return media ID."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    # Create a temporary file for upload
    temp_file_path = ""
    try:
        # WhatsApp accepts audio/mpeg (MP3), audio/ogg (OGG with opus codec), audio/amr, audio/mp4
        # Use .mp3 extension for audio/mpeg
        suffix = ".mp3" if "audio" in mime_type else ".png"
        
        logger.info(f"Preparing to upload media: {len(media_content)} bytes, type: {mime_type}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(media_content)
            temp_file_path = temp_file.name
        
        logger.info(f"Created temp file: {temp_file_path}")

        # The 'with' block has now closed the file, making it safe to re-open.
        with open(temp_file_path, "rb") as temp_file_to_upload:
            # For WhatsApp, use the correct MIME type
            files = {"file": (os.path.basename(temp_file_path), temp_file_to_upload, mime_type)}
            data = {"messaging_product": "whatsapp"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                upload_url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/media"
                logger.info(f"Uploading to: {upload_url}")
                
                response = await client.post(
                    upload_url,
                    headers=headers,
                    files=files,
                    data=data,
                )
                
                logger.info(f"Upload response status: {response.status_code}")
                logger.info(f"Upload response body: {response.text}")
                
                response.raise_for_status()
                result = response.json()
                logger.info(f"Media uploaded successfully. Media ID: {result.get('id')}")

        if "id" not in result:
            raise Exception("Failed to upload media - no ID in response")
        return result["id"]
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise
    finally:
        # Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info(f"Cleaned up temp file: {temp_file_path}")

async def send_typing_indicator(message_id: str) -> bool:
    """Send typing indicator and mark message as read via WhatsApp Cloud API."""
    if not message_id:
        logger.warning("No message ID provided for typing indicator")
        return False

    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    
    json_data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        }
    }

    logger.info(f"Sending typing indicator for message {message_id}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, headers=headers, json=json_data)
            logger.info(f"Typing indicator response status: {response.status_code}")
            logger.info(f"Typing indicator response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") is True:
                    logger.info("✅ Typing indicator sent successfully!")
                    return True
                else:
                    logger.warning(f"Typing indicator API returned non-success: {result}")
                    return False
            else:
                logger.error(f"Typing indicator API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")
            return False

async def send_whatsapp_message(to_number: str, message_text: str = None, media_id: str = None, media_type: str = "text") -> bool:
    """Send message via WhatsApp API (text, audio, or image)."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    
    if media_type == "audio" and media_id:
        json_data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "audio",
            "audio": {"id": media_id}
        }
    elif media_type == "image" and media_id:
        json_data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "image",
            "image": {"id": media_id, "caption": message_text or ""}
        }
    else:
        json_data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message_text or ""}
        }

    # Enhanced logging for debugging
    logger.info(f"Attempting to send WhatsApp message to {to_number}")
    logger.info(f"Message type: {media_type}")
    logger.info(f"JSON payload: {json.dumps(json_data, indent=2)}")
    logger.info(f"Token length: {len(WHATSAPP_TOKEN) if WHATSAPP_TOKEN else 0}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
            logger.info(f"Making request to URL: {url}")
            
            response = await client.post(
                url,
                headers=headers,
                json=json_data,
            )
            
            logger.info(f"WhatsApp API response status: {response.status_code}")
            
            response_text = response.text
            logger.info(f"WhatsApp API response body: {response_text}")
            
            # Try to parse as JSON for better logging
            try:
                response_json = response.json()
                logger.info(f"WhatsApp API response JSON: {json.dumps(response_json, indent=2)}")
            except:
                logger.info("Response is not valid JSON")
            
            response.raise_for_status()
            logger.info("Message sent successfully!")
            return True
            
        except httpx.TimeoutException as e:
            logger.error(f"WhatsApp API timeout error: {e}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API HTTP error: {e.response.status_code}")
            logger.error(f"Error response text: {e.response.text}")
            logger.error(f"Error response headers: {dict(e.response.headers)}")
            try:
                error_json = e.response.json()
                logger.error(f"Error response JSON: {json.dumps(error_json, indent=2)}")
            except:
                logger.error("Error response is not valid JSON")
            return False
        except httpx.RequestError as e:
            logger.error(f"WhatsApp API request error: {e}")
            logger.error(f"Request URL: {e.request.url if e.request else 'Unknown'}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

async def send_interactive_buttons(to_number: str, body: str, buttons: List[dict | str], header_text: str = None) -> bool:
    """Send interactive button message via WhatsApp API."""
    
    # WhatsApp interactive buttons have a 1024 character limit
    MAX_INTERACTIVE_LENGTH = 1024
    if len(body) > MAX_INTERACTIVE_LENGTH:
        await send_whatsapp_message(to_number, message_text=body)
        body = "Select an option:"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    action_buttons = []
    for btn in buttons:
        if isinstance(btn, str):
            action_buttons.append({"type": "reply", "reply": {"id": f"btn_{btn.lower()}", "title": btn[:20]}})
        else:
            action_buttons.append({"type": "reply", "reply": {"id": btn["id"], "title": btn["title"][:20]}})

    json_data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": action_buttons[:3]}
        }
    }
    
    if header_text and header_text.strip():
        json_data["interactive"]["header"] = {"type": "text", "text": header_text[:60]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending interactive buttons: {e}")
            return False

async def send_interactive_list(to_number: str, data: Dict[str, Any]) -> bool:
    """Send interactive list message (radio-style) via WhatsApp API."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    
    rows = []
    for row in data.get("rows", []):
        rows.append({
            "id": row["id"],
            "title": row["title"][:24],
            "description": row.get("description", "")[:72]
        })
        
    json_data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": data.get("body", "")},
            "footer": {"text": data.get("footer", "")},
            "action": {
                "button": data.get("button_label", "Select"),
                "sections": [
                    {
                        "title": data.get("section_title", "Options"),
                        "rows": rows
                    }
                ]
            }
        }
    }

    if data.get("header"):
        json_data["interactive"]["header"] = {"type": "text", "text": data.get("header", "")[:60]}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            logger.info("Interactive list sent successfully!")
            return True
        except Exception as e:
            logger.error(f"Error sending interactive list: {e}")
            return False

def _lang_buttons(current_language: str = "english") -> list:
    """Return language buttons - exclude current language, show only other options."""
    all_langs = [
        {"id": "lang_en", "title": "🇬🇧 English"},
        {"id": "lang_ha", "title": "🇳🇬 Hausa"},
        {"id": "lang_ig", "title": "🇳🇬 Igbo"},
        {"id": "lang_yo", "title": "🇳🇬 Yoruba"},
    ]
    lang_key = {"lang_en": "english", "lang_ha": "hausa", "lang_ig": "igbo", "lang_yo": "yoruba"}
    # Return languages other than current one (max 3 buttons for WhatsApp)
    others = [b for b in all_langs if lang_key[b["id"]] != current_language.lower()]
    return others[:3]

def _action_buttons(has_wallet: bool = False) -> list:
    """Return main action buttons for SabiSpend functionality."""
    buttons = [
        {"id": "check_balance", "title": "💰 Check Balance"},
        {"id": "verify_account", "title": "🔐 Verify Account"},
    ]
    
    if has_wallet:
        buttons.append({"id": "send_money", "title": "💸 Send Money"})
    else:
        buttons.append({"id": "open_account", "title": "🏦 Open Account"})
    
    return buttons

def _action_buttons(has_wallet: bool = False) -> list:
    """Return main action buttons for SabiSpend functionality."""
    buttons = [
        {"id": "check_balance", "title": "💰 Balance"},
        {"id": "verify_account", "title": "🔐 Verify"}
    ]
    
    if has_wallet:
        buttons.append({"id": "send_money", "title": "💸 Send Money"})
    else:
        buttons.append({"id": "open_account", "title": "🏦 Open Account"})
    
    return buttons


def _lang_list(current_language: str = "english", body: str = None) -> dict:
    """Build the Switch Language interactive list, marking the currently active language."""
    _display = {"english": "English", "hausa": "Hausa", "igbo": "Igbo", "yoruba": "Yoruba"}
    current_display = _display.get(current_language, "English")
    return {
        "body": body or ".",
        "footer": f"🗣 Current Language: {current_display}",
        "button_label": "Switch Language 🇳🇬",
        "section_title": "Nigerian Languages",
        "rows": [
            {"id": "lang_en", "title": "English",
             "description": "✓ Active" if current_language == "english" else "Default language"},
            {"id": "lang_ha", "title": "Hausa",
             "description": "✓ Active" if current_language == "hausa" else "Harshen Hausa"},
            {"id": "lang_ig", "title": "Igbo",
             "description": "✓ Active" if current_language == "igbo" else "Asụsụ Igbo"},
            {"id": "lang_yo", "title": "Yoruba",
             "description": "✓ Active" if current_language == "yoruba" else "Èdè Yorùbá"},
        ]
    }


async def process_audio_message(message: Dict, language: str = "english") -> str:
    """Process audio message and return transcribed text."""
    try:
        audio_id = message["audio"]["id"]
        audio_bytes = await download_media(audio_id)
        
        stt_service = get_stt_service(language)
        if not stt_service:
            raise Exception(f"STT service for {language} not initialized")
            
        transcribed_text = await stt_service.transcribe(audio_bytes)
        logger.info(f"Transcribed audio ({language}): {transcribed_text}")
        return transcribed_text
    except Exception as e:
        logger.error(f"Error processing audio in {language}: {e}")
        raise
@app.api_route("/whatsapp", methods=["GET", "POST"])
async def whatsapp_handler(request: Request) -> Response:
    """
    Lightweight handler that ACKs Facebook immediately and
    delegates the real work to a fire-and-forget background task.
    """
    # ---------- GET (webhook verification) ----------
    if request.method == "GET":
        params = request.query_params
        if params.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN:
            return Response(content=params.get("hub.challenge"), status_code=200)
        return Response(content="Verification token mismatch", status_code=403)

    # ---------- POST (incoming message) -------------
    await validate_whatsapp_hmac(request)
    try:
        data = await request.json()
    except Exception:
        logger.warning("Malformed JSON received")
        return Response(status_code=400)

    # Extract the message envelope
    try:
        value = data["entry"][0]["changes"][0]["value"]
        messages = value.get("messages", [])
        if not messages:  # ignore status/delivery receipts
            return Response(status_code=200)
        message = messages[0]
        from_number = message["from"]
        
        # Extract user's name from contacts
        contacts = value.get("contacts", [])
        user_name = "there"  # default
        if contacts and len(contacts) > 0:
            profile = contacts[0].get("profile", {})
            user_name = profile.get("name", "there")
        
        # Add user name to message for background processing
        message["_user_name"] = user_name
        
    except (KeyError, IndexError):
        logger.warning("Missing expected fields in webhook payload")
        return Response(status_code=200)

    # ✅ CRITICAL: Check for duplicates BEFORE scheduling background task
    message_id = message.get("id")
    if message_id and await _is_duplicate(message_id):
        logger.info(f"🚫 Duplicate message {message_id} from {from_number} - ignored")
        # Still return 200 OK to acknowledge receipt
        return Response(status_code=200)

    # ✅ FIRE-AND-FORGET: Schedule heavy work WITHOUT waiting
    task = asyncio.create_task(
        process_whatsapp_message(message, from_number)
    )
    
    # Add exception handler to prevent "Task exception was never retrieved" warnings
    def handle_task_exception(task_obj):
        try:
            task_obj.result()
        except Exception as e:
            logger.error(f"❌ Background task failed for {from_number}: {e}", exc_info=True)
    
    task.add_done_callback(handle_task_exception)
    
    # ✅ IMMEDIATE RESPONSE: ACK Facebook instantly
    logger.info(f"⚡ Webhook acknowledged immediately for message {message_id} from {from_number}")
    return Response(status_code=200)

async def process_whatsapp_message(message: dict, from_number: str):
    """
    Full pipeline:
    - download media (if any)
    - STT / vision / agent logic via MICROSERVICE
    - TTS (optional)
    - send reply via WhatsApp API
    """
    refresher_task = None
    stop_typing = None
    try:
        user_name = (
            message.get("_user_name") or
            "there"
        )
        message_type = message.get("type", "unknown")
        message_id = message.get("id")
        thread_id = from_number.replace("+", "")
        logger.info(f"[bg] Processing {message_type} from {from_number} (ID: {message_id})")

        content_for_agent = []
        should_respond_with_audio = False

        # ---------- INTERACTIVE ----------
        if message_type == "interactive":
            interactive = message["interactive"]
            itype = interactive["type"]
            if itype == "button_reply":
                button_reply = interactive["button_reply"]
                button_id = button_reply.get("id")
                
                if button_id == "select_language":
                    # Send List for language selection
                    list_data = _lang_list(get_user_language(thread_id))
                    await send_interactive_list(from_number, list_data)
                    return

                # Handle other button clicks
                else:
                    button_title = button_reply.get("title", "")
                    content_for_agent.append({
                        "type": "text",
                        "text": f"Interactive: {button_title}"
                    })

            elif itype == "list_reply":
                list_reply = interactive["list_reply"]
                row_id = list_reply.get("id")
                
                if row_id.startswith("lang_"):
                    lang_map = {"lang_en": "english", "lang_ha": "hausa", "lang_ig": "igbo", "lang_yo": "yoruba"}
                    selected_lang = lang_map.get(row_id, "english")
                    set_user_language(thread_id, selected_lang)
                    
                    # Confirm language change
                    confirms = {
                        "english": "Language selected will now be English! 🇳🇬",
                        "hausa": "Harshen da aka zaɓa yanzu zai zama Hausa! 🇳🇬",
                        "igbo": "Asụsụ a họọrọ ga-abụzi Igbo! 🇳🇬",
                        "yoruba": "Èdè tí a yàn yóò jẹ́ Yorùbá! 🇳🇬"
                    }
                    confirm_text = confirms.get(selected_lang, f"Language selected will now be {selected_lang.capitalize()}! 🇳🇬")
                    await send_whatsapp_message(from_number, message_text=confirm_text)
                    return
                else:
                    item_title = list_reply.get("title", "")
                    content_for_agent.append({
                        "type": "text",
                        "text": f"Selection: {item_title}"
                    })
            else:
                logger.info(f"Unsupported interactive type: {itype}")
                return

        # Get user's preferred language
        user_language = get_user_language(thread_id)
        logger.info(f"[bg] User language: {user_language}")

        # ---------- TEXT ----------
        if message_type == "text":
            raw_text = message["text"]["body"]
            
            # Translate to English if needed
            if user_language != "english":
                logger.info(f"🔄 Translating {user_language} input: {raw_text}")
                try:
                    translator = get_translator()
                    if user_language == "hausa":
                        english_text = translator.hausa_to_english(raw_text)
                    elif user_language == "igbo":
                        english_text = translator.igbo_to_english(raw_text)
                    elif user_language == "yoruba":
                        english_text = translator.yoruba_to_english(raw_text)
                    else:
                        english_text = raw_text

                    logger.info(f"✅ Translated to English: {english_text}")
                    content_for_agent.append({
                        "type": "text",
                        "text": english_text,
                        "original_text": raw_text
                    })
                except Exception as e:
                    logger.error(f"❌ Translation failed: {e}")
                    content_for_agent.append({
                        "type": "text",
                        "text": raw_text
                    })
            else:
                content_for_agent.append({
                    "type": "text",
                    "text": raw_text
                })

        # ---------- AUDIO ----------
        elif message_type == "audio":
            try:
                # Transcribe in correct language
                transcribed_text = await process_audio_message(message, language=user_language)
                
                # Translate to English if needed
                agent_input_text = transcribed_text
                if user_language != "english":
                    logger.info(f"🔄 Translating transcribed {user_language}: {transcribed_text}")
                    try:
                        translator = get_translator()
                        if user_language == "hausa":
                            agent_input_text = translator.hausa_to_english(transcribed_text)
                        elif user_language == "igbo":
                            agent_input_text = translator.igbo_to_english(transcribed_text)
                        elif user_language == "yoruba":
                            agent_input_text = translator.yoruba_to_english(transcribed_text)
                        logger.info(f"✅ Translated voice to English: {agent_input_text}")
                    except Exception as e:
                        logger.error(f"❌ Voice translation failed: {e}")

                    content_for_agent.append({
                        "type": "text",
                        "text": f"[Voice]: {agent_input_text}",
                        "original_text": transcribed_text
                    })
                else:
                    content_for_agent.append({
                        "type": "text",
                        "text": f"[Voice]: {agent_input_text}"
                    })
                should_respond_with_audio = True
            except Exception as e:
                logger.error(f"[bg] STT failed: {e}")
                asyncio.create_task(send_error_alert("WhatsApp", e, f"STT failed — language: {user_language}"))
                list_data = _lang_list(user_language, "Sorry, I couldn't process that voice message. Please try again.")
                await send_interactive_list(from_number, list_data)
                return

        # ---------- IMAGE ----------
        elif message_type == "image":
            caption = message.get("image", {}).get("caption", "")
            user_text = caption if caption else "Look at this image and tell me what you see. Then answer any question about it if related to Nigerian government services."
            try:
                image_bytes = await download_media(message["image"]["id"])
                data_uri = convert_to_data_uri(image_bytes, "image/jpeg")
                # image_url must come before text for vision models
                content_for_agent.append({
                    "type": "image_url",
                    "image_url": {"url": data_uri}
                })
                content_for_agent.append({
                    "type": "text",
                    "text": user_text
                })
            except Exception as e:
                logger.error(f"[bg] Image processing failed: {e}")
                list_data = _lang_list(user_language, "Sorry, I couldn't process that image. Please try again.")
                await send_interactive_list(from_number, list_data)
                return

        # ---------- UNSUPPORTED ----------
        else:
            # Unsupported type with Language List
            list_data = _lang_list(user_language, "I can process text, voice messages, and images.")
            await send_interactive_list(from_number, list_data)
            return

        # ---------- SEND TYPING INDICATOR ----------
        if message_id:
            await send_typing_indicator(message_id)

        # Set up refresher if needed (for long-running voice responses)
        if should_respond_with_audio:
            stop_typing = asyncio.Event()
            async def typing_refresher():
                while not stop_typing.is_set():
                    if not await send_typing_indicator(message_id):
                        logger.warning("Failed to refresh typing indicator")
                    await asyncio.sleep(20)
            refresher_task = asyncio.create_task(typing_refresher())

        # ---------- CALL AGENT MICROSERVICE ----------
        # Extract user's question from content_for_agent
        user_question = ""
        for item in content_for_agent:
            if item.get("type") == "text":
                user_question = item.get("text", "")
                break

        logger.info(f"[bg] 📤 Calling agent microservice for thread {thread_id}")

        # Sentence boundary regex used for streaming TTS pipeline
        _sent_re = re.compile(r'(?<=[.!?])\s+')

        # Holds asyncio.Tasks for concurrent TTS
        pre_tts_tasks: list = []
        _already_translated = False  # set True when non-English streaming pipeline handles translation
        dashboard_conversation_id = None  # set after microservice logs the conversation

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if should_respond_with_audio and user_language != "english":
                    # ── STREAMING path: LLM → NLLB (sentence) → TTS tasks ──────────
                    text_content = next(
                        (item.get("text", "") for item in content_for_agent if item.get("type") == "text"),
                        ""
                    )
                    logger.info(f"[bg] 🌊 Streaming: LLM → NLLB → TTS ({user_language} voice)")
                    response_text = ""
                    en_buf = ""
                    local_sentences: list = []
                    _translator = get_translator()
                    _tts_svc = get_tts_service(user_language)
                    if user_language == "hausa":
                        _voice_param = HAUSA_TTS_VOICE
                    elif user_language == "igbo":
                        _voice_param = IGBO_TTS_VOICE
                    else:
                        _voice_param = YORUBA_TTS_VOICE

                    async def _translate_sentence(sentence: str) -> str:
                        if user_language == "hausa":
                            return await asyncio.to_thread(_translator.english_to_hausa, sentence)
                        elif user_language == "igbo":
                            return await asyncio.to_thread(_translator.english_to_igbo, sentence)
                        else:
                            return await asyncio.to_thread(_translator.english_to_yoruba, sentence)

                    async with client.stream(
                        "POST",
                        f"{AGENT_MICROSERVICE_URL}/api/agent/stream",
                        json={
                            "content": text_content,
                            "thread_id": thread_id,
                            "message_type": "voice",
                            "source": "whatsapp",
                            "user_name": user_name,
                            "language": user_language
                        },
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            raw = line[6:]
                            if raw == "[DONE]":
                                break
                            try:
                                ev = json.loads(raw)
                            except json.JSONDecodeError:
                                continue
                            if ev.get("done") or "error" in ev:
                                dashboard_conversation_id = ev.get("conversation_id")
                                break
                            chunk = ev.get("content", "")
                            if not chunk:
                                continue
                            response_text += chunk
                            en_buf += chunk
                            parts = _sent_re.split(en_buf)
                            if len(parts) > 1:
                                for sentence in parts[:-1]:
                                    sentence = sentence.strip()
                                    if len(sentence) <= 3:
                                        continue
                                    logger.info(f"[bg] 🌍 Translating: {sentence[:60]}")
                                    local_sent = (await _translate_sentence(sentence)).strip()
                                    if local_sent:
                                        local_sentences.append(local_sent)
                                        tts_input = yoruba_numbers_to_words(local_sent) if user_language == "yoruba" else local_sent
                                        pre_tts_tasks.append(asyncio.create_task(
                                            asyncio.to_thread(_tts_svc.synthesize_sync, tts_input, _voice_param)
                                        ))
                                en_buf = parts[-1]

                    # Flush leftover buffer
                    if en_buf.strip() and len(en_buf.strip()) > 3:
                        local_sent = (await _translate_sentence(en_buf.strip())).strip()
                        if local_sent:
                            local_sentences.append(local_sent)
                            tts_input = yoruba_numbers_to_words(local_sent) if user_language == "yoruba" else local_sent
                            pre_tts_tasks.append(asyncio.create_task(
                                asyncio.to_thread(_tts_svc.synthesize_sync, tts_input, _voice_param)
                            ))

                    # Set response_text to translated text; skip re-translation later
                    response_text = " ".join(local_sentences) if local_sentences else response_text
                    _already_translated = True

                    # Update dashboard with native language response
                    if dashboard_conversation_id:
                        try:
                            async with httpx.AsyncClient(timeout=10.0) as _client:
                                await _client.post(
                                    f"{AGENT_MICROSERVICE_URL}/api/agent/update-native-response",
                                    json={"conversation_id": dashboard_conversation_id, "native_response": response_text}
                                )
                        except Exception as _e:
                            logger.warning(f"⚠️ Could not update native response in dashboard: {_e}")
                    logger.info(f"[bg] ✅ Streamed+translated {len(local_sentences)} sentences, {len(pre_tts_tasks)} TTS tasks queued")

                elif should_respond_with_audio and user_language == "english":
                    # ── STREAMING path: LLM streams → TTS tasks start immediately ─
                    text_content = next(
                        (item.get("text", "") for item in content_for_agent if item.get("type") == "text"),
                        ""
                    )
                    logger.info("[bg] 🌊 Streaming agent + concurrent TTS (English voice)")
                    response_text = ""
                    text_buf = ""
                    tts_svc = get_tts_service("english")
                    async with client.stream(
                        "POST",
                        f"{AGENT_MICROSERVICE_URL}/api/agent/stream",
                        json={
                            "content": text_content,
                            "thread_id": thread_id,
                            "message_type": "voice",
                            "source": "whatsapp",
                            "user_name": user_name,
                            "language": user_language
                        },
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            raw = line[6:]
                            if raw == "[DONE]":
                                break
                            try:
                                ev = json.loads(raw)
                            except json.JSONDecodeError:
                                continue
                            if ev.get("done") or "error" in ev:
                                break
                            chunk = ev.get("content", "")
                            if not chunk:
                                continue
                            response_text += chunk
                            text_buf += chunk
                            parts = _sent_re.split(text_buf)
                            if len(parts) > 1:
                                for sentence in parts[:-1]:
                                    sentence = sentence.strip()
                                    if len(sentence) > 3:
                                        logger.info(f"[bg] 🎤 TTS task launched: {sentence[:60]}")
                                        pre_tts_tasks.append(
                                            asyncio.create_task(
                                                asyncio.to_thread(tts_svc.synthesize_sync, sentence, ENGLISH_TTS_VOICE)
                                            )
                                        )
                                text_buf = parts[-1]
                    # Flush remaining buffer
                    if text_buf.strip() and len(text_buf.strip()) > 3:
                        pre_tts_tasks.append(
                            asyncio.create_task(
                                asyncio.to_thread(tts_svc.synthesize_sync, text_buf.strip(), ENGLISH_TTS_VOICE)
                            )
                        )
                    if not response_text:
                        response_text = "I received your message. How can I help you?"

                    # Fallback: if streaming returned an error phrase, retry with non-streaming
                    _error_phrases = ("sorry, something went wrong", "i'm having trouble", "please try again")
                    if len(response_text) < 60 and any(p in response_text.lower() for p in _error_phrases):
                        logger.warning("[bg] ⚠️ Streaming returned error response, falling back to non-streaming")
                        pre_tts_tasks.clear()
                        fallback_resp = await client.post(
                            f"{AGENT_MICROSERVICE_URL}/api/agent/chat",
                            json={
                                "content": text_content,
                                "thread_id": thread_id,
                                "message_type": "voice",
                                "source": "whatsapp",
                                "user_name": user_name,
                                "language": user_language
                            },
                        )
                        fallback_resp.raise_for_status()
                        response_text = fallback_resp.json().get("response", response_text)

                    logger.info(f"[bg] ✅ Streamed {len(response_text)} chars, {len(pre_tts_tasks)} TTS tasks running")

                else:
                    # ── Standard non-streaming path ──────────────────────────────
                    agent_response = await client.post(
                        f"{AGENT_MICROSERVICE_URL}/api/agent/chat",
                        json={
                            "content": content_for_agent,
                            "thread_id": thread_id,
                            "message_type": "voice" if should_respond_with_audio else "text",
                            "source": "whatsapp",
                            "user_name": user_name,
                            "language": user_language
                        }
                    )
                    logger.info(f"[bg] Agent microservice response status: {agent_response.status_code}")
                    agent_response.raise_for_status()
                    result = agent_response.json()
                    response_text = result.get("response", "")
                    dashboard_conversation_id = result.get("conversation_id")
                    if not response_text:
                        logger.error("[bg] ❌ Agent microservice returned empty response")
                        response_text = "I received your message. How can I help you?"
                    logger.info(f"[bg] ✅ Agent response: {response_text[:100]}...")
                
        except httpx.TimeoutException as e:
            logger.error("[bg] ❌ Agent microservice timeout")
            asyncio.create_task(send_error_alert("WhatsApp", e, f"Agent microservice timeout — user: {from_number}, lang: {user_language}"))
            list_data = _lang_list(user_language, "I'm taking longer than usual to respond. Please try again.")
            await send_interactive_list(from_number, list_data)
            return
        except httpx.HTTPError as e:
            logger.error(f"[bg] ❌ Agent microservice HTTP error: {e}")
            asyncio.create_task(send_error_alert("WhatsApp", e, f"Agent microservice HTTP error — user: {from_number}, lang: {user_language}"))
            list_data = _lang_list(user_language, "Something went wrong on our side. Please try again later.")
            await send_interactive_list(from_number, list_data)
            return
        except Exception as e:
            logger.error(f"[bg] ❌ Error calling agent microservice: {e}")
            asyncio.create_task(send_error_alert("WhatsApp", e, f"Agent microservice call failed — user: {from_number}, lang: {user_language}"))
            list_data = _lang_list(user_language, "Something went wrong on our side. Please try again later.")
            await send_interactive_list(from_number, list_data)
            return

        # Handle non-English response translation (skipped if streaming pipeline already translated)
        if user_language != "english" and not _already_translated:
            logger.info(f"🔄 Translating agent response to {user_language}...")
            try:
                translator = get_translator()
                # Split by newline to preserve list/paragraph structure
                # Protect numbered list markers (e.g. "1.") from being translated
                _num_re = re.compile(r'^(\s*\d+\.\s*)')
                lines = response_text.split('\n')
                translated_lines = []
                for line in lines:
                    if not line.strip():
                        translated_lines.append(line)
                        continue
                    # Extract leading number marker if present
                    num_match = _num_re.match(line)
                    prefix = num_match.group(1) if num_match else ""
                    text_part = line[len(prefix):].strip()
                    if not text_part:
                        translated_lines.append(line)
                        continue
                    if user_language == "hausa":
                        translated = translator.english_to_hausa(text_part)
                    elif user_language == "igbo":
                        translated = translator.english_to_igbo(text_part)
                    elif user_language == "yoruba":
                        translated = translator.english_to_yoruba(text_part)
                    else:
                        translated = text_part
                    translated_lines.append(prefix + translated)
                response_text = "\n".join(translated_lines)
                logger.info(f"✅ Final {user_language} response: {response_text[:100]}...")

                # Update dashboard with native language response
                if dashboard_conversation_id:
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as _client:
                            await _client.post(
                                f"{AGENT_MICROSERVICE_URL}/api/agent/update-native-response",
                                json={"conversation_id": dashboard_conversation_id, "native_response": response_text}
                            )
                    except Exception as _e:
                        logger.warning(f"⚠️ Could not update native response in dashboard: {_e}")
            except Exception as e:
                logger.error(f"❌ Translation back failed: {e}")

        # Clean up markdown for WhatsApp display
        response_text = clean_whatsapp_message(response_text)

        # === SAVE CONVERSATION TO MONGODB (Old feedback system for backward compatibility) ===
        from feedback import store_conversation, store_pending_response
        store_conversation(
            thread_id=thread_id,
            user_name=user_name,
            question=user_question,
            response=response_text,
            feedback=None  # No feedback yet
        )

        # Set pending response for feedback (store both question and response)
        store_pending_response(thread_id, user_question, response_text)

        # ---------- SEND REPLY ----------
        # Stop typing refresher before sending reply
        if refresher_task:
            stop_typing.set()
            refresher_task.cancel()
            try:
                await asyncio.wait_for(refresher_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            refresher_task = None
        
        # Send audio if voice message
        if should_respond_with_audio:
            try:
                logger.info(f"[bg] 🔊 Generating regional audio for: {response_text[:50]}...")
                
                # Pick correct TTS
                tts_service = get_tts_service(user_language)
                if not tts_service:
                    raise Exception(f"TTS service for {user_language} not initialized")
                
                # Check for regional voice param
                voice_param = "regional_voice"
                if user_language == "english":
                    voice_param = ENGLISH_TTS_VOICE
                elif user_language == "hausa":
                    voice_param = HAUSA_TTS_VOICE
                elif user_language == "igbo":
                    voice_param = IGBO_TTS_VOICE
                elif user_language == "yoruba":
                    voice_param = YORUBA_TTS_VOICE
                
                if pre_tts_tasks:
                    # English: await all concurrent tasks launched during LLM streaming
                    logger.info(f"[bg] ⏳ Awaiting {len(pre_tts_tasks)} concurrent TTS tasks...")
                    audio_parts = []
                    for task in pre_tts_tasks:
                        try:
                            audio_parts.append(await task)
                        except Exception as tts_err:
                            logger.warning(f"[bg] ⚠️ TTS task failed: {tts_err}")
                    audio_bytes = await asyncio.to_thread(_concat_mp3_chunks, audio_parts)
                    if not audio_bytes:
                        raise Exception("All TTS tasks produced no audio")
                    logger.info(f"[bg] ✅ Concatenated {len(audio_parts)} chunks → {len(audio_bytes)} bytes")
                else:
                    # Non-English or fallback: single TTS call on full text
                    sentences = [s.strip() for s in _sent_re.split(response_text) if len(s.strip()) > 3]
                    if not sentences:
                        sentences = [response_text]
                    logger.info(f"[bg] 🎤 Running parallel TTS for {len(sentences)} sentences ({user_language})")
                    tasks = [
                        asyncio.create_task(asyncio.to_thread(tts_service.synthesize_sync, s, voice_param))
                        for s in sentences
                    ]
                    audio_parts = []
                    for t in tasks:
                        try:
                            audio_parts.append(await t)
                        except Exception as tts_err:
                            logger.warning(f"[bg] ⚠️ TTS sentence failed: {tts_err}")
                    audio_bytes = await asyncio.to_thread(_concat_mp3_chunks, audio_parts)
                    if not audio_bytes:
                        raise Exception("All TTS sentences produced no audio")

                logger.info(f"[bg] ✅ Audio generated: {len(audio_bytes)} bytes")
                
                media_id = await upload_media_to_whatsapp(audio_bytes, "audio/mpeg")
                if media_id:
                    logger.info(f"[bg] ✅ Media uploaded successfully. Sending audio with media_id: {media_id}")
                    
                    # Wait for WhatsApp to process the uploaded media before sending
                    await asyncio.sleep(0.5)
                    
                    success = await send_whatsapp_message(from_number, media_id=media_id, media_type="audio")
                    if success:
                        logger.info(f"[bg] ✅ Audio message sent successfully to WhatsApp API!")
                        # Just send a small confirmation/language change option
                        list_data = _lang_list(user_language)
                        await send_interactive_list(from_number, list_data)
                        return
                
                # Fallback to text if audio fails OR if __LIST__ is present (lists need to be shown)
                if "__LIST__" in response_text:
                    parts = response_text.split("__LIST__")[1].split("|")
                    if len(parts) >= 5:
                        list_data = {
                            "header": parts[1],
                            "body": parts[2],
                            "button_label": parts[0],
                            "section_title": parts[3],
                            "rows": [{"id": f"opt_{i}", "title": opt.strip()} for i, opt in enumerate(parts[4].split(","))]
                        }
                        await send_interactive_list(from_number, list_data)
                        return

                # Standard Text Response with Language List
                # Handle long responses by splitting them from interactive elements
                if len(response_text) > 1024:
                    await send_whatsapp_message(from_number, message_text=response_text)
                    list_data = _lang_list(user_language)
                else:
                    list_data = _lang_list(user_language, response_text)
                await send_interactive_list(from_number, list_data)

            except Exception as e:
                logger.error(f"[bg] ❌ Operation failed: {e}", exc_info=True)
                asyncio.create_task(send_error_alert("WhatsApp", e, f"TTS/audio upload failed — user: {from_number}, lang: {user_language}"))
                list_data = _lang_list(user_language, response_text)
                await send_interactive_list(from_number, list_data)
        else:
            # Send text message with buttons
            # Check for __LIST__ format for MCQs
            if "__LIST__" in response_text:
                parts = response_text.split("__LIST__")[1].split("|")
                if len(parts) >= 5:
                    list_data = {
                        "header": parts[1],
                        "body": parts[2],
                        "button_label": parts[0],
                        "section_title": parts[3],
                        "rows": [{"id": f"opt_{i}", "title": opt.strip()} for i, opt in enumerate(parts[4].split(","))]
                    }
                    await send_interactive_list(from_number, list_data)
                    return

            # Standard Text Response (Non-Audio Branch) with Language List
            # Handle long responses by splitting them from interactive elements
            if len(response_text) > 1024:
                await send_whatsapp_message(from_number, message_text=response_text)
                list_data = _lang_list(user_language)
            else:
                list_data = _lang_list(user_language, response_text)
            await send_interactive_list(from_number, list_data)

    except Exception as e:
        logger.exception("[bg] ❌ Unhandled exception in background task")
        asyncio.create_task(send_error_alert("WhatsApp", e, f"Unhandled exception in message processing — user: {from_number}"))
        try:
            list_data = _lang_list(get_user_language(thread_id), "Something went wrong on our side. Please try again later.")
            await send_interactive_list(from_number, list_data)
        except Exception:
            pass
    finally:
        # Cleanup typing refresher
        if refresher_task:
            if stop_typing:
                stop_typing.set()
            refresher_task.cancel()
            try:
                await asyncio.wait_for(refresher_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
@app.get("/")
async def root():
    return {"message": "WhatsApp Voice Retriever Agent is running!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))