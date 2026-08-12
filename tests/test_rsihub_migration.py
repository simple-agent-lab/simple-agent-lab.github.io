from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/simple-agent-lab/RSIHub"
DOCS_URL = "https://simpleagentlab.com/RSIHub/"
OVERVIEW_URL = "https://simpleagentlab.com/rsihub/"


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.canonicals = []
        self.refreshes = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and "href" in values:
            self.links.append(values["href"])
        if tag == "link" and values.get("rel") == "canonical":
            self.canonicals.append(values.get("href"))
        if tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            self.refreshes.append(values.get("content"))


def parse_html(relative_path):
    parser = LinkParser()
    parser.feed((ROOT / relative_path).read_text(encoding="utf-8"))
    return parser


class RSIHubProjectPageTests(unittest.TestCase):
    def test_canonical_project_page_uses_new_identity_and_urls(self):
        page_path = ROOT / "rsihub/index.html"
        self.assertTrue(page_path.is_file())
        text = page_path.read_text(encoding="utf-8")
        parser = parse_html("rsihub/index.html")
        self.assertIn("RSIHub", text)
        self.assertNotIn("EvolveX", text)
        self.assertNotIn("simple-agent-lab/EvolveX", text)
        self.assertNotIn("simple-agent-lab.github.io/EvolveX", text)
        self.assertEqual(parser.canonicals, [OVERVIEW_URL])
        self.assertIn(REPO_URL, parser.links)
        self.assertIn(DOCS_URL, parser.links)

    def test_project_assets_moved_and_svg_titles_renamed(self):
        assets = ROOT / "rsihub/assets"
        expected = {
            "architecture.svg",
            "benchmark-results.svg",
            "evolve-lineage.svg",
            "paper-poster-lora-gen0.png",
            "paper-poster-lora-gen2.png",
        }
        self.assertEqual({path.name for path in assets.iterdir()}, expected)
        for svg in assets.glob("*.svg"):
            self.assertNotIn("EvolveX", svg.read_text(encoding="utf-8"))


class RSIHubHomepageTests(unittest.TestCase):
    def test_homepage_uses_rsihub_name_and_actions(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")
        parser = parse_html("index.html")
        self.assertIn("RSIHub", text)
        self.assertNotIn("EvolveX", text)
        self.assertIn("./rsihub/", parser.links)
        self.assertIn(REPO_URL, parser.links)
        self.assertIn(DOCS_URL, parser.links)

    def test_homepage_structured_data_uses_canonical_rsihub_urls(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'"@id": "{OVERVIEW_URL}#software"', text)
        self.assertIn(f'"url": "{OVERVIEW_URL}"', text)
        self.assertIn(f'"codeRepository": "{REPO_URL}"', text)
        self.assertNotIn("simpleagentlab.com/evolvex/", text)
        self.assertNotIn("simple-agent-lab/EvolveX", text)
        self.assertNotIn("simple-agent-lab.github.io/EvolveX", text)
