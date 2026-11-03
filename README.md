# waqasdilawar.github.io

Personal site, published to https://waqasdilawar.github.io by GitHub Pages.

## Stack Index (`/stack/`)

`stack/index.html` is generated from `stack/stack-index.json`. The page is plain static HTML; a small
inline script adds search, engine tabs, tag filters and a real-time toggle, with the filters kept in
the URL (e.g. `/stack/?q=keeper&tag=rbac`).

## Publishing Notion pages here

| Script | What it does |
|---|---|
| `tools/notion_index_to_json.py` | Notion reading-index Markdown → JSON (drops the page preamble and curation notes) |
| `tools/privacy_check.py` | Flags first-person / internal wording and private terms before anything is published |
| `tools/build_stack_index.py` | JSON → `stack/index.html` |

```sh
python3 tools/notion_index_to_json.py notion-export/stack-index.md stack/stack-index.json
python3 tools/privacy_check.py stack/stack-index.json   # then edit the notes by hand
python3 tools/build_stack_index.py
```

Private terms for the check go in `tools/private-terms.local.txt`, one per line. It is git-ignored on
purpose: the list itself is private. See `CLAUDE.md` for the full workflow and commit rules.
