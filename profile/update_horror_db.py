#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/.openclaw/workspace/briefing-repo/profile')
OUT = ROOT / 'horror.html'
HISTORY = ROOT / 'horror-history.json'
RECS = ROOT / 'horror-recommendations.json'

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def esc(text: str) -> str:
    return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def build_recommendations():
    data = load_json(RECS, {'items': []})
    items = data.get('items', []) if isinstance(data, dict) else []
    buckets = defaultdict(list)
    for item in items:
        buckets[item.get('bucket', 'suggestions')].append(item)
    return buckets


def card(item: dict) -> str:
    title = esc(item.get('title', 'Untitled'))
    notes = esc(item.get('notes', ''))
    tags = item.get('tags', []) or []
    chips = ''.join(f'<span class="tag">{esc(tag)}</span>' for tag in tags)
    return f'''
    <article class="show-card">
      <div class="show-top">
        <h3>{title}</h3>
        <div class="badges">{chips}</div>
      </div>
      <div class="notes">{notes}</div>
    </article>
    '''.strip()


def section(title: str, items: list[dict], count_label: str) -> str:
    if not items:
        return ''
    return f'''
    <section class="bucket">
      <div class="bucket-head">
        <h2>{esc(title)}</h2>
        <span>{esc(count_label)}</span>
      </div>
      <div class="grid">
        {''.join(card(item) for item in items)}
      </div>
    </section>
    '''


def build_html(history: dict) -> str:
    liked = [item for item in history.get('entries', []) if item.get('liked')]
    not_liked = [item for item in history.get('entries', []) if not item.get('liked')]
    sections = []
    if liked:
        sections.append(section('Seen and liked', liked[:24], f'{len(liked)} titles'))
    if not_liked:
        sections.append(section('Seen but not liked', not_liked[:24], f'{len(not_liked)} titles'))
    recs = build_recommendations()
    rec_html = ''
    for bucket, items in recs.items():
        if not items:
            continue
        rec_html += f'''
        <section class="bucket">
          <div class="bucket-head">
            <h2>{esc(bucket.title())}</h2>
            <span>{len(items)} picks</span>
          </div>
          <div class="grid">
            {''.join(card({'title': item.get('title'), 'notes': item.get('why', ''), 'tags': ['recommendation']}) for item in items[:12])}
          </div>
        </section>
        '''
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Horror Memory · James Daily Briefing</title>
  <link rel="stylesheet" href="../style.css">
  <style>
    .profile-shell {{ max-width: 1260px; margin: 0 auto; padding: 24px; }}
    .profile-hero {{ margin-bottom: 20px; }}
    .profile-hero .lede-summary {{ margin-top: 8px; }}
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
    .tag {{ display:inline-flex; padding:5px 9px; border-radius:999px; border:1px solid var(--color-divider); font-size:.74rem; color: var(--color-text-muted); }}
    .notes {{ margin-top:10px; color: var(--color-text); }}
    @media (max-width: 820px) {{ .grid {{ grid-template-columns: 1fr; }} .show-top {{ flex-direction:column; }} .badges {{ justify-content:flex-start; }} }}
  </style>
</head>
<body>
  <div class="profile-shell">
    <section class="briefing-lede profile-hero">
      <div class="lede-inner">
        <div class="lede-text">
          <div class="lede-kicker">Profile · horror memory</div>
          <p class="lede-summary">A redesign-aligned view of the horror works you’ve seen and liked, plus a small recommendation deck.</p>
          <div class="profile-actions">
            <a class="btn-ghost" href="../">Back to briefing</a>
            <a class="btn-ghost" href="watch-history.html">Watch history</a>
          </div>
        </div>
        <div class="lede-stats">
          <div class="stat-item"><span class="stat-label">Liked</span><span class="stat-value">{len(liked)}</span></div>
          <div class="stat-item"><span class="stat-label">Not liked</span><span class="stat-value">{len(not_liked)}</span></div>
          <div class="stat-item"><span class="stat-label">Updated</span><span class="stat-value updated">{esc(NOW)}</span></div>
        </div>
      </div>
    </section>
    <div class="profile-buckets">
      {''.join(sections)}
      {rec_html}
    </div>
  </div>
</body>
</html>'''


def main():
    history = load_json(HISTORY, {'entries': []})
    html = build_html(history)
    OUT.write_text(html, encoding='utf-8')
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
