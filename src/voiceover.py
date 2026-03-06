"""
Voiceover Generator
Uses Microsoft Edge-TTS (edge-tts) — free, no API key, 400+ voices.
"""

import asyncio
import logging
from pathlib import Path

import edge_tts

log = logging.getLogger(__name__)

# Pick any voice from: edge-tts --list-voices
DEFAULT_VOICE = "en-US-AriaNeural"   # Natural, friendly female voice
# Other great options:
#   en-US-GuyNeural       — Male US
#   en-GB-SoniaNeural     — Female British
#   en-AU-NatashaNeural   — Female Australian
#   en-US-JennyNeural     — Female, conversational


class VoiceoverGenerator:
    def __init__(self, voice: str = DEFAULT_VOICE, rate: str = "+0%", volume: str = "+0%"):
        self.voice = voice
        self.rate = rate      # e.g. "+10%" to speed up
        self.volume = volume

    def generate(self, text: str, output_path: Path) -> Path:
        """Convert text to speech and save as MP3."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        log.info(f"Generating voiceover | voice={self.voice} | chars={len(text)}")
        asyncio.run(self._synthesize(text, output_path))
        log.info(f"Voiceover saved → {output_path}")
        return output_path

    async def _synthesize(self, text: str, output_path: Path):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
        )
        await communicate.save(str(output_path))

    def list_voices(self, language_filter: str = "en-") -> list:
        """Return all available voices (optionally filtered by language prefix)."""
        async def _list():
            voices = await edge_tts.list_voices()
            return [v for v in voices if v["ShortName"].startswith(language_filter)]
        return asyncio.run(_list())
