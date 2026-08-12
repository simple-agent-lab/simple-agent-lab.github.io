# RSIHub Rename and Link Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the website's EvolveX presentation to RSIHub, migrate all code and documentation links, and preserve the old overview route as a compatibility redirect.

**Architecture:** Keep the existing plain HTML/CSS/JavaScript structure. Move the project overview and its colocated assets to lowercase `rsihub/`, reserve uppercase `/RSIHub/` for the separately deployed documentation, and replace `evolvex/index.html` with a static redirect page. Add standard-library regression tests that parse tracked text and HTML without introducing a dependency or build step.

**Tech Stack:** Static HTML5, CSS, vanilla JavaScript, SVG, XML sitemap, Python 3 `unittest` and `html.parser`, GitHub Pages.

## Global Constraints

- This is a rename and link migration only; do not alter RSIHub positioning, capability claims, architecture descriptions, maturity statements, or substantive project copy.
- Use `RSIHub` for the product name everywhere.
- Use `https://github.com/simple-agent-lab/RSIHub` as the repository base URL.
- Use `https://simpleagentlab.com/RSIHub/` as the case-sensitive documentation URL.
- Use `https://simpleagentlab.com/rsihub/` as the canonical website overview URL.
- Preserve `https://simpleagentlab.com/evolvex/` as a compatibility route that redirects to `/rsihub/` and provides a clickable fallback.
- Do not redesign pages or change shared language and theme behavior.

---

## File Structure

- `tests/test_rsihub_migration.py`: dependency-free regression checks for naming, links, canonical metadata, sitemap entries, and redirect behavior.
- `rsihub/index.html`: canonical RSIHub overview page, moved from `evolvex/index.html` and mechanically renamed.
- `rsihub/assets/*`: project illustrations moved with the overview page; SVG accessible titles use RSIHub.
- `index.html`: homepage visible name, overview link, actions, metadata, and JSON-LD.
- `evolvex/index.html`: compatibility-only redirect page; it contains no project presentation.
- `sitemap.xml`: lists the canonical `/rsihub/` route and excludes `/evolvex/`.

### Task 1: Establish the canonical RSIHub project page

**Files:**
- Create: `tests/test_rsihub_migration.py`
- Move: `evolvex/assets/architecture.svg` → `rsihub/assets/architecture.svg`
- Move: `evolvex/assets/benchmark-results.svg` → `rsihub/assets/benchmark-results.svg`
- Move: `evolvex/assets/evolve-lineage.svg` → `rsihub/assets/evolve-lineage.svg`
- Move: `evolvex/assets/paper-poster-lora-gen0.png` → `rsihub/assets/paper-poster-lora-gen0.png`
- Move: `evolvex/assets/paper-poster-lora-gen2.png` → `rsihub/assets/paper-poster-lora-gen2.png`
- Move and modify: `evolvex/index.html` → `rsihub/index.html`

**Interfaces:**
- Consumes: shared `../assets/styles.css`, `../assets/site.js`, and `../assets/favicon.svg` at the same relative depth as the old page.
- Produces: canonical overview route `/rsihub/`, repository base `https://github.com/simple-agent-lab/RSIHub`, and documentation action `https://simpleagentlab.com/RSIHub/` for later homepage and redirect work.

- [ ] **Step 1: Write focused failing project-page tests**

Create `tests/test_rsihub_migration.py` with:

```python
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
```

- [ ] **Step 2: Run the focused tests and verify the new route is absent**

Run:

```bash
python3 -m unittest tests.test_rsihub_migration.RSIHubProjectPageTests -v
```

Expected: FAIL because `rsihub/index.html` and `rsihub/assets/` do not exist.

- [ ] **Step 3: Move the page and assets without changing their relative layout**

Run:

```bash
mv evolvex rsihub
```

In `rsihub/index.html`, apply these exact mechanical substitutions throughout visible copy, accessibility text, metadata, JSON-LD, and links:

```text
EvolveX                                      → RSIHub
https://simpleagentlab.com/evolvex/          → https://simpleagentlab.com/rsihub/
https://github.com/simple-agent-lab/EvolveX  → https://github.com/simple-agent-lab/RSIHub
https://simple-agent-lab.github.io/EvolveX/  → https://simpleagentlab.com/RSIHub/
```

