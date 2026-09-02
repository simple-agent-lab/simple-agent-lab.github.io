#!/usr/bin/env python3
"""Builds the short English page that ai4ai-survey.github.io serves.

The AI4AI survey article lives in this repository under ai4ai/ and is the
long, bilingual read on the lab site. The ai4ai-survey GitHub org publishes
a second page from the same source at its own domain: a short, English-only
"what is AI4AI" read. It opens with its own definition of the field, then
keeps one takeaway per section, the figures, the closure table and the
conclusion, and links to the full article for everything else. Two pages,
two sets of search queries, one source. The sync workflow pushes the output
to that repository.

Every extraction below must find exactly what it looks for; if the article
is restructured, the build fails instead of shipping a broken page.

Usage: build_ai4ai_survey_site.py OUTPUT_DIR
"""

from pathlib import Path
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
LAB_URL = "https://simpleagentlab.com/"
PAGE_URL = LAB_URL + "ai4ai/"
SITE_URL = "https://ai4ai-survey.github.io/"
PAPER_DOI_URL = "https://doi.org/10.20944/preprints202608.2108.v1"
SHARED_ASSETS = ["styles.css", "site.js", "logo.svg", "logo.png", "favicon.svg"]

LAB_TITLE = "AI4AI Survey: From Long-Horizon Agents to Recursive Self-Improvement"
SITE_TITLE = "What Is AI4AI? Key Findings of the AI4AI Survey"
SITE_HEADING = "What is AI4AI? Key findings of the AI4AI survey"
SITE_DESCRIPTION = (
    "AI4AI explained in a short read: what AI-for-AI research is, what "
    "frontier agents already do, why the harness matters as much as the "
    "model, and the composition gap. Key findings of the AI4AI survey by "
    "Simple Agent Lab."
)
SITE_KEYWORDS = (
    "what is AI4AI, AI4AI, AI for AI, AI4AI research, AI4AI explained, "
    "AI4AI survey, AI4AI key findings, recursive self-improvement, RSI, "
    "long-horizon agents, agent harness, composition gap"
)
SITE_PUBLISHED = "2026-09-02"

EYEBROW = "Blog · AI4AI explained · September 2026"
TAGLINE = (
    "A short English read-through of the AI4AI survey: what the field is, "
    "what already works, and what is still missing."
)
INTRO = (
    "This is the short version of Simple Agent Lab's AI4AI research write-up: "
    "a definition of the field, one takeaway per section, the figures and the "
    "closure table. The full article, in English and Chinese, is at "
    '<a href="%s">simpleagentlab.com/ai4ai</a>.' % PAGE_URL
)
DEFINITION = [
    "AI4AI, AI for AI, means using AI systems to improve AI systems. An agent "
    "proposes a change to a model, a training pipeline, a harness or a benchmark, "
    "runs the experiment, reads the result, and repairs what failed. The survey "
    "treats this as a long-horizon loop with five stages, goal, plan, execute, "
    "feedback and repair, and asks one question of every system: how far can it "
    "carry that loop from an idea to a verified result on its own?",
    "Recursive self-improvement, RSI, is the special case where the system being "
    "improved is the one doing the improving. Most of what is called self-improvement "
    "today is not that: a fixed harness, an outer search over scaffolds, or an agent "
    "editing its own code under an evaluator that humans wrote. The survey audits 35 "
    "systems against the five stages to say which paradigm each one belongs to.",
]
FULL_ARTICLE_NOTE = (
    "That is the short version. The full article walks through each section, "
    "with the paper's abstract, the recursion ladder, the model and harness routes, "
    "the three places the composition gap shows up, the BibTeX entry, and a Chinese "
    'translation: <a href="%s">read it on simpleagentlab.com</a>.' % PAGE_URL
)
CITE_NOTE = (
    'The survey is published on Preprints.org as <a href="%s" target="_blank" '
    'rel="noreferrer">doi:10.20944/preprints202608.2108.v1</a>. The BibTeX entry '
    'is on the <a href="%s#cite">full article page</a>.' % (PAPER_DOI_URL, PAGE_URL)
)

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

README = """# What is AI4AI?

Short English read of the AI4AI survey, served at {site} by GitHub Pages
from the root of this repository.

This repository is generated. The article is maintained in
https://github.com/simple-agent-lab/simple-agent-lab.github.io under
`ai4ai/` and this short version is built from it by
`scripts/build_ai4ai_survey_site.py`; edit it there, not here.
Full article: {page}  Preprint: {doi}
"""


