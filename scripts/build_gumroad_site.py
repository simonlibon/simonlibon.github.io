#!/usr/bin/env python3
"""Build the Gumroad homepage from public release/concert data.

The product catalogue is rendered by Gumroad's injected gumroad-data.
No publishing, product mutation, or sending emails happens here.
"""
import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path
from urllib.parse import quote, urlparse
from zoneinfo import ZoneInfo
if __package__:
    from .mirror_gumroad import mirror_profile
else:
    from mirror_gumroad import mirror_profile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "gumroad-site" / "profile.html"
RELEASE_MARKER = "<!-- SIMON_RELEASES_FEED -->"
CONCERT_MARKER = "<!-- SIMON_CONCERTS_FEED -->"


def valid_https(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def releases_html(releases):
    if not isinstance(releases, list):
        raise ValueError("releases.json: releases must be an array")
    cards = []
    for item in reversed(releases):
        if not isinstance(item, dict) or item.get("published") is not True:
            continue
        slug, title = item.get("id"), item.get("title")
        links = item.get("platforms")
        if not (isinstance(slug, str) and re.fullmatch(r"[a-z0-9-]{1,80}", slug)
                and isinstance(title, str) and title.strip() and isinstance(links, list)
                and any(isinstance(p, dict) and valid_https(p.get("url")) for p in links)):
            continue
        kind = str(item.get("type") or "release").upper()
        if kind not in {"SINGLE", "EP", "ALBUM"}:
            kind = "RELEASE"
        href = "https://simonlibon.github.io/listen.html?id=" + quote(slug)
        cards.append('<article class="feed-row"><span class="eyebrow">' + html.escape(kind) +
                     '</span><strong>' + html.escape(title.strip()) +
                     '</strong><a href="' + html.escape(href, quote=True) +
                     '">LISTEN NOW</a></article>')
        if len(cards) == 3:
            break
    return ('<div class="live-feed" aria-label="Recent releases">' + ''.join(cards) + '</div>') if cards else ''


def concerts_html(concerts, today):
    if not isinstance(concerts, list):
        raise ValueError("concerts-data.json: concerts must be an array")
    accepted = []
    for item in concerts:
        if not isinstance(item, dict):
            continue
        date, city, country = item.get("date"), item.get("city"), item.get("country")
        if not (isinstance(date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
                and isinstance(city, str) and city.strip() and isinstance(country, str)):
            continue
        try:
            concert_date = dt.date.fromisoformat(date)
        except ValueError:
            continue
        if concert_date < today:
            continue
        accepted.append((concert_date, city.strip(), country.strip(), item.get("ticketUrl")))
    accepted.sort(key=lambda x: (x[0], x[1]))
    cards = []
    for date, city, country, ticket_url in accepted[:3]:
        place = html.escape(city + (", " + country if country else ""))
        shown = html.escape(date.strftime("%d %b %Y").upper())
        action = ('<a href="' + html.escape(ticket_url, quote=True) +
                  '" rel="noopener noreferrer">TICKETS</a>') if valid_https(ticket_url) else '<span>DATES</span>'
        cards.append('<article class="feed-row"><span class="eyebrow">' + shown +
                     '</span><strong>' + place + '</strong>' + action + '</article>')
    return ('<div class="live-feed" aria-label="Upcoming concerts">' + ''.join(cards) + '</div>') if cards else ''


def build(source, releases, concerts, today):
    if source.count(RELEASE_MARKER) != 1 or source.count(CONCERT_MARKER) != 1:
        raise ValueError("Gumroad template feed markers missing or duplicated")
    return (source.replace(RELEASE_MARKER, releases_html(releases))
                  .replace(CONCERT_MARKER, concerts_html(concerts, today)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Generated HTML destination")
    args = parser.parse_args()
    releases = json.loads((ROOT / "releases.json").read_text(encoding="utf-8"))["releases"]
    concerts = json.loads((ROOT / "concerts-data.json").read_text(encoding="utf-8"))["concerts"]
    today = dt.datetime.now(ZoneInfo("Europe/Brussels")).date()
    # Homepage: exact canonical HTML and styles; other sections remain on the official site.
    generated = mirror_profile()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(generated, encoding="utf-8")
    print(f"Gumroad homepage generated: {len(generated)} characters; no products or emails changed")


if __name__ == "__main__":
    main()