In `rsihub/assets/architecture.svg` and `rsihub/assets/benchmark-results.svg`, replace `EvolveX` with `RSIHub` in the `<title>` text. Do not change illustration geometry, labels unrelated to the product name, or raster assets.

- [ ] **Step 4: Run focused tests and inspect the rename diff**

Run:

```bash
python3 -m unittest tests.test_rsihub_migration.RSIHubProjectPageTests -v
git diff --check
git diff --find-renames -- rsihub evolvex tests/test_rsihub_migration.py
```

Expected: both tests PASS; `git diff --check` emits nothing; the page diff consists only of the directory move and approved name/URL substitutions.

- [ ] **Step 5: Commit the canonical project page**

```bash
git add rsihub evolvex tests/test_rsihub_migration.py
git commit -m "feat: migrate EvolveX page to RSIHub"
```

### Task 2: Migrate homepage presentation and discovery metadata

**Files:**
- Modify: `tests/test_rsihub_migration.py`
- Modify: `index.html`

**Interfaces:**
- Consumes: `/rsihub/`, `https://github.com/simple-agent-lab/RSIHub`, and `https://simpleagentlab.com/RSIHub/` from Task 1.
- Produces: homepage navigation and structured discovery data consistently pointing to the canonical RSIHub identity.

- [ ] **Step 1: Add failing homepage tests**

Append this class to `tests/test_rsihub_migration.py`:

```python
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
```

- [ ] **Step 2: Run the homepage tests and verify they reject the old identity**

Run:

```bash
python3 -m unittest tests.test_rsihub_migration.RSIHubHomepageTests -v
```

Expected: FAIL because the homepage still contains EvolveX names and URLs.

- [ ] **Step 3: Update homepage copy, actions, metadata, and JSON-LD**

In `index.html`, apply these exact substitutions:

```text
EvolveX                                      → RSIHub
./evolvex/                                   → ./rsihub/
https://simpleagentlab.com/evolvex/          → https://simpleagentlab.com/rsihub/
https://github.com/simple-agent-lab/EvolveX  → https://github.com/simple-agent-lab/RSIHub
https://simple-agent-lab.github.io/EvolveX/  → https://simpleagentlab.com/RSIHub/
```

Preserve all surrounding descriptions, keyword ordering, bilingual text, markup structure, and action labels.

- [ ] **Step 4: Run homepage and project-page tests**

Run:

```bash
python3 -m unittest tests.test_rsihub_migration -v
git diff --check
git diff -- index.html tests/test_rsihub_migration.py
```

Expected: all tests currently defined PASS; `git diff --check` emits nothing; the homepage diff contains only approved name and URL substitutions.

- [ ] **Step 5: Commit the homepage migration**

```bash
git add index.html tests/test_rsihub_migration.py
git commit -m "feat: feature RSIHub on homepage"
```

### Task 3: Preserve the legacy route and update the sitemap

**Files:**
- Modify: `tests/test_rsihub_migration.py`
- Create: `evolvex/index.html`
- Modify: `sitemap.xml`

**Interfaces:**
- Consumes: canonical `/rsihub/` overview from Task 1.
- Produces: browser-compatible `/evolvex/` redirect, fallback navigation, and canonical sitemap discovery.

- [ ] **Step 1: Add failing redirect, sitemap, and repository-wide regression tests**

Append this class to `tests/test_rsihub_migration.py`:

```python
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

    def test_old_identity_remains_only_in_migration_docs(self):
        allowed = {
            Path("docs/superpowers/specs/2026-08-12-rsihub-rename-migration-design.md"),
            Path("docs/superpowers/plans/2026-08-12-rsihub-rename-migration.md"),
            Path("tests/test_rsihub_migration.py"),
        }
        forbidden = (
            "EvolveX",
            "simple-agent-lab/EvolveX",
            "simple-agent-lab.github.io/EvolveX",
        )
        for path in ROOT.rglob("*"):
            relative = path.relative_to(ROOT)
            if not path.is_file() or ".git" in relative.parts or relative in allowed:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                continue
            text = path.read_text(encoding="utf-8")
            for old_value in forbidden:
                self.assertNotIn(old_value, text, f"{old_value!r} remains in {relative}")
```

