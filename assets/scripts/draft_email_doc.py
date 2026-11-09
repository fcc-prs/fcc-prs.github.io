"""
Create a Google Doc draft of the weekly FCC software changes email.

Usage (from repo root):
    python3 assets/scripts/draft_email_doc.py          # fetch live from fcc-prs.github.io
    python3 assets/scripts/draft_email_doc.py --local  # read assets/json/summary.json on disk
"""

import argparse
import json
import os
import re
import urllib.request
from datetime import date, timedelta

import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

INDICO_CATEG_URL = "https://indico.cern.ch/export/categ/5666.json"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CREDENTIALS_FILE = os.path.join(REPO_ROOT, "google_apps.json")
TOKEN_FILE = os.path.join(REPO_ROOT, "token.json")
LAST_DOC_FILE = os.path.join(REPO_ROOT, "assets", "json", "last_doc.json")
SUMMARY_URL = "https://fcc-prs.github.io/assets/json/summary.json"


def compute_meeting_window():
    """Return (start, end) as date objects: next Tuesday through the following Tuesday."""
    today = date.today()
    days_until_tuesday = (1 - today.weekday()) % 7 or 7  # 1 = Tuesday
    start = today + timedelta(days=days_until_tuesday)
    end = start + timedelta(days=7)
    return start, end


def fetch_indico_meetings(start, end):
    """Fetch PS&C events from Indico between start and end (date objects).
    Returns list of {title, url, day} dicts sorted by date. Returns [] on any error."""
    url = f"{INDICO_CATEG_URL}?from={start}&to={end}&detail=events"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
        meetings = []
        for ev in data.get("results", []):
            start_info = ev.get("startDate", {})
            dt = date.fromisoformat(start_info.get("date", ""))
            meetings.append({
                "title": ev["title"],
                "url": ev["url"],
                "day": dt.strftime("%A"),
                "date": dt,
            })
        meetings.sort(key=lambda m: m["date"])
        return meetings
    except Exception as e:
        print(f"Warning: could not fetch Indico meetings: {e}")
        return []


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def parse_markdown_segments(text):
    """Parse markdown into (display_text, url_or_None, bold) tuples."""
    segments = []
    pattern = re.compile(
        r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*'  # **[text](url)**  → bold link
        r'|\[([^\]]+)\]\(([^)]+)\)'          # [text](url)      → link
        r'|\*\*([^*\n]+)\*\*'               # **text**         → bold
        r'|`([^`]+)`'                        # `code`           → plain
    )
    last_end = 0
    for m in pattern.finditer(text):
        if m.start() > last_end:
            segments.append((text[last_end:m.start()], None, False))
        if m.group(1):    # **[text](url)**
            segments.append((m.group(1), m.group(2), True))
        elif m.group(3):  # [text](url)
            segments.append((m.group(3), m.group(4), False))
        elif m.group(5):  # **text**
            segments.append((m.group(5), None, True))
        elif m.group(6):  # `code`
            segments.append((m.group(6), None, False))
        last_end = m.end()
    if last_end < len(text):
        segments.append((text[last_end:], None, False))
    return segments


def build_doc_parts(data, meetings=None):
    """
    Returns (subject, full_text, styles) where
    styles = [(char_start, char_end, url_or_None, bold), ...].
    char offsets are 0-indexed into full_text.
    """
    period_start = data.get("period_start", "")
    period_end = data.get("period_end", "")
    bullets = data.get("summary", [])

    subject = f"[FCC PS&C] Summary ({period_start} – {period_end})"
    subject_line = f"Subject: {subject}\n\n"

    intro = (
        f"Dear all,\n\n"
        f"Here is a summary of the most notable pull requests merged in the FCC/Key4hep "
        f"software ecosystem during the previous week (ending {period_end}).\n\n"
    )

    outro_url = "https://fcc-prs.github.io/summary.html"
    outro_prefix = "\n\nFull details and all merged PRs are available at "
    outro_suffix = (
        ". Did we miss something interesting and/or newsworthy? "
        "Please let David and Brieuc know so we can include it in our next summary."
        "\n\nBest regards,\nBrieuc and David"
    )
    outro = outro_prefix + outro_url + outro_suffix

    # Build a flat list of (text, url, bold) parts
    parts = []
    parts.append((subject_line, None, True))
    if meetings:
        parts.append(("PS&C meetings this week include ", None, False))
        for i, m in enumerate(meetings):
            if i > 0:
                sep = " and " if i == len(meetings) - 1 else ", "
                parts.append((sep, None, False))
            parts.append((m["title"], None, False))
            parts.append((" (", None, False))
            parts.append((m["url"], m["url"], False))
            parts.append((f") on {m['day']}", None, False))
        parts.append((".\n\n", None, False))
    parts.append((intro, None, False))
    for i, bullet in enumerate(bullets):
        if i > 0:
            parts.append(("\n\n", None, False))
        parts.extend(parse_markdown_segments(bullet.strip()))
    parts.append((outro_prefix, None, False))
    parts.append((outro_url, outro_url, False))
    parts.append((outro_suffix, None, False))

    # Concatenate into full_text and record style ranges
    full_text = ""
    styles = []
    for (txt, url, bold) in parts:
        start = len(full_text)
        full_text += txt
        end = len(full_text)
        if url or bold:
            styles.append((start, end, url, bold))

    return subject, full_text, styles


