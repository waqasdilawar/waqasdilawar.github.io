#!/usr/bin/env python3
"""Convert a Notion reading-index page (as fetched in Notion-flavoured Markdown) to JSON.

Usage:
    python3 tools/notion_index_to_json.py notion-export/page.md stack/stack-index.json

Expected page shape (what the Stack Index uses):
    ## Engine name  ·  N entries
    <i>one-line blurb</i>
    ### Section name  (N)
    <i>section note</i>                       -> dropped (private curation log)
    <b>Sub-heading</b>                        -> dropped (grouping only)
    - ⚡ [<b>Title</b>](url) — <i>Source · Author, Date, kind</i>. Note text.  <code>tag</code> <code>tag</code>
      - nested bullet                         -> kept as a bullet in the note
    Anything before the first "## " (page preamble, provenance, refresh log) is dropped.

Output is RAW text: always run tools/privacy_check.py on it and edit the notes
by hand before publishing.
"""
import json, re, sys

LINK = re.compile(r"\[(.*?)\]\((https?://[^)\s]+)\)")
TAG = re.compile(r"<code>([a-z0-9-]+)</code>\s*$")
ENTRY = re.compile(
    r"^- (⚡ )?(<b><span[^>]*>⚠️ ACTION</span></b> )?\[(.*?)\]\((https?://[^)\s]+)\)(.*)$")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def convert(text):
    # Notion sometimes splits a bold title into two links: [<b>A </b>](u1)[<b>B</b>](u2)
    text = re.sub(r"</b>\]\((https?://[^)]+)\)\[<b>([^<]*)</b>\]\(http[^)]*\)", r"\2</b>](\1)", text)
    engines, eng, sec, entry = [], None, None, None

    def close():
        nonlocal entry
        if entry is None:
            return
        body = entry.pop("_raw").strip()
        tags = []
        while (m := TAG.search(body)):
            tags.insert(0, m.group(1))
            body = body[: m.start()].rstrip()
        entry["tags"] = tags
        entry["body"] = LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', body)
        sec["entries"].append(entry)
        entry = None

    started = False
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("<content>"):
            started = True
            continue
        if s.startswith("</content>") or s.startswith("</page>"):
            break
        if ln.startswith("## "):
            started = True
            close()
            eng = {"name": re.sub(r"\s+·\s+\d+ entries\s*$", "", ln[3:]).strip(), "blurb": "", "sections": []}
            engines.append(eng)
            sec = None
            continue
        if not started or eng is None:
            continue
        if ln.startswith("### "):
            close()
            name = re.sub(r"\s+\(\d+\)\s*$", "", ln[4:]).strip()
            sec = {"name": re.sub(r"^\d\d — ", "", name), "entries": []}
            eng["sections"].append(sec)
            continue
        m = ENTRY.match(ln)
        if m and sec is not None:
            close()
            meta, note = "", m.group(5)
            mm = re.match(r"^\s*—\s*(.+?</i>)\.\s+(.*)$", m.group(5))
            if mm:
                meta, note = mm.group(1), mm.group(2)
            entry = {
                "title": strip_tags(m.group(3)).strip(), "url": m.group(4),
                "rt": bool(m.group(1)), "alert": bool(m.group(2)),
                "meta": strip_tags(LINK.sub(lambda x: x.group(1), meta)).strip(), "_raw": note,
            }
            continue
        if re.fullmatch(r"<b>[^<]*</b>", s):
            close()
            continue
        if entry is not None and s:
            if s in ("<p>", "</p>"):
                continue
            entry["_raw"] += ("\n• " + s[2:]) if s.startswith("- ") else ("\n" + s)
            continue
        if s.startswith("<i>") and sec is None and entry is None:
            eng["blurb"] = strip_tags(s).strip()
    close()
    return engines


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    data = convert(open(src, encoding="utf-8").read())
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for e in data:
        print(f'{e["name"]}: {sum(len(s["entries"]) for s in e["sections"])} entries')
    print("Next: python3 tools/privacy_check.py", out)
