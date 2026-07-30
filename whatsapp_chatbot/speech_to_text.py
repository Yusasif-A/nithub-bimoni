import os
import tempfile
import logging
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

LINGUACENTER_URL = "https://inference.linguacenter.net/transcribe"


class SpeechToTextError(Exception):
    pass

class SpeechToText:
    """English speech-to-text.
    Primary: OpenAI-compatible endpoint (Lightning AI /en/v1).
    Fallback: linguacenter.net direct POST /transcribe.
    """

    def __init__(self):
        primary_raw = os.getenv("ENGLISH_STT_API_URL", "")
        self.primary_url = self._normalize(primary_raw) if primary_raw else None
        self.fallback_url = os.getenv("ENGLISH_STT_FALLBACK_URL", LINGUACENTER_URL)
        logger.info(f"✅ English STT initialized: {self.primary_url} | fallback: {self.fallback_url}")

    @staticmethod
    def _normalize(url: str) -> str:
        url = url.rstrip('/')
        if not url.endswith('/v1'):
            url = url + '/v1'
        return url

    @staticmethod
    def _is_linguacenter(url: str) -> bool:
        return "linguacenter.net" in url

    async def transcribe(self, audio_data: bytes) -> str:
        if not audio_data:
            raise ValueError("Audio data cannot be empty")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            temp_file_path = tmp.name

        try:
            if self.primary_url:
                try:
                    return self._transcribe_openai(self.primary_url, temp_file_path)
                except Exception as primary_err:
                    logger.warning(f"⚠️ Primary English STT failed ({primary_err}), switching to fallback: {self.fallback_url}")

            # Fallback
            if self._is_linguacenter(self.fallback_url):
                return self._transcribe_linguacenter(temp_file_path)
            else:
                return self._transcribe_openai(self._normalize(self.fallback_url), temp_file_path)

        except SpeechToTextError:
            raise
        except Exception as e:
            raise SpeechToTextError(f"Speech-to-text conversion failed: {e}") from e
        finally:
            os.unlink(temp_file_path)

    def _transcribe_openai(self, base_url: str, temp_file_path: str) -> str:
        logger.info(f"📤 English STT: Sending to {base_url}")
        client = OpenAI(base_url=base_url, api_key="dummy")
        with open(temp_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="en"
            )
        result = str(transcription).strip()
        if not result:
            raise SpeechToTextError("Transcription result is empty")
        logger.info(f"✅ English STT transcribed: '{result}'")
        return result

    def _transcribe_linguacenter(self, temp_file_path: str) -> str:
        logger.info(f"📤 English STT: Sending to {self.fallback_url} (linguacenter direct)")
        with open(temp_file_path, "rb") as audio_file:
            response = requests.post(
                self.fallback_url,
                files={"audio": ("audio.wav", audio_file, "audio/wav")},
                timeout=60
            )
        if response.status_code != 200:
            raise SpeechToTextError(f"Linguacenter STT failed: {response.status_code} {response.text}")
        result = response.json().get("text", "").strip()
        if not result:
            raise SpeechToTextError("Linguacenter transcription result is empty")
        logger.info(f"✅ English STT (linguacenter) transcribed: '{result}'")
        return result
