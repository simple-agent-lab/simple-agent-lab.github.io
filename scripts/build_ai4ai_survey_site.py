#!/usr/bin/env python3
"""Builds the standalone copy of /ai4ai/ that ai4ai-survey.github.io serves.

The survey page lives in this repository under ai4ai/ and depends on the
lab site's shared assets one directory up. The ai4ai-survey GitHub org
publishes the same page at its own domain from the root of a repository,
so this script assembles a self-contained site: the page at index.html,
every asset it needs under assets/, links back to the lab site made
absolute, and the canonical, Open Graph, citation and JSON-LD URLs pointed
at the new domain. The sync workflow pushes the output to that repository.

The two pages are deliberately not identical. The lab site keeps the
long-form article; the new domain is framed as the paper's project page
(title, description, opening lines, resource links), and each page links
to the other, so search engines see two pages with different jobs rather
than one page mirrored.

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

LAB_TITLE = "AI4AI Survey: From Long-Horizon Agents to Recursive Self-Improvement"
SITE_TITLE = "AI4AI Survey Project Page: Paper, Code, Citation, and Key Findings"
SITE_DESCRIPTION = (
    "Project page of the AI4AI survey (Preprints.org, 2026): the paper, the "
    "RSIHub code, BibTeX, and the survey's main findings on long-horizon "
    "agents, closure, the model and harness routes, and the composition gap."
)
SITE_SOCIAL_DESCRIPTION = (
    "Paper, code, citation, and key findings of the AI4AI survey: how far AI "
    "can reliably carry an improvement loop, and what still bounds recursive "
    "self-improvement."
)

# Each rewrite must match at least once so a page restructure fails the
# build instead of silently shipping a page with broken links.
REWRITES = [
    # Paths and URLs: make the page self-contained on the new domain.
    ('href="../assets/', 'href="./assets/'),
    ('src="../assets/', 'src="./assets/'),
    ('href="../"', 'href="%s"' % LAB_URL),
    ('href="../disclaimer.html"', 'href="%sdisclaimer.html"' % LAB_URL),
    (PAGE_URL + "assets/", SITE_URL + "assets/"),
    (PAGE_URL, SITE_URL),
    # Framing: this domain is the paper's project page, not a mirror.
    ("<title>%s</title>" % LAB_TITLE, "<title>%s</title>" % SITE_TITLE),
    ('property="og:title" content="%s"' % LAB_TITLE,
     'property="og:title" content="%s"' % SITE_TITLE),
    ('name="twitter:title" content="%s"' % LAB_TITLE,
     'name="twitter:title" content="%s"' % SITE_TITLE),
    ('content="The AI4AI survey, published on Preprints.org: how far can AI reliably '
     'carry an improvement loop from idea to verified result? A taxonomy, a closure '
     'audit of 35 systems, and the composition gap."',
     'content="%s"' % SITE_DESCRIPTION),
    ('content="Published on Preprints.org: a survey of how far AI systems can reliably '
     'carry an improvement process from idea to verified result\u2014and what still '
     'limits recursive self-improvement."',
     'content="%s"' % SITE_SOCIAL_DESCRIPTION),
    ('content="AI increasingly performs the work of improvement, but humans still '
     'define its goals and evidence. A survey of AI4AI\'s reliable limits and '
     'composition gap."',
     'content="%s"' % SITE_SOCIAL_DESCRIPTION),
    ('<span class="lang-en" lang="en">Survey · Preprints.org · August 2026</span>',
     '<span class="lang-en" lang="en">Project page · Survey · Preprints.org · August 2026</span>'),
    ('<span class="lang-zh" lang="zh-CN">综述 · Preprints.org · 2026 年 8 月</span>',
     '<span class="lang-zh" lang="zh-CN">项目主页 · 综述 · Preprints.org · 2026 年 8 月</span>'),
    ('<span class="lang-en" lang="en">A survey of AI4AI: definitions, reliable horizons, and open problems.</span>',
     '<span class="lang-en" lang="en">Project page for the AI4AI survey: paper, code, citation, and the main findings.</span>'),
    ('<span class="lang-zh" lang="zh-CN">AI4AI 综述：定义、可靠 horizon 与开放问题。</span>',
     '<span class="lang-zh" lang="zh-CN">AI4AI 综述项目主页：论文、代码、引用与主要结论。</span>'),
    # The lab page links here; here the same slot links back to the article.
    ('<a class="project-page-link" href="%s" target="_blank" rel="noreferrer">\n'
     '            <span class="lang-en" lang="en">Project page</span>\n'
     '            <span class="lang-zh" lang="zh-CN">项目主页</span>' % SITE_URL,
     '<a class="project-page-link" href="%s">\n'
     '            <span class="lang-en" lang="en">Full article on simpleagentlab.com</span>\n'
     '            <span class="lang-zh" lang="zh-CN">完整文章（simpleagentlab.com）</span>' % PAGE_URL),
    # Structured data: name the lab article as another page about the paper.
    ('"sameAs": [\n', '"sameAs": [\n          "%s",\n' % PAGE_URL),
]

# Inserted between the action links and the abstract, so the first thing
# a reader (or a crawler) sees after the byline is what this page is for.
INTRO = """        <p class="opening-note">
          <span class="lang-en" lang="en">This is the project page for the survey: paper, code, citation, and the write-up in one place. The same write-up also runs on the lab site at <a href="%s">simpleagentlab.com/ai4ai</a>, next to the lab's other projects.</span>
          <span class="lang-zh" lang="zh-CN">这里是综述的项目主页，论文、代码、引用方式和正文都在这一页。同一篇正文也发布在实验室网站 <a href="%s">simpleagentlab.com/ai4ai</a>，和实验室的其他工作放在一起。</span>
        </p>

""" % (PAGE_URL, PAGE_URL)
INTRO_ANCHOR = '        <div class="abstract" id="abstract">\n'

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
    if page.count(INTRO_ANCHOR) != 1:
        raise SystemExit("abstract block not found in ai4ai/index.html")
    page = page.replace(INTRO_ANCHOR, INTRO + INTRO_ANCHOR)
    for tag in ('rel="canonical" href="%s"', 'property="og:url" content="%s"'):
        if tag % PAGE_URL in page:
            raise SystemExit("page still claims %s as its own URL" % PAGE_URL)
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
