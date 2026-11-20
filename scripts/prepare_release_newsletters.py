#!/usr/bin/env python3
"""Prepare EmailOctopus newsletter drafts from released music. Never sends email."""
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "email-templates" / "drafts"
KINDS = {"single": "SINGLE", "ep": "EP", "album": "ALBUM"}

def https_url(value):
    if not isinstance(value, str):
        return False
    u = urlparse(value)
    return u.scheme == "https" and bool(u.hostname) and not u.username and not u.password

def release_info(item):
    slug, title, kind = item.get("id"), item.get("title"), item.get("type")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]{1,80}", slug):
        raise ValueError(f"Invalid release id: {slug!r}")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"Release {slug}: missing title")
    if kind not in KINDS:
        raise ValueError(f"Release {slug}: type must be single, ep or album")
    if not https_url(item.get("cover")):
        raise ValueError(f"Release {slug}: public HTTPS cover required")
    platforms = item.get("platforms")
    if not isinstance(platforms, list) or not any(
        isinstance(p, dict) and isinstance(p.get("name"), str)
        and p.get("name", "").strip() and https_url(p.get("url"))
        for p in platforms
    ):
        raise ValueError(f"Release {slug}: at least one valid listening link required")
    return slug, title.strip(), KINDS[kind]

def main():
    releases = json.loads((ROOT / "releases.json").read_text(encoding="utf-8")).get("releases")
    if not isinstance(releases, list):
        raise ValueError("releases.json must contain a releases array")
    template = (ROOT / "email-templates" / "new-release.html").read_text(encoding="utf-8")
    markers = ("[RELEASE TITLE]", "[SINGLE / EP / ALBUM]", "RELEASE ARTWORK",
               "https://simonlibon.github.io/listen.html?preview=1",
               "{{UnsubscribeURL}}", "{{SenderInfo}}")
    for marker in markers:
        if marker not in template:
            raise ValueError(f"Missing email template marker: {marker}")
    base = os.environ.get("SITE_BASE_URL", "https://simonlibon.github.io").rstrip("/")
    if not https_url(base):
        raise ValueError("SITE_BASE_URL must be HTTPS")
    seen = set()
    count = 0
    for item in releases:
        if not isinstance(item, dict) or item.get("published") is not True:
            continue
        slug, title, kind = release_info(item)
        if slug in seen:
            raise ValueError(f"Duplicate release id: {slug}")
        seen.add(slug)
        listen_url = f"{base}/listen.html?id={quote(slug)}"
        cover = html.escape(item["cover"], quote=True)
        artwork = (
            f'<img src="{cover}" alt="Cover artwork for {html.escape(title, quote=True)}" '
            'width="270" height="270" style="display:block;width:270px;'
            'max-width:100%;height:auto;border:0">'
        )
        message = template.replace("[RELEASE TITLE]", html.escape(title))
        message = message.replace("[SINGLE / EP / ALBUM]", kind)
        message = message.replace("RELEASE ARTWORK", artwork)
        message = message.replace(
            "https://simonlibon.github.io/listen.html?preview=1",
            html.escape(listen_url, quote=True),
        )
        message = re.sub(
            r"<!-- EmailOctopus HTML template:.*? -->",
            "<!-- Automatically generated DRAFT; no email has been sent. -->",
            message,
            count=1,
        )
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / f"{slug}.html").write_text(message, encoding="utf-8")
        metadata = {
            "release_id": slug,
            "title": title,
            "type": kind,
            "subject": f"NEW RELEASE — {title} | Simon Libon",
            "preview_text": f"{title} is out now. Listen to the new {kind.lower()}.",
            "listen_url": listen_url,
            "status": "DRAFT — REVIEW AND SEND IN EMAILOCTOPUS",
        }
        (OUTPUT / f"{slug}.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        count += 1
    print(f"Prepared {count} newsletter draft(s). No emails sent.")

if __name__ == "__main__":
    main()
