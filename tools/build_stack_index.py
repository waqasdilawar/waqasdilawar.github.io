#!/usr/bin/env python3
"""Build stack/index.html from stack/stack-index.json.

Usage:  python3 tools/build_stack_index.py

The page is plain static HTML (readable with JavaScript off and by search
engines); a small inline script adds instant search, engine tabs, tag chips
and a real-time-only toggle, with filters mirrored in the URL so a filtered
view can be shared, e.g. /stack/?q=keeper&tag=rbac
"""
import collections, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "stack" / "stack-index.json"
OUT = ROOT / "stack" / "index.html"

engines = json.loads(DATA.read_text(encoding="utf-8"))
esc = html.escape

SHORT = {"ClickHouse": "ClickHouse", "Apache Iceberg": "Iceberg", "Apache Flink": "Flink", "Agentic Data": "Agents"}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def body_html(b):
    """Notes come from Notion with inline <b>/<i>/<code>/<a>; turn bullets into a list."""
    b = re.sub(r"\\([_~*<>|])", r"\1", b)
    # Escape everything except the small set of inline tags Notion emits.
    allowed = re.compile(r'(</?(?:b|i|code)>|<a href="https?://[^"<>]+">|</a>)')
    b = "".join(p if allowed.fullmatch(p) else html.escape(p, quote=False) for p in allowed.split(b))
    b = re.sub(r'<a href="(https?://[^"]+)">', r'<a href="\1" rel="noopener">', b)
    out, bullets = [], []
    for line in b.split("\n"):
        if line.startswith("• "):
            bullets.append(f"<li>{line[2:]}</li>")
            continue
        if bullets:
            out.append("<ul>" + "".join(bullets) + "</ul>")
            bullets = []
        if line.strip():
            out.append(f"<p>{line}</p>")
    if bullets:
        out.append("<ul>" + "".join(bullets) + "</ul>")
    return "".join(out)


