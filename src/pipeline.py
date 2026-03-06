"""
YouTube Automation Pipeline — Main Orchestrator
Runs: Script → Voice → Visuals → Edit → Upload
"""

import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

from script_generator import ScriptGenerator
from voiceover import VoiceoverGenerator
from visuals import VisualsFetcher
from video_editor import VideoEditor
from uploader import YouTubeUploader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log"),
    ],
)
log = logging.getLogger(__name__)


def run_pipeline(topic: str, schedule_time: str = None, dry_run: bool = False):
    """
    Full end-to-end pipeline for a single video.

    Args:
        topic:          What the video is about, e.g. "10 Python tips for beginners"
        schedule_time:  ISO-8601 string to schedule upload, or None to publish now
        dry_run:        If True, skip the YouTube upload step
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info(f"Pipeline started  |  topic='{topic}'  |  run={run_id}")
    log.info("=" * 60)

    # ── 1. Script ────────────────────────────────────────────────
    log.info("STEP 1/5 — Generating script …")
    generator = ScriptGenerator()
    script = generator.generate(topic)
    script_path = output_dir / "script.json"
    script_path.write_text(json.dumps(script, indent=2))
    log.info(f"Script saved → {script_path}")

    # ── 2. Voiceover ─────────────────────────────────────────────
    log.info("STEP 2/5 — Generating voiceover …")
    voice = VoiceoverGenerator()
    audio_path = voice.generate(script["narration"], output_dir / "narration.mp3")
    log.info(f"Audio saved  → {audio_path}")

    # ── 3. Visuals ───────────────────────────────────────────────
    log.info("STEP 3/5 — Fetching stock footage …")
    fetcher = VisualsFetcher()
    clips = fetcher.fetch_for_scenes(script["scenes"], output_dir / "clips")
    log.info(f"Downloaded {len(clips)} clips")

    # ── 4. Edit ──────────────────────────────────────────────────
    log.info("STEP 4/5 — Assembling video …")
    editor = VideoEditor()
    video_path = editor.assemble(
        audio_path=audio_path,
        clips=clips,
        script=script,
        output_path=output_dir / "final_video.mp4",
    )
    log.info(f"Video saved  → {video_path}")

    # ── 5. Upload ────────────────────────────────────────────────
    if dry_run:
        log.info("STEP 5/5 — DRY RUN: skipping YouTube upload")
        log.info(f"Video ready at: {video_path}")
    else:
        log.info("STEP 5/5 — Uploading to YouTube …")
        uploader = YouTubeUploader()
        video_id = uploader.upload(
            video_path=video_path,
            title=script["title"],
            description=script["description"],
            tags=script["tags"],
            schedule_time=schedule_time,
        )
        log.info(f"Uploaded! https://youtube.com/watch?v={video_id}")

    log.info("Pipeline complete ✓")
    return str(video_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Automation Pipeline")
    parser.add_argument("topic", help="Video topic, e.g. '5 Python tips for beginners'")
    parser.add_argument("--schedule", default=None, help="ISO-8601 publish time, e.g. 2024-12-01T18:00:00Z")
    parser.add_argument("--dry-run", action="store_true", help="Skip YouTube upload")
    args = parser.parse_args()

    run_pipeline(args.topic, schedule_time=args.schedule, dry_run=args.dry_run)