def fail(message):
    raise SystemExit("build_ai4ai_survey_site: " + message)


def grab(pattern, text, what):
    """Returns the single match of pattern in text, or fails the build."""
    found = re.findall(pattern, text, flags=re.S)
    if len(found) != 1:
        fail("expected exactly one %s, found %d" % (what, len(found)))
    return found[0]


def section(source, section_id):
    """Returns the article between one h2 and the next."""
    pattern = r'(<h2 id="%s">.*?)(?=\n        <h2 id=")' % re.escape(section_id)
    return grab(pattern, source, "section #" + section_id)


def english_only(html):
    """Drops the Chinese spans and unwraps the English ones."""
    html = re.sub(r'\s*<span class="lang-zh" lang="zh-CN">.*?</span>', "", html, flags=re.S)
    html = re.sub(r'<span class="lang-en" lang="en">(.*?)</span>', r"\1", html, flags=re.S)
    if "lang-zh" in html or "lang-en" in html:
        fail("bilingual markup survived the English-only pass")
    return html


def build_head(source, lastmod):
    head = grab(r"^(.*?</head>)", source, "head")
    swaps = [
        ("<title>%s</title>" % LAB_TITLE, "<title>%s</title>" % SITE_TITLE),
        ('property="og:title" content="%s"' % LAB_TITLE,
         'property="og:title" content="%s"' % SITE_TITLE),
        ('name="twitter:title" content="%s"' % LAB_TITLE,
         'name="twitter:title" content="%s"' % SITE_TITLE),
        ('<meta property="article:section" content="Survey" />',
         '<meta property="article:section" content="Blog" />'),
        ('<meta property="og:locale:alternate" content="zh_CN" />\n', ""),
        ('"name": "AI4AI Survey",\n            "item": "%s"' % SITE_URL,
         '"name": "What is AI4AI",\n            "item": "%s"' % SITE_URL),
        # The inline bootstrap picks the language from the browser; this
        # page has no Chinese text, so pin it to English.
        ('var language = savedLanguage === "en" || savedLanguage === "zh"\n'
         "          ? savedLanguage\n"
         "          : browserLanguage;", 'var language = "en";'),
    ]
    for old, new in swaps:
        if old not in head:
            fail("head rewrite target not found: %r" % old[:60])
        head = head.replace(old, new)

    # description / keywords / social descriptions carry the lab wording.
    head = re.sub(r'(name="description"\s+content=")[^"]*(")',
                  r"\g<1>%s\2" % SITE_DESCRIPTION, head, count=1)
    head = re.sub(r'(name="keywords"\s+content=")[^"]*(")',
                  r"\g<1>%s\2" % SITE_KEYWORDS, head, count=1)
    head = re.sub(r'(property="og:description"\s+content=")[^"]*(")',
                  r"\g<1>%s\2" % SITE_DESCRIPTION, head, count=1)
    head = re.sub(r'(name="twitter:description"\s+content=")[^"]*(")',
                  r"\g<1>%s\2" % SITE_DESCRIPTION, head, count=1)

    # The scholarly record stays on the lab page: drop the Scholar tags and
    # their comment, and describe this page as an article about the paper.
    head = re.sub(r"\n    <!-- The paper's scholarly record.*?-->\n", "\n", head, count=1, flags=re.S)
    head, dropped = re.subn(r'    <meta name="citation_[^\n]*\n', "", head)
    if dropped < 20:
        fail("expected to drop the citation_* tags, dropped %d" % dropped)
    scholarly = grab(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "ScholarlyArticle".*?</script>',
                     head, "ScholarlyArticle JSON-LD block")
    paper_title = grab(r'"name": "(AI4AI Survey: From Long-Horizon[^"]*)"', scholarly, "paper title")
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "@id": SITE_URL + "#article",
        "headline": SITE_HEADING,
        "description": SITE_DESCRIPTION,
        "url": SITE_URL,
        "mainEntityOfPage": {"@type": "WebPage", "@id": SITE_URL},
        "image": SITE_URL + "assets/teaser-card.jpg",
        "inLanguage": "en",
        "datePublished": SITE_PUBLISHED,
        "dateModified": lastmod,
        "keywords": [k.strip() for k in SITE_KEYWORDS.split(",")],
        "isBasedOn": {
            "@type": "ScholarlyArticle",
            "@id": PAGE_URL + "#article",
            "name": paper_title,
            "url": PAGE_URL,
            "sameAs": [PAPER_DOI_URL],
        },
        "author": {"@type": "Organization", "name": "Simple Agent Lab", "url": LAB_URL},
        "publisher": {
            "@type": "Organization",
            "@id": LAB_URL + "#organization",
            "name": "Simple Agent Lab",
            "url": LAB_URL,
            "logo": LAB_URL + "assets/logo.png",
        },
    }
    head = head.replace(
        scholarly,
        '<script type="application/ld+json">\n'
        + json.dumps(article, ensure_ascii=False, indent=2)
        + "\n    </script>",
    )
    return head


