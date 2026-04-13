#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/.openclaw/workspace/briefing-repo/profile')
OUT = ROOT / 'watch-index.json'
SHOWS_PATH = ROOT / 'shows.json'
ADDED_PATH = ROOT / 'added-shows.json'
MAGGIE_PATH = ROOT / 'maggie-watched.json'
HORROR_PATH = ROOT / 'horror-history.json'
LETTERBOXD = ROOT / 'letterboxd'

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def canonical_title(title: str) -> str:
    title = (title or '').strip().lower()
    title = re.sub(r'\s*\(\d{4}\)$', '', title)
    title = re.sub(r'\s+', ' ', title)
    return title


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def add_item(items: dict, title: str, *, media_type: str, source: str, watched: bool = True, liked: bool | None = None, aliases=None, notes: str | None = None):
    if not title:
        return
    key = canonical_title(title)
    entry = items.get(key)
    if entry is None:
        entry = {
            'title': title.strip(),
            'aliases': [],
            'mediaType': media_type,
            'watched': bool(watched),
            'liked': bool(liked) if liked is not None else False,
            'sources': [],
            'notes': [],
        }
        items[key] = entry
    else:
        entry['watched'] = entry.get('watched', False) or bool(watched)
        if liked is not None:
            entry['liked'] = entry.get('liked', False) or bool(liked)
        if media_type == 'tv':
            entry['mediaType'] = 'tv'
    if aliases:
        for alias in aliases:
            a = (alias or '').strip()
            if a and a not in entry['aliases']:
                entry['aliases'].append(a)
    if source not in entry['sources']:
        entry['sources'].append(source)
    if notes:
        entry['notes'].append(notes)


def load_shows(items: dict):
    shows = load_json(SHOWS_PATH, [])
    for show in shows:
        title = (show.get('title') or '').strip()
        watched = 0
        total = 0
        for season in show.get('seasons', []):
            for ep in season.get('episodes', []):
                if ep.get('special'):
                    continue
                total += 1
                watched += 1 if ep.get('is_watched') else 0
        if watched <= 0:
            continue
        add_item(items, title, media_type='tv', source='shows.json', watched=True, notes=f'watched {watched}/{total}')


def load_added(items: dict):
    payload = load_json(ADDED_PATH, {'entries': []})
    for entry in payload.get('entries', []):
        title = (entry.get('title') or '').strip()
        add_item(
            items,
            title,
            media_type='tv',
            source='added-shows.json',
            watched=True,
            liked=entry.get('verdict') == 'loved',
            aliases=entry.get('aliases', []),
            notes=entry.get('notes'),
        )


def load_maggie(items: dict):
    payload = load_json(MAGGIE_PATH, {'watched': []})
    for entry in payload.get('watched', []):
        title = (entry.get('title') or '').strip()
        add_item(items, title, media_type='tv', source='maggie-watched.json', watched=True, aliases=entry.get('aliases', []))


def load_horror(items: dict):
    payload = load_json(HORROR_PATH, {'entries': []})
    for entry in payload.get('entries', []):
        title = (entry.get('title') or '').strip()
        media_type = entry.get('mediaType') or 'tv'
        add_item(
            items,
            title,
            media_type=media_type,
            source='horror-history.json',
            watched=True,
            liked=bool(entry.get('liked')),
            notes=entry.get('notes'),
        )


def load_letterboxd(items: dict):
    for kind, media_type in [
        ('watched.csv', 'film'),
        ('likes/films.csv', 'film'),
        ('diary.csv', 'film'),
        ('ratings.csv', 'film'),
    ]:
        path = LETTERBOXD / kind
        if not path.exists():
            continue
        try:
            with path.open(newline='', encoding='utf-8') as fh:
                for row in csv.DictReader(fh):
                    title = (row.get('Name') or row.get('Title') or row.get('title') or '').strip()
                    if not title:
                        continue
                    add_item(items, title, media_type=media_type, source=f'letterboxd/{kind}', watched=True, liked=(kind.startswith('likes') or kind.startswith('ratings') and row.get('Rating') in {'5', '4.5'}))
        except Exception:
            continue


def main():
    items: dict[str, dict] = {}
    load_shows(items)
    load_added(items)
    load_maggie(items)
    load_horror(items)
    load_letterboxd(items)

    out = {
        'updatedAt': NOW,
        'source': 'normalized union of shows, added-shows, maggie watched, horror history, and letterboxd exports',
        'items': sorted(items.values(), key=lambda e: e['title'].lower()),
        'counts': {
            'items': len(items),
            'tv': sum(1 for e in items.values() if e['mediaType'] == 'tv'),
            'film': sum(1 for e in items.values() if e['mediaType'] == 'film'),
            'liked': sum(1 for e in items.values() if e.get('liked')),
        }
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUT} with {len(items)} items')


if __name__ == '__main__':
    main()
