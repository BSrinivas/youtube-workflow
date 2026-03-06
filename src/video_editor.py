"""
Video Editor
Assembles voiceover + stock clips + auto-captions using MoviePy & FFmpeg.
Whisper (openai-whisper, free) generates word-level subtitle timing.
"""

import logging
import os
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

FFMPEG = os.getenv(
    "FFMPEG_PATH",
    r"C:\Users\srini\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",
)


class VideoEditor:
    def __init__(self, resolution=(1920, 1080), fps=30):
        self.resolution = resolution
        self.fps = fps

    def assemble(self, audio_path: Path, clips: list, script: dict, output_path: Path) -> Path:
        """
        Full assembly pipeline:
        1. Trim/loop each clip to its target duration
        2. Concatenate clips
        3. Mix in voiceover audio
        4. Burn in captions using Whisper timestamps
        5. Export final MP4
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = output_path.parent / "tmp"
        tmp.mkdir(exist_ok=True)

        log.info("  Trimming clips to scene durations …")
        trimmed = self._trim_clips(clips, tmp)

        log.info("  Concatenating clips …")
        concat_path = tmp / "concat.mp4"
        self._concatenate(trimmed, concat_path)

        log.info("  Mixing audio …")
        mixed_path = tmp / "mixed.mp4"
        self._mix_audio(concat_path, audio_path, mixed_path)

        log.info("  Generating captions with Whisper …")
        srt_path = tmp / "captions.srt"
        self._generate_captions(audio_path, srt_path)

        log.info("  Burning captions into video …")
        self._burn_captions(mixed_path, srt_path, output_path)

        log.info(f"  Final video → {output_path}")
        return output_path

    # ── Step helpers ──────────────────────────────────────────────

    def _trim_clips(self, clips: list, tmp_dir: Path) -> list:
        trimmed = []
        for c in clips:
            out = tmp_dir / f"trimmed_{c['scene_id']:02d}.mp4"
            dur = c["duration_seconds"]
            # Scale to target resolution, trim/loop, strip audio
            cmd = [
                FFMPEG, "-y",
                "-stream_loop", "-1",          # loop if clip is too short
                "-i", str(c["clip_path"]),
                "-t", str(dur),
                "-vf", f"scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=decrease,"
                       f"pad={self.resolution[0]}:{self.resolution[1]}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-r", str(self.fps),
                "-an",                          # no audio from stock clip
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                str(out),
            ]
            self._run(cmd)
            trimmed.append(out)
        return trimmed

    def _concatenate(self, clip_paths: list, output: Path):
        list_file = output.parent / "clip_list.txt"
        list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in clip_paths))
        cmd = [
            FFMPEG, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output),
        ]
        self._run(cmd)

    def _mix_audio(self, video: Path, audio: Path, output: Path):
        cmd = [
            FFMPEG, "-y",
            "-i", str(video),
            "-i", str(audio),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            str(output),
        ]
        self._run(cmd)

    def _generate_captions(self, audio_path: Path, srt_path: Path):
        """Use openai-whisper to transcribe audio → SRT subtitles."""
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path), word_timestamps=False)
            self._write_srt(result["segments"], srt_path)
        except ImportError:
            log.warning("whisper not installed — skipping captions (pip install openai-whisper)")
            srt_path.write_text("")  # empty SRT, FFmpeg will just skip

    def _write_srt(self, segments: list, srt_path: Path):
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._fmt_time(seg["start"])
            end = self._fmt_time(seg["end"])
            lines.append(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n")
        srt_path.write_text("\n".join(lines))

    def _burn_captions(self, video: Path, srt: Path, output: Path):
        if srt.stat().st_size == 0:
            # No captions — just copy
            import shutil
            shutil.copy(video, output)
            return

        style = (
            "FontName=Arial,FontSize=22,PrimaryColour=&HFFFFFF,"
            "OutlineColour=&H000000,Outline=2,Bold=1,"
            "Alignment=2,MarginV=40"
        )
        # ffmpeg subtitles filter needs forward slashes and escaped colons on Windows
        srt_escaped = str(srt.resolve()).replace("\\", "/").replace(":", "\\:")
        cmd = [
            FFMPEG, "-y",
            "-i", str(video),
            "-vf", f"subtitles='{srt_escaped}':force_style='{style}'",
            "-c:a", "copy",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            str(output),
        ]
        self._run(cmd)

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    @staticmethod
    def _run(cmd: list):
        log.debug("FFmpeg: " + " ".join(str(c) for c in cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.error(f"FFmpeg error:\n{result.stderr[-1000:]}")
            raise RuntimeError(f"FFmpeg failed: {cmd[0]}")
