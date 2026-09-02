"""The standalone copy of /ai4ai/ that syncs to ai4ai-survey.github.io must
be self-contained: no path may reach outside the built directory, and the
page must name its own domain rather than the lab site's."""

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


class SurveySiteBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "site"
        subprocess.run([sys.executable, str(SCRIPT), str(cls.out)], check=True)
        cls.page = (cls.out / "index.html").read_text(encoding="utf-8")

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

    def test_the_two_pages_are_not_mirrors(self):
        # Same paper, different jobs: the lab site carries the article, this
        # domain is the project page. Title and description must differ, and
        # each page must link to the other.
        lab = (ROOT / "ai4ai/index.html").read_text(encoding="utf-8")
        lab_title = re.search(r"<title>(.*?)</title>", lab).group(1)
        site_title = re.search(r"<title>(.*?)</title>", self.page).group(1)
        self.assertNotEqual(lab_title, site_title)
        self.assertIn("Project Page", site_title)
        lab_h1 = re.search(r"<h1>(.*?)</h1>", lab).group(1)
        site_h1 = re.search(r"<h1>(.*?)</h1>", self.page).group(1)
        self.assertNotEqual(lab_h1, site_h1)
        lab_desc = re.search(r'name="description"\s+content="([^"]*)"', lab).group(1)
        site_desc = re.search(r'name="description"\s+content="([^"]*)"', self.page).group(1)
        self.assertNotEqual(lab_desc, site_desc)
        self.assertIn('href="%s"' % SITE_URL, lab)
        self.assertIn('href="%s"' % LAB_PAGE_URL, self.page)
        self.assertIn('class="opening-note"', self.page)

    def test_pages_serves_the_raw_tree(self):
        self.assertTrue((self.out / ".nojekyll").exists())


if __name__ == "__main__":
    unittest.main()