def plain(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip().lower()


total = 0
tag_count = collections.Counter()
parts = []
for e in engines:
    ekey = slug(SHORT.get(e["name"], e["name"]))
    n = sum(len(s["entries"]) for s in e["sections"])
    parts.append(f'<section class="engine" data-engine="{ekey}" id="{ekey}">')
    parts.append(f'<h2>{esc(e["name"])} <span class="n">{n}</span></h2>')
    if e.get("blurb"):
        parts.append(f'<p class="blurb">{esc(e["blurb"])}</p>')
    for s in e["sections"]:
        parts.append(f'<section class="group"><h3 id="{ekey}-{slug(s["name"])}">{esc(s["name"])}</h3><ol>')
        for x in s["entries"]:
            total += 1
            tag_count.update(x["tags"])
            search = plain(" ".join([x["title"], x["meta"], x["body"], " ".join(x["tags"])]))
            badges = ""
            if x["rt"]:
                badges += '<span class="badge rt" title="Real-time / streaming">⚡</span>'
            if x["alert"]:
                badges += '<span class="badge alert">Security</span>'
            tags = "".join(f'<button type="button" class="tag" data-tag="{esc(t)}">{esc(t)}</button>' for t in x["tags"])
            parts.append(
                f'<li class="entry" data-engine="{ekey}" data-rt="{int(x["rt"])}" '
                f'data-tags="{esc(" ".join(x["tags"]))}" data-s="{esc(search)}">'
                f'<div class="head">{badges}<a class="title" href="{esc(x["url"])}" rel="noopener">{esc(x["title"])}</a></div>'
                f'<div class="meta">{esc(x["meta"])}</div>'
                f'<div class="note">{body_html(x["body"])}</div>'
                + (f'<div class="tags">{tags}</div>' if tags else "")
                + "</li>"
            )
        parts.append("</ol></section>")
    parts.append("</section>")

top_tags = [t for t, _ in tag_count.most_common()]
engine_tabs = "".join(
    f'<button type="button" class="tab" data-engine="{slug(SHORT.get(e["name"], e["name"]))}" aria-pressed="false">'
    f'{esc(SHORT.get(e["name"], e["name"]))}</button>'
    for e in engines
)
chips = "".join(f'<button type="button" class="tag" data-tag="{esc(t)}" aria-pressed="false">{esc(t)}</button>' for t in top_tags)

page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Stack Index · Muhammad Waqas Dilawar</title>
  <meta name="description" content="A curated reading index on ClickHouse, Apache Iceberg, Apache Flink and data agents: {total} links, each with a short note on what you'll get.">
  <link rel="canonical" href="https://waqasdilawar.github.io/stack/">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <meta name="theme-color" content="#fafafa" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#111111" media="(prefers-color-scheme: dark)">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://waqasdilawar.github.io/stack/">
  <meta property="og:title" content="The Stack Index: ClickHouse · Iceberg · Flink">
  <meta property="og:description" content="{total} curated links on ClickHouse, Apache Iceberg, Apache Flink and data agents, each with a short note.">
  <meta property="og:image" content="https://waqasdilawar.github.io/og.png">
  <meta name="twitter:card" content="summary_large_image">
  <style>
    :root {{ --bg: #fafafa; --fg: #1a1a1a; --muted: #666; --accent: #0b57d0; --line: #e4e4e4; --chip: #efefef; --rt: #b45309; --alert: #b3261e; --mark: #fff3b0; }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --bg: #111; --fg: #eee; --muted: #999; --accent: #8ab4f8; --line: #2a2a2a; --chip: #222; --rt: #f6b24a; --alert: #f28b82; --mark: #5c4d00; }}
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-padding-top: 14rem; }}
    body {{ margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }}
    .wrap {{ max-width: 860px; margin: 0 auto; padding: 0 16px; }}
    header.top {{ padding: 8vh 0 1.25rem; }}
    .back {{ font-size: .9rem; }}
    h1 {{ font-size: 2.25rem; line-height: 1.2; margin: .75rem 0 .5rem; }}
    .lede {{ color: var(--muted); margin: 0; max-width: 640px; }}
    a {{ color: var(--accent); text-decoration: none; text-underline-offset: 4px; }}
    a:hover, a:focus-visible {{ text-decoration: underline; }}
    :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }}
    .bar {{ position: sticky; top: 0; z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line); padding: .75rem 0 .6rem; }}
    .search {{ display: flex; gap: .5rem; align-items: center; }}
    .search input {{ flex: 1; min-width: 0; font: inherit; color: var(--fg); background: transparent; border: 1px solid var(--line); border-radius: 8px; padding: .55rem .75rem; }}
    .search input:focus {{ outline: 2px solid var(--accent); outline-offset: -1px; }}
    .row {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .6rem; align-items: center; }}
    button {{ font: inherit; cursor: pointer; }}
    .tab, .toggle {{ font-size: .85rem; border: 1px solid var(--line); background: transparent; color: var(--fg); border-radius: 999px; padding: .2rem .75rem; }}
    .tab[aria-pressed="true"], .toggle[aria-pressed="true"] {{ background: var(--fg); color: var(--bg); border-color: var(--fg); }}
    .tag {{ font: .75rem/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; border: 0; background: var(--chip); color: var(--muted); border-radius: 4px; padding: .15rem .45rem; }}
    .tag:hover {{ color: var(--fg); }}
    .tag[aria-pressed="true"] {{ background: var(--accent); color: var(--bg); }}
    .chips {{ max-height: 3.1rem; overflow: hidden; }}
    .chips.open {{ max-height: none; }}
    .status {{ font-size: .85rem; color: var(--muted); margin-left: auto; }}
    .linkish {{ background: none; border: 0; color: var(--accent); font-size: .85rem; padding: 0; }}
    .engine > h2 {{ font-size: 1.5rem; margin: 2.5rem 0 .25rem; }}
    .n {{ font-size: .9rem; font-weight: 400; color: var(--muted); }}
    .blurb {{ color: var(--muted); margin: 0 0 .5rem; }}
    h3 {{ font-size: .8rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 2rem 0 .5rem; }}
    ol {{ list-style: none; margin: 0; padding: 0; }}
    .entry {{ padding: .9rem 0; border-top: 1px solid var(--line); }}
    .head {{ display: flex; gap: .4rem; align-items: baseline; }}
    .title {{ font-weight: 600; font-size: 1.02rem; }}
    .badge {{ flex: none; font-size: .7rem; font-weight: 600; letter-spacing: .03em; }}
    .badge.rt {{ color: var(--rt); }}
    .badge.alert {{ color: var(--alert); border: 1px solid currentColor; border-radius: 4px; padding: 0 .3rem; text-transform: uppercase; }}
    .meta {{ font-size: .85rem; color: var(--muted); margin: .1rem 0 .35rem; }}
    .note p {{ margin: 0 0 .4rem; }}
    .note ul {{ margin: 0 0 .4rem; padding-left: 1.2rem; }}
    .note code, .tag {{ overflow-wrap: anywhere; }}
    .note code {{ font: .85em ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--chip); padding: .05rem .3rem; border-radius: 3px; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .4rem; }}
    mark {{ background: var(--mark); color: inherit; border-radius: 2px; }}
    .empty {{ display: none; color: var(--muted); padding: 3rem 0; text-align: center; }}
    [hidden] {{ display: none !important; }}
    footer {{ margin: 3rem 0; font-size: .85rem; color: var(--muted); }}
    .nojs .bar {{ display: none; }}
    @media (max-width: 560px) {{ h1 {{ font-size: 1.8rem; }} .status {{ width: 100%; margin-left: 0; }} .bar {{ position: static; }} html {{ scroll-padding-top: 0; }} }}
  </style>
