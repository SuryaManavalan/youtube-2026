#!/usr/bin/env python3
"""Upload rendered Shorts to YouTube.

Usage:
  python3 tools/upload_youtube.py --auth-only
  python3 tools/upload_youtube.py "<episode-dir>" [slug ...]
      [--privacy private|unlisted|public]

Reads <episode-dir>/clips.json for per-clip title + caption (caption becomes
the video description; falls back to title) and uploads
<episode-dir>/SHORTS/<slug>.mp4. Default privacy: private (flip in Studio or
re-run with --privacy after review).

Auth: OAuth client in ~/.yt_client_secret.json, cached token in
~/.yt_token.json. First run prints a URL to open in your browser; the local
redirect server catches the approval (WSL2: Windows browser -> localhost
forwards automatically).

Quota: uploads cost 1600 units of the default 10,000/day -> ~6 uploads/day.
Unverified API projects force uploads to private until Google review.
"""
import argparse, json, os, sys
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT = os.path.expanduser("~/.yt_client_secret.json")
TOKEN = os.path.expanduser("~/.yt_token.json")
CATEGORY_TECH = "28"


def get_service():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
        creds = flow.run_local_server(
            port=8090, open_browser=False,
            authorization_prompt_message="\nOpen this URL to authorize:\n{url}\n")
    with open(TOKEN, "w") as f:
        f.write(creds.to_json())
    os.chmod(TOKEN, 0o600)
    return build("youtube", "v3", credentials=creds)


def upload(yt, path, title, description, privacy, publish_at=None):
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
    if publish_at:
        status["privacyStatus"] = "private"   # required with publishAt
        status["publishAt"] = publish_at.isoformat()
    body = {
        "snippet": {"title": title, "description": description,
                    "categoryId": CATEGORY_TECH},
        "status": status,
    }
    media = MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%", end="\r")
    when = f"scheduled {publish_at:%Y-%m-%d %H:%M %Z}" if publish_at else privacy
    print(f"  https://youtube.com/shorts/{resp['id']}  ({when})")
    return resp["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?")
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--privacy", default="private",
                    choices=["private", "unlisted", "public"])
    ap.add_argument("--auth-only", action="store_true")
    ap.add_argument("--daily-from", metavar="ISO_DATETIME",
                    help="schedule publishing one clip per day starting at "
                         "this time, e.g. 2026-07-21T12:00:00-07:00")
    args = ap.parse_args()

    yt = get_service()
    if args.auth_only:
        print("auth OK, token cached")
        return
    if not args.episode:
        sys.exit("episode dir required (or --auth-only)")

    clips = json.load(open(os.path.join(args.episode, "clips.json")))["clips"]
    want = set(args.slugs)
    start = datetime.fromisoformat(args.daily_from) if args.daily_from else None
    results, i = {}, 0
    for c in clips:
        if want and c["slug"] not in want:
            continue
        path = os.path.join(args.episode, "SHORTS", f"{c['slug']}.mp4")
        if not os.path.exists(path):
            print(f"SKIP {c['slug']}: {path} missing")
            continue
        desc = c.get("caption", c["title"])
        publish_at = start + timedelta(days=i) if start else None
        i += 1
        print(f"uploading {c['slug']}: {c['title']!r}")
        results[c["slug"]] = upload(yt, path, c["title"], desc,
                                    args.privacy, publish_at)
    log = os.path.join(args.episode, "work", "youtube_uploads.json")
    prev = json.load(open(log)) if os.path.exists(log) else {}
    prev.update(results)
    json.dump(prev, open(log, "w"), indent=1)
    print(f"{len(results)} uploaded; ids logged to {log}")


main()
