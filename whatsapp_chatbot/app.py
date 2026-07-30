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

from services import get_stt_service, get_tts_service
from expense_tracker import get_all_user_threads

# Import unified agent directly (now SabiSpend agent)
from unified_agent import unified_agent

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")

from config import (
    HAUSA_TTS_VOICE, IGBO_TTS_VOICE, YORUBA_TTS_VOICE, ENGLISH_TTS_VOICE,
    VISION_API_URL
)

if not all([WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN]):
    logger.error("Missing one or more required WhatsApp environment variables.")
    exit(1)

from feedback import (
    store_feedback, store_conversation, store_pending_response, get_pending_response,
    get_user_language, set_user_language,
    set_user_journey, get_user_journey, get_all_users_with_journey,
    is_new_user
)

logger.info("🚀 Starting WhatsApp Voice Retriever Agent")
_find_ffmpeg()  # Cache ffmpeg path at startup

# SabiSpend - No scheduled reminders (user-initiated only)
# Users can check their profit and savings anytime by asking

# No background tasks for SabiSpend - all user-initiated

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the FastAPI app and initialize components."""

    logger.info("=" * 60)
    logger.info("💰 Starting SabiSpend WhatsApp Agent")
    logger.info("=" * 60)

    try:
        # Initialize unified agent (now SabiSpend)
        logger.info("🔧 Initializing SabiSpend agent...")
        await unified_agent.initialize()
        logger.info("✅ SabiSpend agent ready!")

        logger.info("=" * 60)
        logger.info("✅ SabiSpend WhatsApp Agent Ready!")
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
    title="SabiSpend WhatsApp Money Assistant",
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

async def recognize_invoice_from_image(image_bytes: bytes) -> dict:
    """
    Send image to Vision API for OCR (invoice/receipt recognition).
    Returns dict with extracted text and amounts.
    """
    try:
        from invoice_ocr import recognize_invoice
        
        logger.info(f"📸 Sending image to Vision API for OCR: {VISION_API_URL}")
        result = await recognize_invoice(image_bytes)
        
        logger.info(f"✅ Invoice OCR result: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Invoice OCR error: {e}")
        return {"success": False, "error": str(e), "text": "", "amounts": []}

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


def _split_whatsapp_text(text: str, limit: int = 4000) -> List[str]:
    """Split text without breaking words or WhatsApp's 4096-char limit."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    parts = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break
        boundary = remaining.rfind("\n\n", 0, limit + 1)
        if boundary < limit // 2:
            boundary = remaining.rfind("\n", 0, limit + 1)
        if boundary < limit // 2:
            boundary = remaining.rfind(" ", 0, limit + 1)
        if boundary <= 0:
            boundary = limit
        parts.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()
    return [part for part in parts if part]

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
       
        text_parts = _split_whatsapp_text(message_text or "")
        if len(text_parts) > 1:
            for part in text_parts:
                if not await send_whatsapp_message(to_number, message_text=part):
                    return False
            return True
        json_data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": text_parts[0] if text_parts else ""}
        }

    # Enhanced logging for debugging
    logger.info(f"Attempting to send WhatsApp message to {to_number}")
    logger.info(f"Message type: {media_type}")
    logger.info("WhatsApp payload prepared (content omitted, %s chars)", len(message_text or ""))
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

def _lang_list(current_language: str = "english", body: str = None) -> dict:
    """Build the Switch Language interactive list, excluding the current language."""
    _display = {"english": "English", "hausa": "Hausa", "igbo": "Igbo", "yoruba": "Yoruba"}
    current_display = _display.get(current_language, "English")
    
    # All language options
    all_rows = [
        {"id": "lang_en", "title": "English", "description": "Default language", "lang": "english"},
        {"id": "lang_ha", "title": "Hausa", "description": "Harshen Hausa", "lang": "hausa"},
        {"id": "lang_ig", "title": "Igbo", "description": "Asụsụ Igbo", "lang": "igbo"},
        {"id": "lang_yo", "title": "Yoruba", "description": "Èdè Yorùbá", "lang": "yoruba"},
    ]
    
    # Filter out the current language
    available_rows = [
        {"id": row["id"], "title": row["title"], "description": row["description"]}
        for row in all_rows 
        if row["lang"] != current_language.lower()
    ]
    
    return {
        "body": body or "Select your language:",
        "footer": f"🗣 Current: {current_display}",
        "button_label": "Change Language",
        "section_title": "Available Languages",
        "rows": available_rows
    }

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


