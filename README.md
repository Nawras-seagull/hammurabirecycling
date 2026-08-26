# Hammurabi Golden Gate — Static Site Rebuild

A fully static (plain HTML/CSS/JS) rebuild of https://hammurabirecycling.com/# Hammurabi Golden Gate — WordPress → Static Rebuild

This is a full rebuild of the website for **Hammurabi Golden Gate**, Iraq's tire recycling factory. The live WordPress install this replaced had grown to about **1.6GB** for what was, content-wise, five pages. This version is **~40MB**, has no database, no PHP runtime, and no plugins — just HTML, CSS, and a small amount of vanilla JavaScript.

I took it on as a full rebuild rather than a redesign: same content, same URLs, same information — but rethought from the ground up as a static site, because that's what the content actually needed. There was no blog, no e-commerce, no user accounts — just five pages of information that WordPress was serving through an entire CMS stack for no real reason.

## What actually changed

- **WordPress → flat static files.** No database, no admin panel, no plugin surface to keep patched. Pages load close to instantly because there's nothing to query.
- **Same URL structure, preserved on purpose.** `/about-us/`, `/contact-us/`, `/our_products/` — kept exactly as they were so the migration wouldn't cost the client any of their existing search ranking.
- **Full English/Arabic bilingual support**, including proper right-to-left layout — not just mirrored text, but a layout that actually reflows correctly, plus separate typefaces chosen for Arabic rather than a fallback font.
- **A light/dark theme switch**, done without a flash-of-wrong-theme on load.
- **A visual identity pulled from the client's own name** rather than a generic "green recycling" template — the palette (basalt black, burnished gold, glazed-brick terracotta) is a nod to the Ishtar Gate of Babylon, since the company is named after Hammurabi.
- **A small pre-launch test suite** — link/asset checking, security header checks, accessibility checks, SEO/structured-data validation — written as separate standalone scripts so each one can be run (or dropped into another project) independently.



## The Arabic version

Building the right-to-left layout taught me something I didn't expect going in: because the CSS was already written with flexbox and grid rather than hardcoded left/right positioning, almost the entire layout mirrored itself correctly the moment `dir="rtl"` was set on the page — no extra work. Only a handful of things needed an explicit override (a couple of accent borders that visually needed to sit on the reading-start edge, and the direction a mobile nav drawer slides in from). That was a direct payoff of writing the CSS the "right" way the first time instead of reaching for absolute positioning everywhere.

The Arabic type isn't a generic web-safe fallback either — headings use Noto Kufi Arabic, chosen because Kufic script originated in Kufa, Iraq, which felt like the right pairing for a company already named after an ancient Iraqi king.

## Structure

```
/
├── index.html                  → Home
├── about-us/                   → About
├── our_products/                → Products
├── contact-us/                  → Contact (form via Formspree)
├── ar/                          → Arabic mirror of every page above
├── 404.html
├── assets/
│   ├── css/style.css            → the entire design system, one file
│   ├── js/main.js               → nav, theme switch, form handling, scroll reveal
│   ├── images/
│   └── video/
├── tests/                       → standalone pre-launch checks (see tests/README_TESTS.md)
├── netlify.toml
├── _redirects
├── sitemap.xml
└── robots.txt
```

## Running it locally

No build step, so there's nothing to install. Any static file server works:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000`. To test the `_redirects`/404 behavior the way Netlify actually serves it (a plain static server won't honor those), use the Netlify CLI instead:

```
netlify dev
```

## A note on the content

The text throughout — process descriptions, testimonials, contact details — is the real client's content, carried over and preserved rather than rewritten, with a few explicit exceptions I documented as I went (leftover placeholder text on the original site that I removed rather than translated, a couple of broken links I fixed, that kind of thing). The Arabic translation was written by hand for this rebuild and is flagged for a native-speaker review before anything goes live off it, the way any real translation should be before it's public-facing.

---

Live site: https://hammurabirecycling.com