def create_doc(subject, full_text, styles, timeout=120):
    creds = get_credentials()
    authorized_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=timeout))
    service = build("docs", "v1", http=authorized_http)

    doc = service.documents().create(body={"title": f"DRAFT — {subject}"}).execute()
    doc_id = doc["documentId"]

    # Insert the full plain text in one shot at index 1
    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"insertText": {"location": {"index": 1}, "text": full_text}}]},
    ).execute()

    # Apply link / bold styles.
    # After inserting at doc index 1, character i in full_text lives at doc index 1+i.
    # Google Docs ranges are [startIndex, endIndex) (endIndex exclusive).
    requests = []
    for (start, end, url, bold) in styles:
        text_style = {}
        fields = []
        if url:
            text_style["link"] = {"url": url}
            fields.append("link")
        if bold:
            text_style["bold"] = True
            fields.append("bold")
        requests.append({
            "updateTextStyle": {
                "range": {"startIndex": 1 + start, "endIndex": 1 + end},
                "textStyle": text_style,
                "fields": ",".join(fields),
            }
        })

    if requests:
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests},
        ).execute()

    # Set permissions via Drive API
    drive = build("drive", "v3", http=authorized_http)
    # Anyone with the link can comment
    drive.permissions().create(
        fileId=doc_id,
        body={"type": "anyone", "role": "commenter"},
    ).execute()
    # brieucfra@gmail.com as editor
    drive.permissions().create(
        fileId=doc_id,
        body={"type": "user", "role": "writer", "emailAddress": "brieucfra@gmail.com"},
        sendNotificationEmail=False,
    ).execute()
    # david.lange@princeton.edu as editor with notification (primary alert that doc is ready)
    drive.permissions().create(
        fileId=doc_id,
        body={"type": "user", "role": "writer", "emailAddress": "david.lange@princeton.edu"},
        sendNotificationEmail=True,
    ).execute()

    return doc_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true",
                        help="Read summary.json from disk instead of fetching the live URL")
    args = parser.parse_args()

    if args.local:
        local_path = os.path.join(REPO_ROOT, "assets", "json", "summary.json")
        print(f"Reading {local_path}...")
        with open(local_path) as f:
            data = json.load(f)
    else:
        print(f"Fetching {SUMMARY_URL}...")
        with urllib.request.urlopen(SUMMARY_URL) as resp:
            data = json.load(resp)

    start, end = compute_meeting_window()
    print(f"Fetching Indico meetings {start} – {end}...")
    meetings = fetch_indico_meetings(start, end)
    print(f"Found {len(meetings)} meeting(s)")
    subject, full_text, styles = build_doc_parts(data, meetings=meetings)
    print(f"Subject: {subject}")
    print(f"Doc length: {len(full_text)} chars, {len(styles)} styled spans")
    print("Creating Google Doc...")
    doc_id = create_doc(subject, full_text, styles)
    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"Done: {url}")

    with open(LAST_DOC_FILE, "w") as f:
        json.dump({"doc_id": doc_id, "url": url, "subject": subject}, f)
    print(f"Saved doc ID to {LAST_DOC_FILE}")