def build_body(source):
    header = grab(r"<header class=\"site-header\">.*?</header>", source, "site header")
    # site.js needs both controls to exist; this page has no Chinese text, so
    # the language toggle is hidden and the Chinese theme label emptied.
    for old, new in [
        ('<button class="language-toggle" type="button" aria-label="切换为中文">中文</button>',
         '<button class="language-toggle" type="button" style="display:none"></button>'),
        ('<span class="theme-action-zh" lang="zh-CN">深色</span>',
         '<span class="theme-action-zh" lang="zh-CN"></span>'),
    ]:
        if old not in header:
            fail("header control not found: %r" % old[:50])
        header = header.replace(old, new)
    skip = grab(r'<a class="skip-link" href="#main">.*?</a>', source, "skip link")
    cover = grab(r'<figure class="cover">.*?</figure>', source, "cover figure")
    authors = grab(r'<p class="authors">.*?</p>', source, "authors")
    affiliations = grab(r'<p class="affiliations">.*?</p>', source, "affiliations")
    actions = grab(r'<div class="page-actions">.*?</div>', source, "page actions")
    link_old = ('<a class="project-page-link" href="%s" target="_blank" rel="noreferrer">\n'
                '            <span class="lang-en" lang="en">Short version (English)</span>\n'
                '            <span class="lang-zh" lang="zh-CN">英文短版</span>' % SITE_URL)
    if link_old not in actions:
        fail("the lab page's short-version link is missing from page-actions")
    actions = actions.replace(link_old,
        '<a class="project-page-link" href="%s">\n'
        '            <span class="lang-en" lang="en">Full article on simpleagentlab.com</span>' % PAGE_URL)

    def toc_item(sid):
        return grab(r'<li>\s*<a href="#%s">.*?</a>\s*</li>' % sid, source, "contents entry #" + sid)

    toc = "\n".join([
        '<div class="toc-rail">',
        '          <nav class="toc" aria-labelledby="toc-title">',
        '            <p class="toc-title" id="toc-title">Contents</p>',
        "            <ul>",
        '              <li><a href="#what-is-ai4ai">What is AI4AI?</a></li>',
        toc_item("loop"), toc_item("closure"), toc_item("horizon"),
        toc_item("composition"), toc_item("conclusion"), toc_item("cite"),
        "            </ul>",
        "          </nav>",
        "        </div>",
    ])

    def h2_and_takeaway(sec, sid):
        h2 = grab(r'<h2 id="%s">.*?</h2>' % sid, sec, "h2 #" + sid)
        takeaway = grab(r'<p class="takeaway">.*?</p>', sec, "takeaway of #" + sid)
        return h2, takeaway

    def full_link(sid, label):
        return '<p class="full-link"><a href="%s#%s">%s ↗</a></p>' % (PAGE_URL, sid, label)

    definition = "\n".join(
        ['<h2 id="what-is-ai4ai">What is AI4AI?</h2>'] + ["<p>%s</p>" % text for text in DEFINITION]
    )

    loop = section(source, "loop")
    h2, takeaway = h2_and_takeaway(loop, "loop")
    figure = grab(r'<figure class="framed plate">.*?</figure>', loop, "taxonomy figure")
    loop_out = "\n".join([h2, takeaway, figure, full_link("loop", "Read this section in full")])

    closure = section(source, "closure")
    h2, takeaway = h2_and_takeaway(closure, "closure")
    table = grab(r'<div class="table-scroll">.*?</table>\s*</div>', closure, "closure table")
    closure_out = "\n".join([h2, takeaway, table, full_link("closure", "Read the recursion ladder in full")])

    horizon = section(source, "horizon")
    h2, takeaway = h2_and_takeaway(horizon, "horizon")
    figure = grab(r'<figure class="framed plate">.*?</figure>', horizon, "model-design figure")
    horizon_out = "\n".join([h2, takeaway, figure, full_link("horizon", "Read both routes in full")])

    composition = section(source, "composition")
    h2, takeaway = h2_and_takeaway(composition, "composition")
    composition_out = "\n".join([h2, takeaway, full_link("composition", "Read where the failures show up")])

    conclusion = section(source, "conclusion")
    h2, takeaway = h2_and_takeaway(conclusion, "conclusion")
    eve = grab(r'<p>\s*<span class="lang-en" lang="en">The eve ends.*?</p>', conclusion, "eve paragraph")
    build_note = grab(r'<p>\s*<span class="lang-en" lang="en">If reading leaves you wanting to build.*?</p>', conclusion, "RSIHub paragraph")
    conclusion_out = "\n".join([h2, takeaway, eve, build_note])

    cite_h2 = grab(r'<h2 id="cite">.*?</h2>', source, "citation heading")
    cite_out = "\n".join([cite_h2, "<p>%s</p>" % CITE_NOTE])
    back = grab(r'<a class="back-link".*?</a>', source, "back link")
    tail = grab(r"</main>\s*(<script>.*)$", source, "page tail")

    doc = "\n\n".join([
        cover,
        '<p class="eyebrow">%s</p>' % EYEBROW,
        "<h1>%s</h1>" % SITE_HEADING,
        '<p class="tagline">%s</p>' % TAGLINE,
        authors,
        affiliations,
        actions,
        '<p class="opening-note">%s</p>' % INTRO,
        definition,
        loop_out,
        closure_out,
        horizon_out,
        composition_out,
        conclusion_out,
        '<p class="takeaway">%s</p>' % FULL_ARTICLE_NOTE,
        cite_out,
        back,
    ])
    return "\n".join([
        "  <body>",
        "    " + skip,
        "",
        "    " + header,
        "",
        '    <main id="main">',
        '      <article class="legal-page project-page has-toc">',
        "        " + toc,
        "",
        '        <div class="doc">',
        doc,
        "        </div>",
        "      </article>",
        "    </main>",
        "",
        "    " + tail,
    ])


