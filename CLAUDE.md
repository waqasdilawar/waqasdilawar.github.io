# waqasdilawar.github.io

Public personal site on GitHub Pages: plain static HTML, no Jekyll (`.nojekyll`), served from `main`.

## Git rules

- Author and commit as `Waqas Dilawar <20771676+waqasdilawar@users.noreply.github.com>`:
  `git -c user.name="Waqas Dilawar" -c user.email="20771676+waqasdilawar@users.noreply.github.com" commit ...`
- No Claude attribution anywhere: no `Co-Authored-By: Claude`, no `Claude-Session:` lines in
  commits, and no "Generated with Claude Code" footer or session link in PR descriptions.
- Work on a branch and open a PR into `main`; merging the PR is what publishes the site.

## Moving a Notion page here

1. Fetch the page from Notion and save the Markdown to `notion-export/<name>.md` (git-ignored).
2. Convert: `python3 tools/notion_index_to_json.py notion-export/<name>.md <dir>/<name>.json`
   (built for reading-index pages; other page shapes need their own converter).
3. Privacy pass, every time, before anything is committed:
   `python3 tools/privacy_check.py <dir>/<name>.json`
   - Rewrite notes about the employer's systems in neutral terms ("our cluster" → "a self-hosted
     cluster"); drop internal tool names, data-centre locations, business details, private drafts,
     and Notion curation logs (provenance, refresh logs, "checked on" notes).
   - Private terms to search for live in `tools/private-terms.local.txt` (git-ignored). Never commit
     that list or any script that contains original private wording.
4. Build: `python3 tools/build_stack_index.py` (or a sibling builder for a new page), check it in a
   browser at desktop and phone width, then link it from `index.html`.