- [ ] **Step 2: Run compatibility tests and verify the legacy page is absent**

Run:

```bash
python3 -m unittest tests.test_rsihub_migration.RSIHubCompatibilityTests -v
```

Expected: ERROR for missing `evolvex/index.html` and FAIL because the sitemap still lists `/evolvex/`.

- [ ] **Step 3: Add the static compatibility redirect**

Create `evolvex/index.html` with exactly:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RSIHub has moved | Simple Agent Lab</title>
    <meta name="robots" content="noindex, follow" />
    <link rel="canonical" href="https://simpleagentlab.com/rsihub/" />
    <meta http-equiv="refresh" content="0; url=/rsihub/" />
    <script>window.location.replace("/rsihub/" + window.location.search + window.location.hash);</script>
  </head>
  <body>
    <p>RSIHub has moved to <a href="/rsihub/">its new project page</a>.</p>
  </body>
</html>
```

The script preserves query parameters and fragments; the meta refresh and link cover disabled or failed JavaScript.

- [ ] **Step 4: Replace the sitemap project URL and refresh its date**

In `sitemap.xml`, replace:

```xml
    <loc>https://simpleagentlab.com/evolvex/</loc>
    <lastmod>2026-08-09</lastmod>
```

with:

```xml
    <loc>https://simpleagentlab.com/rsihub/</loc>
    <lastmod>2026-08-12</lastmod>
```

Also update the homepage `<lastmod>` to `2026-08-12`, because Task 2 changes homepage content.

- [ ] **Step 5: Run all migration tests and static sanity checks**

Run:

```bash
python3 -m unittest tests.test_rsihub_migration -v
git diff --check
git status --short
```

Expected: all tests PASS; `git diff --check` emits nothing; only the redirect, sitemap, and test additions from this task remain uncommitted.

- [ ] **Step 6: Serve and inspect all affected routes**

Start the documented preview server:

```bash
uv run python -m http.server 3000
```

In a browser, verify:

1. `http://localhost:3000/` shows RSIHub and its three links resolve to `/rsihub/`, the RSIHub GitHub repository, and `https://simpleagentlab.com/RSIHub/`.
2. `http://localhost:3000/rsihub/` loads shared CSS, JavaScript, favicon, and all five project images; English/Chinese and light/dark toggles still work.
3. `http://localhost:3000/evolvex/` immediately arrives at `/rsihub/`.
4. Browser console and network panels show no local 404s or JavaScript errors on the homepage or project page.

Expected: all four checks succeed. Stop the server with `Ctrl-C` after inspection.

- [ ] **Step 7: Commit compatibility and search discovery changes**

```bash
git add evolvex/index.html sitemap.xml tests/test_rsihub_migration.py
git commit -m "feat: redirect EvolveX page to RSIHub"
```

### Task 4: Final verification

**Files:**
- Verify only; no expected modifications.

**Interfaces:**
- Consumes: completed Tasks 1–3.
- Produces: evidence that the approved migration is internally consistent and ready to publish.

- [ ] **Step 1: Run the full dependency-free regression suite**

```bash
python3 -m unittest discover -s tests -v
```

Expected: every discovered test PASS.

- [ ] **Step 2: Verify the repository state and final diff**

```bash
git diff --check origin/main...HEAD
git status --short --branch
git log --oneline --decorate origin/main..HEAD
```

Expected: no whitespace errors; clean worktree; the branch contains the approved design, implementation plan, and three focused migration commits.

- [ ] **Step 3: Confirm the exact public targets one final time**

```bash
python3 - <<'PY'
from pathlib import Path

root = Path.cwd()
homepage = (root / "index.html").read_text()
project = (root / "rsihub/index.html").read_text()
redirect = (root / "evolvex/index.html").read_text()

assert "https://github.com/simple-agent-lab/RSIHub" in homepage and "https://github.com/simple-agent-lab/RSIHub" in project
assert "https://simpleagentlab.com/RSIHub/" in homepage and "https://simpleagentlab.com/RSIHub/" in project
assert "https://simpleagentlab.com/rsihub/" in project
assert 'url=/rsihub/' in redirect
print("RSIHub migration targets verified")
PY
```

Expected: prints `RSIHub migration targets verified`.
