from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile
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


def read_tracked_text(path):
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


class TrackedTextTests(unittest.TestCase):
    def test_read_tracked_text_skips_missing_and_non_utf8_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readable = root / "page.html"
            binary = root / "font.woff2"
            readable.write_text("RSIHub", encoding="utf-8")
            binary.write_bytes(b"\xff\xfe\x00\x01")

            self.assertEqual(read_tracked_text(readable), "RSIHub")
            self.assertIsNone(read_tracked_text(binary))
            self.assertIsNone(read_tracked_text(root / "deleted.html"))
            self.assertIsNone(read_tracked_text(root))


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
            "benchmark-results-rsihub-v2.svg",
            "evolve-lineage.svg",
            "paper-poster-lora-gen0.png",
            "paper-poster-lora-gen2.png",
            "rsihub-mark.svg",
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


class RSIHubCompatibilityTests(unittest.TestCase):
    def test_legacy_page_redirects_and_has_fallback(self):
        parser = parse_html("evolvex/index.html")
        self.assertEqual(parser.canonicals, [OVERVIEW_URL])
        self.assertIn("0; url=/rsihub/", parser.refreshes)
        self.assertIn("/rsihub/", parser.links)

    def test_sitemap_contains_only_the_canonical_project_route(self):
        text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("<loc>https://simpleagentlab.com/rsihub/</loc>", text)
        self.assertNotIn("<loc>https://simpleagentlab.com/evolvex/</loc>", text)

    def test_old_identity_is_absent_from_published_files(self):
        allowed = {
            Path("tests/test_rsihub_migration.py"),
        }
        forbidden = ("EvolveX",)
        tracked = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT
        ).decode("utf-8").split("\0")
        for tracked_path in tracked:
            if not tracked_path:
                continue
            relative = Path(tracked_path)
            path = ROOT / relative
            if relative in allowed:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                continue
            text = read_tracked_text(path)
            if text is None:
                continue
            for old_value in forbidden:
                self.assertNotIn(old_value, text, f"{old_value!r} remains in {relative}")
