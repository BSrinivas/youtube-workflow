"""
Visuals Fetcher
Downloads royalty-free stock footage from Pexels API (free, 200 req/hr).
Get your free key at: https://www.pexels.com/api/
"""

import os
import time
import logging
import requests
from pathlib import Path

log = logging.getLogger(__name__)

PEXELS_API = "https://api.pexels.com/videos/search"
PREFERRED_QUALITIES = ["hd", "sd", "mobile"]


class VisualsFetcher:
    def __init__(self):
        self.api_key = os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            raise EnvironmentError("PEXELS_API_KEY environment variable not set. Get a free key at pexels.com/api")

    def fetch_for_scenes(self, scenes: list, output_dir: Path) -> list:
        """
        Download one video clip per scene.
        Returns list of dicts: [{scene_id, clip_path, duration_seconds, caption}]
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []

        for scene in scenes:
            scene_id = scene["id"]
            keyword = scene["keyword"]
            duration = scene.get("duration_seconds", 8)
            caption = scene.get("caption", "")

            log.info(f"  Scene {scene_id}: searching '{keyword}' …")
            clip_path = self._download_clip(keyword, output_dir / f"scene_{scene_id:02d}.mp4")

            if clip_path:
                results.append({
                    "scene_id": scene_id,
                    "clip_path": clip_path,
                    "duration_seconds": duration,
                    "caption": caption,
                })
            else:
                log.warning(f"  No clip found for '{keyword}' — scene {scene_id} will be skipped")

            time.sleep(0.5)   # Be polite to the API

        return results

    def _download_clip(self, keyword: str, output_path: Path, min_duration: int = 5) -> Path | None:
        headers = {"Authorization": self.api_key}
        params = {"query": keyword, "per_page": 5, "orientation": "landscape"}

        resp = requests.get(PEXELS_API, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        videos = resp.json().get("videos", [])

        if not videos:
            return None

        # Pick first video that's long enough
        for video in videos:
            if video["duration"] < min_duration:
                continue
            url = self._best_file_url(video["video_files"])
            if url:
                return self._stream_download(url, output_path)

        # Fallback: just take the first one regardless of duration
        url = self._best_file_url(videos[0]["video_files"])
        return self._stream_download(url, output_path) if url else None

    def _best_file_url(self, files: list) -> str | None:
        for quality in PREFERRED_QUALITIES:
            for f in files:
                if f.get("quality") == quality and f.get("file_type") == "video/mp4":
                    return f["link"]
        return files[0]["link"] if files else None

    def _stream_download(self, url: str, output_path: Path, retries: int = 3) -> Path:
        for attempt in range(1, retries + 1):
            try:
                with requests.get(url, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(output_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            f.write(chunk)
                log.info(f"    Downloaded -> {output_path.name}")
                return output_path
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                log.warning(f"    Download attempt {attempt}/{retries} failed: {e}")
                if attempt == retries:
                    raise
                time.sleep(2 * attempt)