def build_page(source):
    # Paths first, so every extracted fragment is already self-contained.
    for old, new in [
        ('href="../assets/', 'href="./assets/'),
        ('src="../assets/', 'src="./assets/'),
        ('href="../"', 'href="%s"' % LAB_URL),
        ('href="../disclaimer.html"', 'href="%sdisclaimer.html"' % LAB_URL),
        (PAGE_URL + "assets/", SITE_URL + "assets/"),
        (PAGE_URL, SITE_URL),
    ]:
        if old not in source:
            fail("rewrite target not found in ai4ai/index.html: %r" % old)
        source = source.replace(old, new)
    # Fragments that must keep pointing at the full article get it back.
    lastmod = grab(r'property="article:modified_time" content="([^"]+)"', source, "modified time")
    head = build_head(source, lastmod)
    body = build_body(source)
    page = english_only(head + "\n" + body)
    if not page.rstrip().endswith("</html>"):
        fail("page did not end with </html>")
    if re.search(r'(?:href|src)="\.\./', page):
        fail("parent-relative paths left in page")
    return page, lastmod


def build(output):
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    assets = output / "assets"
    assets.mkdir(parents=True)

    source = (ROOT / "ai4ai/index.html").read_text(encoding="utf-8")
    page, lastmod = build_page(source)
    (output / "index.html").write_text(page, encoding="utf-8")

    for path in sorted((ROOT / "ai4ai/assets").iterdir()):
        shutil.copy2(path, assets / path.name)
    for name in SHARED_ASSETS:
        shutil.copy2(ROOT / "assets" / name, assets / name)

    (output / "robots.txt").write_text(ROBOTS.format(site=SITE_URL), encoding="utf-8")
    (output / "sitemap.xml").write_text(
        SITEMAP.format(site=SITE_URL, lastmod=lastmod), encoding="utf-8"
    )
    (output / "README.md").write_text(
        README.format(site=SITE_URL, page=PAGE_URL, doi=PAPER_DOI_URL), encoding="utf-8"
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")
    return output


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    built = build(sys.argv[1])
    print("built %s (%d files)" % (built, sum(1 for p in built.rglob("*") if p.is_file())))
