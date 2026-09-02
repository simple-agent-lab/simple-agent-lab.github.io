#!/usr/bin/env python3
"""Builds the standalone copy of /ai4ai/ that ai4ai-survey.github.io serves.

The survey page lives in this repository under ai4ai/ and depends on the
lab site's shared assets one directory up. The ai4ai-survey GitHub org
publishes the same page at its own domain from the root of a repository,
so this script assembles a self-contained site: the page at index.html,
every asset it needs under assets/, links back to the lab site made
absolute, and the canonical, Open Graph, citation and JSON-LD URLs pointed
at the new domain. The sync workflow pushes the output to that repository.

Usage: build_ai4ai_survey_site.py OUTPUT_DIR
"""

from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
LAB_URL = "https://simpleagentlab.com/"
PAGE_URL = LAB_URL + "ai4ai/"
SITE_URL = "https://ai4ai-survey.github.io/"
SHARED_ASSETS = ["styles.css", "site.js", "logo.svg", "logo.png", "favicon.svg"]

# Each rewrite must match at least once so a page restructure fails the
# build instead of silently shipping a page with broken links.
REWRITES = [
    ('href="../assets/', 'href="./assets/'),
    ('src="../assets/', 'src="./assets/'),
    ('href="../"', 'href="%s"' % LAB_URL),
    ('href="../disclaimer.html"', 'href="%sdisclaimer.html"' % LAB_URL),
    (PAGE_URL + "assets/", SITE_URL + "assets/"),
    (PAGE_URL, SITE_URL),
]

ROBOTS = """User-agent: *
Allow: /

Sitemap: {site}sitemap.xml
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{site}</loc>
    <lastmod>{lastmod}</lastmod>
    <priority>1.0</priority>
  </url>
</urlset>
"""

README = """# AI4AI Survey

Project page for *AI4AI Survey: From Long-Horizon Agents to Recursive
Self-Improvement*, served at {site} by GitHub Pages from the root of this
repository.

This repository is generated. The page is maintained in
https://github.com/simple-agent-lab/simple-agent-lab.github.io under
`ai4ai/` and synced here by `scripts/build_ai4ai_survey_site.py`; edit it
there, not here. Preprint: https://doi.org/10.20944/preprints202608.2108.v1
"""


def build_page(source):
    page = source
    for old, new in REWRITES:
        if old not in page:
            raise SystemExit("rewrite target not found in ai4ai/index.html: %r" % old)
        page = page.replace(old, new)
    leftovers = re.findall(r'(?:href|src)="\.\./[^"]*"', page)
    if leftovers:
        raise SystemExit("parent-relative paths left in page: %s" % leftovers)
    if PAGE_URL in page:
        raise SystemExit("page still names %s" % PAGE_URL)
    return page


def last_modified(page):
    match = re.search(r'property="article:modified_time" content="([^"]+)"', page)
    if not match:
        raise SystemExit("article:modified_time missing from ai4ai/index.html")
    return match.group(1)


def build(output):
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    assets = output / "assets"
    assets.mkdir(parents=True)

    source = (ROOT / "ai4ai/index.html").read_text(encoding="utf-8")
    page = build_page(source)
    (output / "index.html").write_text(page, encoding="utf-8")

    for path in sorted((ROOT / "ai4ai/assets").iterdir()):
        shutil.copy2(path, assets / path.name)
    for name in SHARED_ASSETS:
        shutil.copy2(ROOT / "assets" / name, assets / name)

    (output / "robots.txt").write_text(ROBOTS.format(site=SITE_URL), encoding="utf-8")
    (output / "sitemap.xml").write_text(
        SITEMAP.format(site=SITE_URL, lastmod=last_modified(source)), encoding="utf-8"
    )
    (output / "README.md").write_text(README.format(site=SITE_URL), encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    return output


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    built = build(sys.argv[1])
    print("built %s (%d files)" % (built, sum(1 for p in built.rglob("*") if p.is_file())))
