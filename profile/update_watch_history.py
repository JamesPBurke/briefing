#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/.openclaw/workspace/briefing-repo/profile')
OUT = ROOT / 'watch-history.html'
INDEX = ROOT / 'watch-index.json'
ADDED = ROOT / 'added-shows.json'
MAGGIE = ROOT / 'maggie-watched.json'

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def esc(text: str) -> str:
    return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def section_cards(items):
    parts = []
    for item in items:
        badges = []
        for src in item.get('sources', []):
            badges.append(f'<span class="badge source">{esc(src)}</span>')
        if item.get('liked'):
            badges.append('<span class="badge verdict">loved</span>')
        if any('Maggie' in note or 'maggie' in note.lower() for note in item.get('notes', [])):
            badges.append('<span class="badge maggie">Maggie + James</span>')
        parts.append(f'''
        <article class='show-card'>
          <div class='show-top'>
            <h3>{esc(item.get('title', 'Untitled'))}</h3>
            <div class='badges'>{''.join(badges)}</div>
          </div>
          <div class='meta'>{esc(item.get('mediaType', 'tv'))} · {'; '.join(item.get('notes', []))}</div>
        </article>
        ''')
    return ''.join(parts)


def build_sections(entries):
    buckets = defaultdict(list)
    for item in entries:
        bucket = item.get('mediaType', 'other')
        buckets[bucket].append(item)
    return buckets


def main():
    index = load_json(INDEX, {'items': [], 'counts': {}})
    entries = index.get('items', [])
    buckets = build_sections(entries)
    bucket_html = []
    order = [
        ('tv', 'Television'),
        ('film', 'Films'),
        ('other', 'Other'),
    ]
    for key, label in order:
        items = buckets.get(key, [])
        if not items:
            continue
        bucket_html.append(f'''
        <section class='bucket'>
          <div class='bucket-head'>
            <h2>{label}</h2>
            <span>{len(items)} titles</span>
          </div>
          <div class='grid'>
            {section_cards(items[:200])}
          </div>
        </section>
        ''')
    html = f'''<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>James Burke Watch History</title>
  <link rel="stylesheet" href="../style.css">
  <style>
    .profile-shell {{ max-width: 1260px; margin: 0 auto; padding: 24px; }}
    .profile-hero {{ margin-bottom: 20px; }}
    .profile-actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; }}
    .profile-buckets {{ display:grid; gap:20px; margin-top:20px; }}
    .bucket {{ background: var(--color-surface); border: 1px solid var(--color-divider); border-radius: 24px; padding: 20px; }}
    .bucket-head {{ display:flex; justify-content:space-between; gap:12px; align-items:baseline; margin-bottom:16px; }}
    .bucket-head h2 {{ margin:0; font-size:1.1rem; }}
    .bucket-head span {{ color: var(--color-text-muted); font-size:.9rem; }}
    .grid {{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px; }}
    .show-card {{ border:1px solid var(--color-divider); border-radius:18px; padding:14px; background: var(--color-surface-2); }}
    .show-top {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }}
    .show-card h3 {{ margin:0; font-size:1rem; line-height:1.35; }}
    .badges {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }}
    .badge {{ display:inline-flex; padding:5px 9px; border-radius:999px; border:1px solid var(--color-divider); font-size:.74rem; color: var(--color-text-muted); }}
    .badge.maggie {{ color: #fee2e2; background: rgba(252,165,165,.14); border-color: rgba(252,165,165,.26); }}
    .badge.verdict {{ color: #dbeafe; background: rgba(139,216,255,.12); border-color: rgba(139,216,255,.22); }}
    .badge.source {{ color: #ddd6fe; background: rgba(184,156,255,.12); border-color: rgba(184,156,255,.22); }}
    .meta {{ color: var(--color-text-muted); margin-top: 8px; font-size: .92rem; }}
    @media (max-width: 820px) {{ .grid {{ grid-template-columns: 1fr; }} .show-top {{ flex-direction:column; }} .badges {{ justify-content:flex-start; }} }}
  </style>
</head>
<body>
  <div class='profile-shell'>
    <section class='briefing-lede profile-hero'>
      <div class='lede-inner'>
        <div class='lede-text'>
          <div class='lede-kicker'>Profile · watch history</div>
          <p class='lede-summary'>A redesign-aligned watch history, built from your show exports plus added watches and Maggie overlaps.</p>
          <div class='profile-actions'>
            <a class='btn-ghost' href='../'>Back to briefing</a>
            <a class='btn-ghost' href='horror.html'>Horror memory</a>
          </div>
        </div>
        <div class='lede-stats'>
          <div class='stat-item'><span class='stat-label'>Tracked watched shows</span><span class='stat-value'>{len(entries)}</span></div>
          <div class='stat-item'><span class='stat-label'>Maggie-shared flags</span><span class='stat-value'>{sum(1 for e in entries if any('Maggie' in note or 'maggie' in note.lower() for note in e.get('notes', [])))}</span></div>
          <div class='stat-item'><span class='stat-label'>Updated</span><span class='stat-value updated'>{esc(NOW)}</span></div>
        </div>
      </div>
    </section>
    <div class='profile-buckets'>
      {''.join(bucket_html)}
    </div>
  </div>
</body>
</html>'''
    OUT.write_text(html, encoding='utf-8')
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
