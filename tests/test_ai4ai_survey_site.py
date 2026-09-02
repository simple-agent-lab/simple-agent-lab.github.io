"""The short English page that syncs to ai4ai-survey.github.io is built from
ai4ai/index.html. It must be self-contained, English-only, clearly shorter
than the full article, name its own domain, and link back to the article,
so that the two pages read as two pages rather than one mirrored."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_ai4ai_survey_site.py"
SITE_URL = "https://ai4ai-survey.github.io/"
LAB_PAGE_URL = "https://simpleagentlab.com/ai4ai/"


def visible_text(html):
    body = html.split("<body>", 1)[1]
    body = re.sub(r"<script.*?</script>", "", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


class SurveySiteBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "site"
        subprocess.run([sys.executable, str(SCRIPT), str(cls.out)], check=True)
        cls.page = (cls.out / "index.html").read_text(encoding="utf-8")
        cls.lab = (ROOT / "ai4ai/index.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_referenced_local_file_exists(self):
        refs = re.findall(r'(?:href|src)="\./([^"?#]+)', self.page)
        self.assertTrue(refs)
        for ref in refs:
            self.assertTrue((self.out / ref).is_file(), ref)

    def test_no_parent_relative_paths(self):
        self.assertNotRegex(self.page, r'(?:href|src)="\.\./')

    def test_page_names_its_own_domain(self):
        self.assertIn('<link rel="canonical" href="%s" />' % SITE_URL, self.page)
        self.assertIn('property="og:url" content="%s"' % SITE_URL, self.page)
        self.assertNotIn('rel="canonical" href="%s"' % LAB_PAGE_URL, self.page)
        self.assertIn(SITE_URL, (self.out / "sitemap.xml").read_text(encoding="utf-8"))
        self.assertIn(SITE_URL, (self.out / "robots.txt").read_text(encoding="utf-8"))

    def test_page_is_english_only(self):
        self.assertIn('<html lang="en" data-lang="en">', self.page)
        self.assertNotIn("lang-zh", self.page)
        self.assertNotIn("lang-en", self.page)
        self.assertIn('var language = "en";', self.page)
        self.assertNotRegex(visible_text(self.page), r"[一-鿿]")

    def test_scholarly_record_stays_on_the_lab_page(self):
        # Scholar should keep merging the lab page with the preprint; this
        # page is an article about the paper, not a second copy of it.
        self.assertNotIn('name="citation_', self.page)
        self.assertNotIn('"@type": "ScholarlyArticle",\n        "@id"', self.page)
        self.assertIn('"isBasedOn"', self.page)
        self.assertIn('"@type": "Article"', self.page)

    def test_the_two_pages_are_different_pages(self):
        lab_title = re.search(r"<title>(.*?)</title>", self.lab).group(1)
        site_title = re.search(r"<title>(.*?)</title>", self.page).group(1)
        self.assertNotEqual(lab_title, site_title)
        self.assertIn("What Is AI4AI", site_title)
        lab_h1 = re.search(r"<h1>(.*?)</h1>", self.lab).group(1)
        site_h1 = re.search(r"<h1>(.*?)</h1>", self.page).group(1)
        self.assertNotEqual(lab_h1, site_h1)
        # The short page keeps the takeaways and drops the section bodies.
        self.assertEqual(self.page.count('class="takeaway"'), 6)
        self.assertNotIn("Darwin Gödel Machine", self.page)
        self.assertNotIn("Across generations", self.page)
        english_lab = re.sub(r'<span class="lang-zh" lang="zh-CN">.*?</span>', "", self.lab, flags=re.S)
        self.assertLess(len(visible_text(self.page)), 0.5 * len(visible_text(english_lab)))
        # Its own definition of the field, not the paper's abstract.
        self.assertIn('id="what-is-ai4ai"', self.page)
        self.assertNotIn('id="abstract"', self.page)
        self.assertNotIn("@misc{", self.page)

    def test_the_two_pages_link_to_each_other(self):
        self.assertIn('href="%s"' % SITE_URL, self.lab)
        self.assertIn('href="%s"' % LAB_PAGE_URL, self.page)
        for anchor in ("#loop", "#closure", "#horizon", "#composition"):
            self.assertIn('href="%s%s"' % (LAB_PAGE_URL, anchor), self.page)

    def test_pages_serves_the_raw_tree(self):
        self.assertTrue((self.out / ".nojekyll").exists())


if __name__ == "__main__":
    unittest.main()
