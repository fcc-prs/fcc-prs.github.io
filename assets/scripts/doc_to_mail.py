"""
Read a Google Doc and open a draft in Apple Mail.

Usage (from repo root):
    python3 assets/scripts/doc_to_mail.py [doc_id_or_url]

If no argument is given, uses the last doc created by draft_email_doc.py.
"""

import html
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CREDENTIALS_FILE = os.path.join(REPO_ROOT, "google_apps.json")
TOKEN_FILE = os.path.join(REPO_ROOT, "token.json")
LAST_DOC_FILE = os.path.join(REPO_ROOT, "assets", "json", "last_doc.json")
LAST_DOC_URL = "https://raw.githubusercontent.com/fcc-prs/fcc-prs.github.io/main/assets/json/last_doc.json"


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


def extract_doc_id(arg):
    m = re.search(r'/document/d/([a-zA-Z0-9_-]+)', arg)
    return m.group(1) if m else arg


def paragraph_to_html(para):
    """Convert a Docs paragraph element to an HTML string."""
    runs_html = []
    for el in para.get("elements", []):
        run = el.get("textRun")
        if not run:
            continue
        text = run.get("content", "").rstrip("\n")
        if not text:
            continue
        style = run.get("textStyle", {})
        escaped = html.escape(text)
        url = style.get("link", {}).get("url")
        bold = style.get("bold", False)

        if url:
            escaped = f'<a href="{html.escape(url)}">{escaped}</a>'
        if bold and not url:
            escaped = f"<strong>{escaped}</strong>"
        runs_html.append(escaped)
    return "".join(runs_html)


def para_plain_text(para):
    """Extract plain text from a paragraph (no HTML)."""
    return "".join(
        el["textRun"]["content"]
        for el in para.get("elements", [])
        if "textRun" in el
    ).strip()


def doc_to_subject_and_html(doc):
    paragraphs = [
        el["paragraph"]
        for el in doc["body"]["content"]
        if "paragraph" in el
    ]

    subject = ""
    body_paras = []

    for i, para in enumerate(paragraphs):
        if i == 0:
            # First paragraph is "Subject: ..." — extract as plain text
            subject = re.sub(r"^Subject:\s*", "", para_plain_text(para))
            continue
        line = paragraph_to_html(para)
        body_paras.append(line)

    # Build HTML body: consecutive empty lines → paragraph break
    html_parts = []
    buffer = []
    for line in body_paras:
        if line.strip():
            buffer.append(line)
        else:
            if buffer:
                html_parts.append("<p>" + "<br>".join(buffer) + "</p>")
                buffer = []
    if buffer:
        html_parts.append("<p>" + "<br>".join(buffer) + "</p>")

    body_html = (
        "<html><body style='font-family:sans-serif;font-size:14px;line-height:1.5'>"
        + "\n".join(html_parts)
        + "</body></html>"
    )

    return subject, body_html


def open_mail_draft(subject, body_html):
    # Write HTML to a temp file so AppleScript can read it without escaping issues
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(body_html)
        tmp_path = f.name

    script = f'''
set htmlPath to POSIX file "{tmp_path}"
set htmlContent to read htmlPath as «class utf8»
tell application "Mail"
    set newMsg to make new outgoing message with properties {{subject:"{subject}", visible:true}}
    set html content of newMsg to htmlContent
    tell newMsg
        make new to recipient with properties {{address:"fcc-ped-softwareandcomputing@cern.ch"}}
    end tell
    activate
end tell
'''
    subprocess.run(["osascript", "-e", script], check=True)
    os.unlink(tmp_path)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        doc_id = extract_doc_id(sys.argv[1])
    else:
        if os.path.exists(LAST_DOC_FILE):
            with open(LAST_DOC_FILE) as f:
                last = json.load(f)
            print(f"Using last doc from repo: {last.get('url', last['doc_id'])}")
        else:
            print(f"Fetching last doc from repository...")
            try:
                with urllib.request.urlopen(LAST_DOC_URL) as resp:
                    last = json.load(resp)
                print(f"Using last doc: {last.get('url', last['doc_id'])}")
            except Exception as e:
                print(f"Could not fetch last_doc.json from repository: {e}")
                print("Pass a doc ID/URL as an argument, or ensure assets/json/last_doc.json exists.")
                sys.exit(1)
        doc_id = last["doc_id"]
        if last.get("subject"):
            print(f"  Subject: {last['subject']}")
    print(f"Reading doc {doc_id}...")

    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)
    doc = service.documents().get(documentId=doc_id).execute()

    subject, body_html = doc_to_subject_and_html(doc)
    print(f"Subject: {subject}")
    print("Opening Mail draft...")
    open_mail_draft(subject, body_html)
    print("Done.")
