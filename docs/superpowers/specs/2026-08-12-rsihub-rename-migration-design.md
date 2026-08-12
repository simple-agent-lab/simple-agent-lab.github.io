# RSIHub Rename and Link Migration Design

## Goal

Rename the website's EvolveX presentation to RSIHub and migrate its links and
search metadata without changing the project's positioning, capabilities, or
substantive copy.

## Public URLs

- The website overview page moves from `https://simpleagentlab.com/evolvex/`
  to `https://simpleagentlab.com/rsihub/`.
- The documentation action points to the distinct, case-sensitive URL
  `https://simpleagentlab.com/RSIHub/`.
- Code and repository deep links point to
  `https://github.com/simple-agent-lab/RSIHub`.
- The old `/evolvex/` path remains as a compatibility redirect to `/rsihub/`.

GitHub Pages cannot return a custom HTTP 301 for a static HTML route. The old
page will therefore use an immediate client-side redirect, declare `/rsihub/`
as its canonical URL, and provide a visible fallback link.

## Content Migration

The homepage will:

- replace the EvolveX name with RSIHub in visible English and Chinese content;
- link the project summary to `/rsihub/`;
- link the Code action to the RSIHub GitHub repository; and
- link the Docs action to `https://simpleagentlab.com/RSIHub/`.

The existing project page and its assets will move from `evolvex/` to
`rsihub/`. All EvolveX names, accessibility labels, SVG titles, and repository
links will become RSIHub equivalents. This is a rename and link migration
only: descriptions of the framework, its architecture, maturity, workflows,
and capabilities will remain substantively unchanged.

## Metadata and Discovery

The migration will update:

- HTML titles, descriptions, keywords, and canonical links;
- Open Graph and Twitter metadata;
- JSON-LD names, identifiers, URLs, repository links, and `sameAs` values;
- the XML sitemap, replacing `/evolvex/` with `/rsihub/`;
- image titles and alternative text that contain the old name.

The canonical website page is lowercase `/rsihub/`. The uppercase `/RSIHub/`
path is reserved for the separately published documentation.

## Compatibility and Failure Handling

Visitors reaching `/evolvex/` will be sent to `/rsihub/`. If automatic
redirect behavior is disabled or unavailable, the compatibility page will
show a direct link to the new page. No other website routes or projects will
change.

## Verification

Verification will:

1. scan tracked text files for obsolete `EvolveX` names and old repository or
   documentation URLs, allowing only the compatibility route where necessary;
2. validate the homepage links, the lowercase overview canonical URL, the
   uppercase documentation link, and the old-route redirect;
3. serve the static site locally and inspect the homepage, `/rsihub/`, and
   `/evolvex/`; and
4. exercise English and Chinese presentation plus light and dark themes to
   ensure the directory move does not break shared scripts, styles, or assets.

## Out of Scope

- Repositioning RSIHub or changing capability claims.
- Redesigning the homepage or project page.
- Changing the shared language or theme behavior.
- Changing the separately deployed RSIHub documentation site.
