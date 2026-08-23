"""Guards for the search-visibility metadata the site depends on.

These pages rank on a handful of fragile strings — a canonical link, one
sitemap entry, the phrase a reader actually searches for. A redesign that
drops one of them fails silently in production, so pin them here.
"""

from html.parser import HTMLParser
from pathlib import Path
import json
import unittest
import xml.etree.ElementTree as ElementTree


ROOT = Path(__file__).resolve().parents[1]
SITEMAP_NS = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
INDEXNOW_KEY = "7c0adc110ed926fce21c24f8501c1239ca908db70bfd0d6ea30fd88cbf8e440b"


class HeadParser(HTMLParser):
    """Collects the head metadata and JSON-LD payloads of a single page."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.metas = {}
        self.canonicals = []
        self.json_ld = []
        self._capture = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "title":
            self._capture = "title"
        if tag == "script" and values.get("type") == "application/ld+json":
            self._capture = "json_ld"
        if tag == "meta":
            name = values.get("name") or values.get("property")
            if name:
                self.metas.setdefault(name, []).append(values.get("content", ""))
        if tag == "link" and values.get("rel") == "canonical":
            self.canonicals.append(values.get("href"))

    def handle_endtag(self, tag):
        if tag in {"title", "script"}:
            self._capture = None

    def handle_data(self, data):
        if self._capture == "title":
            self.title += data
        elif self._capture == "json_ld":
            self.json_ld.append(data)


def parse_head(relative_path):
    parser = HeadParser()
    parser.feed((ROOT / relative_path).read_text(encoding="utf-8"))
    return parser


def json_ld_nodes(parser):
    """Flattens every JSON-LD block on a page into a list of typed nodes."""
    nodes = []
    for payload in parser.json_ld:
        document = json.loads(payload)
        nodes.extend(document.get("@graph", [document]))
    return nodes


class SurveyPageTests(unittest.TestCase):
    def setUp(self):
        self.parser = parse_head("ai4ai/index.html")
        self.text = (ROOT / "ai4ai/index.html").read_text(encoding="utf-8")

    def test_title_and_description_name_the_survey(self):
        self.assertIn("AI4AI", self.parser.title)
        self.assertIn("Survey", self.parser.title)
        description = self.parser.metas["description"][0]
        self.assertIn("AI4AI", description)
        self.assertIn("survey", description.lower())

    def test_page_is_indexable_and_canonical(self):
        self.assertEqual(
            self.parser.canonicals, ["https://simpleagentlab.com/ai4ai/"]
        )
        self.assertIn("index", self.parser.metas["robots"][0])
        self.assertNotIn("noindex", self.parser.metas["robots"][0])

    def test_visible_body_calls_the_paper_a_survey(self):
        # Metadata alone does not rank; the rendered English copy has to carry
        # the phrase too, near the heading and in the citation block.
        self.assertIn("A survey of AI4AI", self.text)
        self.assertIn("How to cite this AI4AI survey", self.text)

    def test_structured_data_describes_a_scholarly_survey(self):
        nodes = json_ld_nodes(self.parser)
        types = {node.get("@type") for node in nodes}
        self.assertIn("ScholarlyArticle", types)
        self.assertIn("BreadcrumbList", types)
        article = next(n for n in nodes if n.get("@type") == "ScholarlyArticle")
        self.assertIn("AI4AI", article["name"])
        self.assertEqual(article["genre"], "survey")
        self.assertIn("AI4AI survey", article["keywords"])
        self.assertTrue(article["abstract"])


class GoogleScholarTests(unittest.TestCase):
    """Scholar is this survey's route to a scholarly record now that arXiv's CS
    category refuses review articles without prior peer review, so the citation
    tags are load-bearing rather than decorative."""

    def setUp(self):
        self.parser = parse_head("ai4ai/index.html")

    def test_the_three_required_citation_fields_are_present(self):
        # Scholar discards every tag on the page if any one of these is missing.
        metas = self.parser.metas
        self.assertTrue(metas.get("citation_title", [""])[0])
        self.assertTrue(metas.get("citation_publication_date", [""])[0])
        self.assertGreaterEqual(len(metas.get("citation_author", [])), 1)

    def test_citation_authors_match_the_structured_data_byline(self):
        article = next(
            node
            for node in json_ld_nodes(self.parser)
            if node.get("@type") == "ScholarlyArticle"
        )
        expected = [
            "{}, {}".format(name.split()[-1], " ".join(name.split()[:-1]))
            for name in (author["name"] for author in article["author"])
        ]
        self.assertEqual(self.parser.metas["citation_author"], expected)

    def test_citation_title_matches_the_structured_data_title(self):
        article = next(
            node
            for node in json_ld_nodes(self.parser)
            if node.get("@type") == "ScholarlyArticle"
        )
        title = self.parser.metas["citation_title"][0]
        self.assertEqual(title, article["name"])
        self.assertEqual(title, article["headline"])

    def test_a_declared_pdf_is_actually_served(self):
        # A citation_pdf_url that 404s makes Scholar drop the record entirely,
        # so the tag may only appear once the file is committed.
        declared = self.parser.metas.get("citation_pdf_url")
        if not declared:
            self.skipTest("no PDF published yet")
        for url in declared:
            relative = url.removeprefix("https://simpleagentlab.com/")
            self.assertTrue(
                (ROOT / relative).is_file(), f"{url} is declared but not in the repo"
            )


class HomepageLinkTests(unittest.TestCase):
    def test_homepage_links_to_the_survey_with_descriptive_anchor_text(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Read the AI4AI survey", text)
        self.assertIn("A survey of AI4AI", text)


class CrossPageConsistencyTests(unittest.TestCase):
    """The homepage and /ai4ai/ both emit a ScholarlyArticle under one @id.
    Consumers merge nodes by @id, so any field both pages define must agree —
    this is exactly how the stale-title conflict slipped in once already."""

    ARTICLE_ID = "https://simpleagentlab.com/ai4ai/#article"

    def article_node(self, page):
        return next(
            node
            for node in json_ld_nodes(parse_head(page))
            if node.get("@id") == self.ARTICLE_ID
        )

    def test_shared_fields_agree_and_authors_stay_canonical(self):
        canonical = self.article_node("ai4ai/index.html")
        homepage = self.article_node("index.html")
        for key in set(canonical) & set(homepage):
            ours, theirs = homepage[key], canonical[key]
            # A bare {"@id": ...} reference is compatible with the full node it
            # points at; only differing values are a conflict.
            if isinstance(ours, dict) and isinstance(theirs, dict):
                if ours.get("@id") and ours.get("@id") == theirs.get("@id"):
                    continue
            self.assertEqual(ours, theirs, f"@id-merged field {key!r} conflicts")
        # The paper's byline is 23 people on the canonical page; the homepage
        # must not overwrite it with the lab as author.
        self.assertNotIn("author", homepage)


class SitemapTests(unittest.TestCase):
    def test_every_indexable_page_is_listed_once(self):
        tree = ElementTree.parse(ROOT / "sitemap.xml")
        locations = [
            element.text
            for element in tree.iterfind(".//sitemap:url/sitemap:loc", SITEMAP_NS)
        ]
        self.assertEqual(sorted(locations), sorted(set(locations)))
        self.assertEqual(
            sorted(locations),
            [
                "https://simpleagentlab.com/",
                "https://simpleagentlab.com/ai4ai/",
                "https://simpleagentlab.com/rsihub/",
            ],
        )

    def test_noindex_pages_stay_out_of_the_sitemap(self):
        text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for excluded in ("disclaimer.html", "/evolvex/"):
            self.assertNotIn(excluded, text)


class IndexNowTests(unittest.TestCase):
    def test_key_file_is_served_and_matches_the_deploy_ping(self):
        key_file = ROOT / f"{INDEXNOW_KEY}.txt"
        self.assertTrue(key_file.is_file())
        self.assertEqual(key_file.read_text(encoding="utf-8").strip(), INDEXNOW_KEY)
        workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertIn(INDEXNOW_KEY, workflow)


if __name__ == "__main__":
    unittest.main()