</head>
<body class="nojs">
  <div class="wrap">
    <header class="top">
      <a class="back" href="../">← Muhammad Waqas Dilawar</a>
      <h1>The Stack Index</h1>
      <p class="lede">A curated reading index on ClickHouse, Apache Iceberg, Apache Flink and data agents: {total} links, each with a short note on what you'll get. Entries marked <span class="badge rt">⚡</span> are about real-time and streaming.</p>
    </header>
  </div>
  <div class="bar">
    <div class="wrap">
      <div class="search">
        <input id="q" type="search" placeholder="Search titles, notes, authors, tags…  ( / )" aria-label="Search the index" autocomplete="off" spellcheck="false">
      </div>
      <div class="row" role="group" aria-label="Filter by engine">
        <button type="button" class="tab" data-engine="" aria-pressed="true">All</button>{engine_tabs}
        <button type="button" class="toggle" id="rt" aria-pressed="false" title="Show only real-time / streaming entries">⚡ Real-time</button>
        <span class="status" id="status" aria-live="polite"></span>
      </div>
      <div class="row chips" id="chips" aria-label="Filter by tag">{chips}</div>
      <div class="row"><button type="button" class="linkish" id="more">More tags</button><button type="button" class="linkish" id="clear" hidden>Clear filters</button></div>
    </div>
  </div>
  <main class="wrap" id="list">
    {"".join(parts)}
    <p class="empty" id="empty">Nothing matches. Try a broader term or clear the filters.</p>
  </main>
  <div class="wrap"><footer>Curated by <a href="../">Muhammad Waqas Dilawar</a>. Notes are personal summaries; follow the links for the full pieces.</footer></div>
  <script>
  (() => {{
    document.body.classList.remove('nojs');
    const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
    const q = $('#q'), rtBtn = $('#rt'), status = $('#status'), empty = $('#empty'), clear = $('#clear');
    const entries = $$('.entry').map(el => ({{
      el, s: el.dataset.s, tags: el.dataset.tags.split(' ').filter(Boolean), engine: el.dataset.engine, rt: el.dataset.rt === '1',
      note: el.querySelector('.note'), title: el.querySelector('.title'),
    }}));
    entries.forEach(e => {{ e.noteHTML = e.note.innerHTML; e.titleText = e.title.textContent; }});
    const groups = $$('.group'), engines = $$('.engine');
    const state = {{ q: '', engine: '', tags: new Set(), rt: false }};

    function readURL() {{
      const p = new URLSearchParams(location.search);
      state.q = p.get('q') || ''; state.engine = p.get('engine') || ''; state.rt = p.get('rt') === '1';
      state.tags = new Set((p.get('tag') || '').split(',').filter(Boolean));
      q.value = state.q;
    }}
    function writeURL() {{
      const p = new URLSearchParams();
      if (state.q) p.set('q', state.q);
      if (state.engine) p.set('engine', state.engine);
      if (state.tags.size) p.set('tag', [...state.tags].join(','));
      if (state.rt) p.set('rt', '1');
      const s = p.toString();
      history.replaceState(null, '', s ? '?' + s : location.pathname);
    }}
    const escRe = s => s.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
    function highlight(root, re) {{
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      const nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
      for (const n of nodes) {{
        if (!re.test(n.nodeValue)) continue; re.lastIndex = 0;
        const frag = document.createDocumentFragment(); let last = 0;
        n.nodeValue.replace(re, (m, i) => {{
          frag.append(n.nodeValue.slice(last, i));
          const mk = document.createElement('mark'); mk.textContent = m; frag.append(mk);
          last = i + m.length;
        }});
        frag.append(n.nodeValue.slice(last)); n.replaceWith(frag);
      }}
    }}
    function render() {{
      const terms = state.q.toLowerCase().split(/\\s+/).filter(Boolean);
      const re = terms.length ? new RegExp('(' + terms.map(escRe).join('|') + ')', 'gi') : null;
      let shown = 0;
      for (const e of entries) {{
        const ok = (!state.engine || e.engine === state.engine) && (!state.rt || e.rt)
          && [...state.tags].every(t => e.tags.includes(t)) && terms.every(t => e.s.includes(t));
        e.el.hidden = !ok;
        if (ok) {{
          shown++;
          e.note.innerHTML = e.noteHTML; e.title.textContent = e.titleText;
          if (re) {{ highlight(e.note, re); highlight(e.title, re); }}
        }}
      }}
      groups.forEach(g => g.hidden = !g.querySelector('.entry:not([hidden])'));
      engines.forEach(g => g.hidden = !g.querySelector('.entry:not([hidden])'));
      $$('.tab').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.engine === state.engine)));
      rtBtn.setAttribute('aria-pressed', String(state.rt));
      $$('.tag').forEach(b => b.setAttribute('aria-pressed', String(state.tags.has(b.dataset.tag))));
      const filtered = state.q || state.engine || state.tags.size || state.rt;
      status.textContent = filtered ? `${{shown}} of ${{entries.length}} entries` : `${{entries.length}} entries`;
      empty.style.display = shown ? 'none' : 'block';
      clear.hidden = !filtered;
    }}
    let t;
    q.addEventListener('input', () => {{ clearTimeout(t); t = setTimeout(() => {{ state.q = q.value.trim(); writeURL(); render(); }}, 80); }});
    document.addEventListener('click', ev => {{
      const tab = ev.target.closest('.tab'), tag = ev.target.closest('.tag');
      if (tab) state.engine = tab.dataset.engine;
      else if (tag) {{
        const v = tag.dataset.tag; state.tags.has(v) ? state.tags.delete(v) : state.tags.add(v);
        if (tag.closest('.entry')) window.scrollTo({{ top: 0 }});
      }}
      else if (ev.target === rtBtn) state.rt = !state.rt;
      else if (ev.target === clear) {{ state.q = ''; q.value = ''; state.engine = ''; state.tags.clear(); state.rt = false; }}
      else return;
      writeURL(); render();
    }});
    $('#more').addEventListener('click', ev => {{
      const c = $('#chips'); c.classList.toggle('open');
      ev.target.textContent = c.classList.contains('open') ? 'Fewer tags' : 'More tags';
    }});
    document.addEventListener('keydown', ev => {{
      if (ev.key === '/' && document.activeElement !== q) {{ ev.preventDefault(); q.focus(); }}
      else if (ev.key === 'Escape' && document.activeElement === q) {{ q.value = ''; state.q = ''; writeURL(); render(); }}
    }});
    readURL(); render();
  }})();
  </script>
</body>
</html>
"""
OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)}: {total} entries, {len(page)//1024} KB")