async def send_response_with_language_list(phone_number: str, message_text: str, current_language: str = "english", has_wallet: bool = False):
    """Send text response with interactive language list directly (no button needed)"""
    
    # Build the language list data
    list_data = _lang_list(current_language, message_text if len(message_text) <= 1000 else None)
    
    # If message is too long, send it separately first
    if len(message_text) > 1000:
        await send_whatsapp_message(phone_number, message_text=message_text)
        list_data = _lang_list(current_language, "Select your language:")
    
    # Send the interactive list directly
    try:
        await send_interactive_list(phone_number, list_data)
        return True
    except Exception as e:
        logger.error(f"Failed to send interactive list: {e}, falling back to button")
        # Fallback to button approach
        language_button = [{"id": "select_language", "title": "🌍 Change Language"}]
        await send_interactive_buttons(phone_number, message_text if len(message_text) <= 1000 else "Choose an option:", language_button)
        return True


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

    message_id = message.get("id")

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
        # Mirror the user's medium. Images use voice because SabiSpend is
        # voice-first and image explanations are easier to hear.
        should_respond_with_audio = message_type in {"audio", "image"}

        # ---------- INTERACTIVE ----------
        if message_type == "interactive":
            interactive = message["interactive"]
            itype = interactive["type"]
            if itype == "button_reply":
                button_reply = interactive["button_reply"]
                button_id = button_reply.get("id")

                # Handle language selection button - show interactive list
                if button_id == "select_language":
                    # Send List for language selection
                    list_data = _lang_list(get_user_language(thread_id))
                    await send_interactive_list(from_number, list_data)
                    return

                # Handle language selection buttons (onboarding)
                if button_id in ("lang_english", "lang_hausa", "lang_igbo", "lang_yoruba"):
                    lang_map = {
                        "lang_english": "english",
                        "lang_hausa": "hausa",
                        "lang_igbo": "igbo",
                        "lang_yoruba": "yoruba"
                    }
                    selected_lang = lang_map[button_id]
                    set_user_language(thread_id, selected_lang)
                    set_user_journey(thread_id, "onboarding_language_selected")
                    logger.info(f"[bg] ✅ Language saved: {from_number} → {selected_lang}")
                    
                    # For hackathon: Auto-create BMONI account with test data
                    logger.info(f"[bg] 🔐 Setting up BMONI account for {from_number}...")
                    try:
                        from bmoni_client import get_or_create_bmoni_user, ensure_wallet_created
                        from bmoni_store import bmoni_store
                        
                        # Normalize phone number (add + prefix if missing)
                        normalized_phone = from_number if from_number.startswith("+") else f"+{from_number}"
                        
                        # Check if account already exists
                        existing_account = bmoni_store.get_by_phone(normalized_phone)
                        
                        if existing_account and existing_account.get("bmoni_user_id"):
                            logger.info(f"[bg] ✅ Account already exists for {normalized_phone}")
                            bmoni_user_id = existing_account["bmoni_user_id"]
                        else:
                            # Create BMONI user with test data (hackathon)
                            logger.info(f"[bg] 📝 Creating new BMONI account with test data...")
                            bmoni_user_id = await get_or_create_bmoni_user(normalized_phone, user_name or "Test User")
                            
                            if bmoni_user_id:
                                logger.info(f"[bg] ✅ BMONI user created: {bmoni_user_id}")
                            else:
                                logger.error(f"[bg] ❌ BMONI user creation failed")
                        
                        # Create wallet (server-side signing)
                        if bmoni_user_id:
                            wallet_result = await ensure_wallet_created(normalized_phone, bmoni_user_id)
                            
                            if wallet_result.get("success"):
                                logger.info(f"[bg] 🎉 Wallet created: {wallet_result.get('wallet_address')}")
                                
                                # TODO: Auto-activate NGN rail with test BVN (22222222222)
                                # This will be added when testing with real BMONI API
                                
                            else:
                                logger.warning(f"[bg] ⚠️ Wallet creation failed: {wallet_result.get('error')}")
                                
                    except Exception as e:
                        logger.error(f"[bg] ❌ BMONI setup error: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    # Send confirmation in selected language with buttons
                    confirms = {
                        "english": "✅ Account created! You can now track expenses, send money, check balance, verify account and detect scams.",
                        "hausa": "✅ An kirkiro asusun! Yanzu za ka iya lura da kashe kuɗi, tura kuɗi, duba ma'auni, tabbatar da asusun da gano damfara.",
                        "igbo": "✅ Emepụtara akaụntụ! Ugbu a ị nwere ike soro mmefu ego, zipu ego, lelee ego, kwado akaụntụ ma chọpụta aghụghọ.",
                        "yoruba": "✅ Iroyin ti dá! Bayi o le tọpa inawo, fi owo ranṣẹ, ṣayẹwo iye owo, jẹrisi iroyin ati ṣawari ẹtan."
                    }
                    confirm_text = confirms.get(selected_lang, confirms["english"])
                    # Send with buttons for immediate functionality
                    await send_response_with_language_list(from_number, confirm_text, selected_lang, has_wallet=True)
                    
                    # Mark onboarding complete
                    set_user_journey(thread_id, "onboarding_complete")
                    return
                
                # Handle language switch buttons (old implementation - keep for backward compatibility)
                elif button_id in ("lang_en", "lang_ha", "lang_ig", "lang_yo"):
                    lang_map = {"lang_en": "english", "lang_ha": "hausa", "lang_ig": "igbo", "lang_yo": "yoruba"}
                    selected_lang = lang_map[button_id]
                    set_user_language(thread_id, selected_lang)
                    confirms = {
                        "english": "✅ Language changed to English! How can I help you?",
                        "hausa": "✅ An canza harshe zuwa Hausa! Yaya zan iya taimaka muku?",
                        "igbo": "✅ Agbanwela asụsụ na Igbo! Kedu etu m ga-esi nyere gị aka?",
                        "yoruba": "✅ Ti yipada ede si Yorùbá! Báwo ni mo ṣe lè ràn ọ́ lọ́wọ́?"
                    }
                    confirm_text = confirms[selected_lang]
                    await send_response_with_language_list(from_number, confirm_text, selected_lang)
                    return
                
                # Handle other button interactions
                else:
                    button_title = button_reply.get("title", "")
                    content_for_agent.append({
                        "type": "text",
                        "text": f"Interactive: {button_title}"
                    })
                    button_title = button_reply.get("title", "")
                    content_for_agent.append({
                        "type": "text",
                        "text": f"Interactive: {button_title}"
                    })

            elif itype == "list_reply":
                list_reply = interactive["list_reply"]
                row_id = list_reply.get("id")
                
                # Handle language selection from interactive list
                if row_id.startswith("lang_"):
                    lang_map = {"lang_en": "english", "lang_ha": "hausa", "lang_ig": "igbo", "lang_yo": "yoruba"}
                    selected_lang = lang_map.get(row_id, "english")
                    set_user_language(thread_id, selected_lang)
                    
                    # Confirm language change
                    confirms = {
                        "english": "✅ Language changed to English! How can I help you?",
                        "hausa": "✅ An canza harshe zuwa Hausa! Yaya zan iya taimaka muku?",
                        "igbo": "✅ Agbanwela asụsụ na Igbo! Kedu etu m ga-esi nyere gị aka?",
                        "yoruba": "✅ Ti yipada ede si Yorùbá! Báwo ni mo ṣe lè ràn ọ́ lọ́wọ́?"
                    }
                    confirm_text = confirms.get(selected_lang, confirms["english"])
                    
                    # Send confirmation with the language list
                    await send_response_with_language_list(from_number, confirm_text, selected_lang)
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

            # ── ONBOARDING FLOW: Language Selection (1/2/3/4) ───
            # Step 1: Language selection
            stripped = raw_text.strip()
            language_map = {"1": "english", "2": "hausa", "3": "igbo", "4": "yoruba"}
            
            # Check if user just selected language (no journey set yet)
            user_profile = get_user_journey(thread_id)
            if stripped in language_map and not user_profile:
                language_choice = language_map[stripped]
                set_user_language(thread_id, language_choice)
                set_user_journey(thread_id, "onboarding_language_selected")
                logger.info(f"[bg] ✅ Language saved: {from_number} → {language_choice}")
                
                user_type_msg = (
                    "Great! Now tell me about yourself:\n\n"
                    "1️⃣ Market trader / seller\n"
                    "2️⃣ Small business owner / artisan\n"
                    "3️⃣ Individual / other\n\n"
                    "Reply with *1*, *2*, or *3*"
                )
                await send_whatsapp_message(from_number, user_type_msg)
                return
            
            # Step 2: User type selection
            user_type_map = {"1": "trader", "2": "artisan", "3": "individual"}
            if stripped in user_type_map and user_profile.get("journey") == "onboarding_language_selected":
                user_type = user_type_map[stripped]
                set_user_journey(thread_id, "onboarding_complete", business_type=user_type)
                logger.info(f"[bg] ✅ User type saved: {from_number} → {user_type}")
                await send_whatsapp_message(from_number, (
                    "✅ You're ready. Send a voice note or text like "
                    "“I bought tomatoes for 12,000 naira,” or send a receipt photo.\n\n"
                    "Your BMONI wallet is set up automatically in the background — "
                    "just tell me your balance, savings, or transfer requests whenever you like."
                ))
                return
            # ────────────────────────────────────────────────────────────

            # ── First message — onboarding (language selection with buttons) ───
            if is_new_user(thread_id):
                logger.info(f"[bg] 👋 New user detected: {from_number} — sending onboarding message")
                onboarding_msg = (
                    "👋 *Welcome to SabiSpend!*\n\n"
                    "I'm your AI money assistant. I help you:\n\n"
                    "💰 Track daily expenses and sales\n"
                    "📊 Calculate your profit\n"
                    "🏦 Save money in your BMONI wallet\n"
                    "🛡️ Check if messages are scams\n\n"
                    "I can respond in *voice and text* in all 4 Nigerian languages.\n\n"
                    "🌍 *Select your language to start:*"
                )
                
                # Language selection buttons
                language_buttons = [
                    {"id": "lang_english", "title": "🇬🇧 English"},
                    {"id": "lang_hausa", "title": "🇳🇬 Hausa"},
                    {"id": "lang_igbo", "title": "🇳🇬 Igbo"},
                    {"id": "lang_yoruba", "title": "🇳🇬 Yoruba"}
                ]
                
                # Save placeholder so this user is not treated as new again
                store_conversation(thread_id, user_name, "[onboarding]", onboarding_msg)
                await send_interactive_buttons(from_number, onboarding_msg, language_buttons)
                
                # Add privacy policy and terms footer
                footer_msg = (
                    "\n\n📄 By using SabiSpend, you agree to our:\n"
                    "• Privacy Policy: https://sabispend.com/privacy\n"
                    "• Terms of Service: https://sabispend.com/terms"
                )
                await send_whatsapp_message(from_number, footer_msg)
                return
            # ────────────────────────────────────────────────────────────

            # ── Returning user greeting (show features) ───
            # Check if user says "hi", "hello", "hey", "start" etc. and has wallet setup
            greeting_pattern = r'^(hi|hello|hey|start|menu|help)[\s!.]*$'
            if re.match(greeting_pattern, stripped, re.IGNORECASE):
                from bmoni_store import bmoni_store
                # Normalize phone number (add + prefix if missing)
                normalized_phone = from_number if from_number.startswith("+") else f"+{from_number}"
                existing_account = bmoni_store.get_by_phone(normalized_phone)
                
                if existing_account and existing_account.get("bmoni_user_id"):
                    logger.info(f"[bg] 👋 Returning user greeting: {from_number}")
                    
                    # Check if wallet exists
                    has_wallet = existing_account.get("wallet") is not None
                    
                    # Get user's language for message
                    welcome_messages = {
                        "english": (
                            "👋 *Welcome back to SabiSpend!*\n\n"
                            "I can help you with:\n\n"
                            "1. 📊 *Track sales, expenses & profit* - \"I bought rice for 15,000 naira\" or \"What's my profit today?\"\n"
                            "2. 💰 *Check balance* - \"How much money do I have?\"\n"
                            "3. 🔐 *Verify account* - Complete KYC verification\n"
                            + ("4. 💸 *Send money* - Transfer to other wallets\n" if has_wallet else "4. 🏦 *Open account* - Create BMONI wallet\n")
                            + "5. 🛡️ *Detect scams* - Forward suspicious messages\n\n"
                            "How can I assist you today?"
                        ),
                        "hausa": (
                            "👋 *Barka da dawowa zuwa SabiSpend!*\n\n"
                            "Zan iya taimaka maka da:\n\n"
                            "1. 📊 *Lura da kashe kuɗi da riba* - \"Na sayi shinkafa da naira 15,000\" ko \"Wane irin riba na samu yau?\"\n"
                            "2. 💰 *Duba ma'auni* - \"Nawa kudin da nake da shi?\"\n"
                            "3. 🔐 *Tabbatar da asusun* - Kammala tabbacin KYC\n"
                            + ("4. 💸 *Tura kuɗi* - Tura zuwa wasu wallet\n" if has_wallet else "4. 🏦 *Buɗe asusun* - Kirkiro wallet na BMONI\n")
                            + "5. 🛡️ *Gano damfara* - Tura saƙon da ake shakka\n\n"
                            "Yaya zan iya taimaka maka yau?"
                        ),
                        "igbo": (
                            "👋 *Nnọọ na SabiSpend!*\n\n"
                            "Enwere m ike inyere gị aka na:\n\n"
                            "1. 📊 *Soro mmefu ego na uru* - \"M zụtara osikapa iri puku na ise naira\" ma ọ bụ \"Kedu uru m nwetara taa?\"\n"
                            "2. 💰 *Lelee ego* - \"Ego ole ka m nwere?\"\n"
                            "3. 🔐 *Kwado akaụntụ* - Mezuo nyocha KYC\n"
                            + ("4. 💸 *Zipu ego* - Ziga na wallet ndị ọzọ\n" if has_wallet else "4. 🏦 *Mepee akaụntụ* - Mepụta wallet BMONI\n")
                            + "5. 🛡️ *Chọpụta aghụghọ* - Ziga ozi ndị na-enyo enyo\n\n"
                            "Kedu ka m ga-esi nyere gị aka taa?"
                        ),
                        "yoruba": (
                            "👋 *Ẹ káàbọ̀ padà sí SabiSpend!*\n\n"
                            "Mo lè ràn ọ́ lọ́wọ́ pẹ̀lú:\n\n"
                            "1. 📊 *Tọpinpin ìnáwó àti èrè* - \"Mo ra ìrẹsì fún ẹgbẹ̀rún mẹ́ẹ̀ẹ́dógún naira\" tàbí \"Èrè mélòó ni mo rí lónìí?\"\n"
                            "2. 💰 *Ṣàyẹ̀wò owó* - \"Owó mélòó ni mo ní?\"\n"
                            "3. 🔐 *Jẹ́rìísí iroyin* - Parí ìjẹ́rìísí KYC\n"
                            + ("4. 💸 *Fi owó ránṣẹ́* - Gbé sí àwọn wallet míràn\n" if has_wallet else "4. 🏦 *Ṣí iroyin* - Dá wallet BMONI\n")
                            + "5. 🛡️ *Ṣàwárí ẹ̀tàn* - Fi àwọn ìfiránsẹ́ tí o fura sí ránṣẹ́\n\n"
                            "Báwo ni mo ṣe lè ràn ọ́ lọ́wọ́ lónìí?"
                        )
                    }
                    
                    welcome_msg = welcome_messages.get(user_language, welcome_messages["english"])
                    # Get wallet status for language list
                    has_wallet = existing_account and existing_account.get("wallet") is not None
                    await send_response_with_language_list(from_number, welcome_msg, user_language, has_wallet)
                    return
            # ────────────────────────────────────────────────────────────

            # No translation needed - Gemma is multilingual and responds in user's language
            content_for_agent.append({
                "type": "text",
                "text": raw_text
            })

        # ---------- AUDIO ----------
        elif message_type == "audio":
            try:
                # Transcribe in correct language (STT transcribes to local language)
                transcribed_text = await process_audio_message(message, language=user_language)
                
                # No translation - Gemma understands the local language directly
                logger.info(f"🎙️ Voice transcribed ({user_language}): {transcribed_text}")
                
                content_for_agent.append({
                    "type": "text",
                    "text": f"[Voice]: {transcribed_text}"
                })
                should_respond_with_audio = True
            except Exception as e:
                logger.error(f"[bg] STT failed: {e}")
                await send_whatsapp_message(from_number, "Sorry, I couldn't process that voice message. Please try again.")
                return

        # ---------- IMAGE (INVOICE/RECEIPT OCR WORKFLOW) ----------
        elif message_type == "image":
            caption = message.get("image", {}).get("caption", "")
            image_media_id = message["image"]["id"]
            image_bytes = None
            _img_max_retries = 3

            for _attempt in range(1, _img_max_retries + 1):
                try:
                    logger.info(f"[bg] 📥 Downloading invoice/receipt image (attempt {_attempt}/{_img_max_retries})")
                    image_bytes = await download_media(image_media_id)
                    if not image_bytes:
                        raise ValueError("Downloaded image is empty")
                    logger.info(f"[bg] ✅ Image downloaded ({len(image_bytes)} bytes)")
                    break
                except Exception as dl_err:
                    logger.warning(f"[bg] Image download failed (attempt {_attempt}): {dl_err}")
                    if _attempt < _img_max_retries:
                        await asyncio.sleep(1.5 * _attempt)
                    else:
                        logger.error(f"[bg] Image download failed after {_img_max_retries} attempts: {dl_err}")
                        await send_whatsapp_message(from_number, "Sorry, I couldn't process that image. Please try again.")
                        return

            try:
                # Step 2: Try OCR on the image (optional — fallback to AI if it fails)
                logger.info("[bg] 🔍 Sending image to OCR/Vision API")
                ocr_hint = ""
                try:
                    ocr_result = await recognize_invoice_from_image(image_bytes)
                    if ocr_result.get("success"):
                        extracted_text = ocr_result.get("text", "")
                        amounts = ocr_result.get("amounts", [])
                        if amounts:
                            amounts_str = ", ".join([f"₦{amt['amount']:,.2f}" for amt in amounts[:3]])
                            ocr_hint = f"Extracted amounts: {amounts_str}"
                            logger.info(f"[bg] ✅ OCR extracted: {ocr_hint}")
                        else:
                            logger.warning("[bg] OCR returned no amounts — AI will analyze directly")
                    else:
                        logger.warning("[bg] OCR failed — sending image to AI directly")
                except Exception as ocr_err:
                    logger.warning(f"[bg] OCR unavailable ({ocr_err}) — sending image to AI directly")

                # Step 3: Send image (+ optional OCR hints) to AI
                data_uri = convert_to_data_uri(image_bytes, "image/jpeg")
                if ocr_hint:
                    hint_text = (
                        f"\n\n[System note: OCR detected these amounts: {ocr_hint}. "
                        f"Look at the image yourself to verify. Ask the user if this is an expense (stock purchase) "
                        f"or sales record, then confirm the amount before logging it.]"
                    )
                else:
                    hint_text = ""
                content_for_agent.append({
                    "type": "image_url",
                    "image_url": {"url": data_uri}
                })
                content_for_agent.append({
                    "type": "text",
                    "text": f"[Invoice/Receipt Image] Caption: {caption}{hint_text}\n\nLook at the image and extract the amount. Ask the user: 'I can see ₦[amount] on this receipt. Is this an expense (stock you bought) or sales you made today?'"
                })

            except Exception as e:
                logger.error(f"[bg] Image processing failed: {e}")
                await send_whatsapp_message(from_number, "Sorry, I couldn't process that image. Please try again.")
                return

        # ---------- UNSUPPORTED ----------
        else:
            # Unsupported type
            await send_whatsapp_message(from_number, "I can process text, voice messages, and images.")
            return

        # ── Inject user profile into agent context ─────────────
        user_profile = get_user_journey(thread_id)
        if user_profile.get("journey") == "onboarding_complete":
            business_type = user_profile.get("business_type", "trader")
            profile_label = {
                "trader": "This user is a market trader/seller.",
                "artisan": "This user is a small business owner/artisan.",
                "individual": "This user is an individual managing personal money.",
            }.get(business_type, "")
            if profile_label:
                for part in content_for_agent:
                    if isinstance(part, dict) and part.get("type") == "text":
                        part["text"] = f"[User profile: {profile_label}]\n\n{part['text']}"
                        break
        # ────────────────────────────────────────────────────────────────

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

        # ---------- CALL UNIFIED AGENT DIRECTLY ----------
        # Extract user's question from content_for_agent
        user_question = ""
        original_content = None
        for item in content_for_agent:
            if item.get("type") == "text":
                user_question = item.get("text", "")
                original_content = item.get("original_text")
                break

        logger.info(f"[bg] 📤 Calling unified agent for thread {thread_id}")

        # Sentence boundary regex used for streaming TTS pipeline
        _sent_re = re.compile(r'(?<=[.!?])\s+')

        # Holds asyncio.Tasks for concurrent TTS
        pre_tts_tasks: list = []
        _already_translated = False  # set True when non-English streaming pipeline handles translation
        dashboard_conversation_id = None  # set after microservice logs the conversation

        try:
            if should_respond_with_audio and user_language != "english":
                    # Streaming path: Gemma response sentences go directly to TTS.
                    text_content = next(
                        (item.get("text", "") for item in content_for_agent if item.get("type") == "text"),
                        ""
                    )
                    # Gemma responds in user's language directly - no translation needed
                    logger.info(f"[bg] 🌊 Streaming: LLM → TTS ({user_language} voice)")
                    response_text = ""
                    text_buf = ""
                    _tts_svc = get_tts_service(user_language)
                    if user_language == "hausa":
                        _voice_param = HAUSA_TTS_VOICE
                    elif user_language == "igbo":
                        _voice_param = IGBO_TTS_VOICE
                    elif user_language == "yoruba":
                        _voice_param = YORUBA_TTS_VOICE
                    else:
                        _voice_param = ENGLISH_TTS_VOICE

                    # Call unified agent with streaming
                    async for chunk in unified_agent.get_response_stream(
                        content=user_question,
                        thread_id=thread_id,
                        user_name=user_name,
                        message_type="voice",
                        language=user_language,
                        original_content=original_content
                    ):
                        response_text += chunk
                        text_buf += chunk
                        parts = _sent_re.split(text_buf)
                        if len(parts) > 1:
                            for sentence in parts[:-1]:
                                sentence = sentence.strip()
                                if len(sentence) <= 3:
                                    continue
                                logger.info(f"[bg] 🎤 TTS: {sentence[:60]}")
                                tts_input = sentence
                                pre_tts_tasks.append(asyncio.create_task(
                                    asyncio.to_thread(_tts_svc.synthesize_sync, tts_input, _voice_param)
                                ))
                            text_buf = parts[-1]

                    # Flush leftover buffer
                    if text_buf.strip() and len(text_buf.strip()) > 3:
                        tts_input = text_buf.strip()
                        pre_tts_tasks.append(asyncio.create_task(
                            asyncio.to_thread(_tts_svc.synthesize_sync, tts_input, _voice_param)
                        ))

                    logger.info(f"[bg] ✅ Streamed response, {len(pre_tts_tasks)} TTS tasks queued")

            elif should_respond_with_audio and user_language == "english":
                    # ── STREAMING path: LLM streams → TTS tasks start immediately ─
                    logger.info("[bg] 🌊 Streaming agent + concurrent TTS (English voice)")
                    response_text = ""
                    text_buf = ""
                    tts_svc = get_tts_service("english")

                    # Call unified agent with streaming
                    async for chunk in unified_agent.get_response_stream(
                        content=user_question,
                        thread_id=thread_id,
                        user_name=user_name,
                        message_type="voice",
                        language=user_language,
                        original_content=original_content
                    ):
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

                    # Fallback: if streaming returned error, retry with non-streaming
                    _error_phrases = ("sorry, something went wrong", "i'm having trouble", "please try again")
                    if len(response_text) < 60 and any(p in response_text.lower() for p in _error_phrases):
                        logger.warning("[bg] ⚠️ Streaming returned error response, falling back to non-streaming")
                        pre_tts_tasks.clear()
                        response_text = await unified_agent.get_response(
                            content=user_question,
                            thread_id=thread_id,
                            user_name=user_name,
                            message_type="voice",
                            language=user_language,
                            original_content=original_content
                        )

                    logger.info(f"[bg] ✅ Streamed {len(response_text)} chars, {len(pre_tts_tasks)} TTS tasks running")

            else:
                    # ── Standard non-streaming path ──────────────────────────────
                    response_text = await unified_agent.get_response(
                        content=content_for_agent,
                        thread_id=thread_id,
                        user_name=user_name,
                        message_type="voice" if should_respond_with_audio else "text",
                        language=user_language,
                        original_content=original_content
                    )
                    if not response_text:
                        logger.error("[bg] ❌ Agent returned empty response")
                        response_text = "I received your message. How can I help you?"
                    logger.info(f"[bg] ✅ Agent response: {response_text[:100]}...")

        except Exception as e:
            logger.error(f"[bg] ❌ Error calling agent: {e}")
            logger.error(f"Error details:Agent call failed — user: {from_number}, lang: {user_language}")
            await send_whatsapp_message(from_number, "Something went wrong. Please try again.")
            return

        # No translation needed - Gemma responds in user's language directly

        # Clean up markdown for WhatsApp display
        response_text = clean_whatsapp_message(response_text)

        # === SAVE CONVERSATION TO MONGODB (Old feedback system for backward compatibility) ===
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
                        return

                # Standard text response + enhanced buttons
                if len(response_text) > 1024:
                    await send_whatsapp_message(from_number, message_text=response_text)
                else:
                    # Get wallet status for buttons
                    from bmoni_store import bmoni_store
                    normalized_phone = from_number if from_number.startswith("+") else f"+{from_number}"
                    existing_account = bmoni_store.get_by_phone(normalized_phone)
                    has_wallet = existing_account and existing_account.get("wallet") is not None
                    await send_response_with_language_list(from_number, response_text, user_language, has_wallet)

            except Exception as e:
                logger.error(f"[bg] ❌ Operation failed: {e}", exc_info=True)
                await send_whatsapp_message(from_number, message_text=response_text)
        else:
            # Standard text response with enhanced buttons
            # Get wallet status for buttons
            from bmoni_store import bmoni_store
            normalized_phone = from_number if from_number.startswith("+") else f"+{from_number}"
            existing_account = bmoni_store.get_by_phone(normalized_phone)
            has_wallet = existing_account and existing_account.get("wallet") is not None
            await send_response_with_language_list(from_number, response_text, user_language, has_wallet)

    except Exception as e:
        logger.exception("[bg] ❌ Unhandled exception in background task")
        logger.error(f"Error details:Unhandled exception in message processing — user: {from_number}")
        try:
            await send_whatsapp_message(from_number, "Something went wrong on our side. Please try again later.")
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
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 4000)))