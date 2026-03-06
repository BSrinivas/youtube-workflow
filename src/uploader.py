"""
YouTube Uploader
Uses YouTube Data API v3 (free, ~6 uploads/day on unverified accounts).
Auth: OAuth 2.0 via client_secrets.json or SERVICE_ACCOUNT_JSON env var.
"""

import os
import json
import logging
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"
CLIENT_SECRETS = os.getenv("CLIENT_SECRETS_FILE", "client_secrets.json")


class YouTubeUploader:
    def __init__(self):
        self.service = self._authenticate()

    def upload(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list,
        schedule_time: str = None,   # ISO-8601, e.g. "2024-12-01T18:00:00Z"
        category_id: str = "28",     # 28 = Science & Technology
        privacy: str = "public",
    ) -> str:
        """
        Upload video to YouTube and return the video ID.
        If schedule_time is set, the video is published at that time (privacy='private' until then).
        """
        video_path = Path(video_path)
        log.info(f"Uploading '{title}' ({video_path.stat().st_size / 1e6:.1f} MB) …")

        status = {"privacyStatus": privacy}
        if schedule_time:
            status = {"privacyStatus": "private", "publishAt": schedule_time}

        body = {
            "snippet": {
                "title": title[:100],           # YouTube max
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": category_id,
                "defaultLanguage": "en",
            },
            "status": status,
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,   # 10 MB chunks
        )

        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        video_id = self._resumable_upload(request)
        log.info(f"Upload complete → https://youtube.com/watch?v={video_id}")
        return video_id

    # ── Auth ──────────────────────────────────────────────────────

    def _authenticate(self):
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CLIENT_SECRETS):
                    raise FileNotFoundError(
                        f"OAuth client secrets not found at '{CLIENT_SECRETS}'.\n"
                        "Download from: https://console.cloud.google.com → APIs & Services → Credentials"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        return build("youtube", "v3", credentials=creds)

    # ── Resumable upload with progress ────────────────────────────

    @staticmethod
    def _resumable_upload(request):
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                log.info(f"  Upload progress: {pct}%")
        return response["id"]
