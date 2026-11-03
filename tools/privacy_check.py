#!/usr/bin/env python3
"""Flag text that should not go on the public site before publishing a page.

Usage:
    python3 tools/privacy_check.py stack/stack-index.json [more.json|.html ...]

Checks every string in the file for:
  * first-person / team wording ("our cluster", "we", "us", "my team") that
    usually means a note is about an employer's systems, and
  * private terms listed one per line in tools/private-terms.local.txt
    (git-ignored, never commit it: the list itself is private), or in the file
    named by $PRIVATE_TERMS_FILE. Lines starting with # are comments.

Exits 1 when anything is found. Some hits are fine (a quoted sentence or a
product name from the source article); judge each one, then edit the JSON.
"""
import json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
GENERIC = [r"\bour\b", r"\bours\b", r"\bwe\b", r"\bus\b", r"\bmy team\b", r"\bin-house\b",
           r"\binternal(ly)?\b", r"\bprivate\b", r"\bconfidential\b", r"\bTODO\b", r"\bstill to add\b"]

# Article titles, links and bylines come from the source, so "How we built…" there is fine.
SOURCE_FIELDS = {"title", "url", "meta"}


def load_terms():
    path = pathlib.Path(os.environ.get("PRIVATE_TERMS_FILE", HERE / "private-terms.local.txt"))
    if not path.exists():
        print(f"note: {path} not found, checking generic wording only", file=sys.stderr)
        return []
    return [re.escape(t.strip()) for t in path.read_text(encoding="utf-8").splitlines()
            if t.strip() and not t.startswith("#")]


def strings(node, where=""):
    if isinstance(node, dict):
        label = node.get("title") or node.get("name") or where
        for k, v in node.items():
            if k in SOURCE_FIELDS:
                continue  # written by the article's author, not by us
            yield from strings(v, label)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v, where)
    elif isinstance(node, str):
        yield where, node


def main(paths):
    private = load_terms()
    pats = [(re.compile(p, re.I), "wording") for p in GENERIC]
    pats += [(re.compile(rf"\b{p}\b", re.I), "PRIVATE") for p in private]
    hits = 0
    for p in paths:
        raw = pathlib.Path(p).read_text(encoding="utf-8")
        items = strings(json.loads(raw)) if p.endswith(".json") else [("", raw)]
        for where, text in items:
            for rx, kind in pats:
                for m in rx.finditer(text):
                    hits += 1
                    ctx = text[max(0, m.start() - 60): m.end() + 40].replace("\n", " ")
                    print(f"[{kind}] {p} :: {where[:50]} :: …{ctx}…")
    print(f"{hits} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["stack/stack-index.json"]))
