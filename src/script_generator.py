"""
Script Generator
Uses Groq (free API) or local Ollama/Llama-3 to produce structured JSON scripts.
"""

import os
import json
import logging
import requests

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a professional YouTube scriptwriter.
Return ONLY valid JSON (no markdown, no extra text) in this exact shape:

{
  "title": "Compelling SEO video title",
  "description": "YouTube description (2-3 paragraphs + hashtags)",
  "tags": ["tag1", "tag2", "tag3"],
  "narration": "Full narration script the voiceover will read aloud.",
  "scenes": [
    {
      "id": 1,
      "keyword": "one or two word stock footage search term",
      "duration_seconds": 8,
      "caption": "Short on-screen caption text"
    }
  ]
}

Rules:
- 5-8 scenes total
- narration should be 90-150 seconds when read at normal pace
- keywords must be generic enough to find stock footage (e.g. "coding laptop", not "Python IDE")
- captions max 8 words
"""


class ScriptGenerator:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model_groq = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        self.model_ollama = os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, topic: str) -> dict:
        """Generate a structured script JSON for the given topic."""
        prompt = f"Write a YouTube script about: {topic}"

        if self.groq_api_key:
            log.info("Using Groq API …")
            return self._generate_groq(prompt)
        else:
            log.info("GROQ_API_KEY not set — falling back to local Ollama …")
            return self._generate_ollama(prompt)

    # ── Groq ──────────────────────────────────────────────────────
    def _generate_groq(self, prompt: str) -> dict:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_groq,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1500,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        return self._parse_json(raw)

    # ── Ollama ────────────────────────────────────────────────────
    def _generate_ollama(self, prompt: str) -> dict:
        url = f"{self.ollama_url}/api/chat"
        payload = {
            "model": self.model_ollama,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        raw = resp.json()["message"]["content"]
        return self._parse_json(raw)

    # ── Helpers ───────────────────────────────────────────────────
    def _parse_json(self, raw: str) -> dict:
        # Strip accidental markdown fences
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse script JSON: {e}\nRaw:\n{raw}")
            raise
