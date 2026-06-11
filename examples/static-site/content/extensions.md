---
title: Extension Model Demo
---

# Extension Model Demo

This page demonstrates the KPress extension model — every customization here is
**site code** (`demo/extensions.js`, injected via `head_extra_html`), with zero
KPress edits:

1. **Minimap widget** — the panel listing this page's headings is a *new* widget
   registered by the site, computed from the published page model
   (`kpress.model().headings`) and mounted into a server-emitted mount
   (`format.widgets: {minimap: on}`).
2. **Bare theme toggle** — the ◐ button drives the built-in theme *engine*
   (`kpress.theme.set(...)`) directly: the settings gear is only the engine's
   default presentation.
3. **TOC toggle tweak** — scroll on a narrow window: the floating TOC button uses
   a custom circle icon and an always-visible policy
   (`kpress.behaviors.configure("toc", {icon, visible: () => true})`) — one
   aspect changed, the rest of the TOC behavior untouched.
4. **Footnote handling override** — this footnote[^demo] jumps on click instead
   of showing a hover preview (`kpress.behaviors.override("footnote-preview", …)`
   over unchanged markup).
5. **Injected HTML made interactive** — the term
   <span data-gloss="A reusable, overridable piece of page chrome">widget</span>
   is plain HTML in this page's Markdown; a site-registered `glossary` behavior
   binds it exactly the way KPress binds its own markup.

## How it is wired

```yaml
# kpress.yml
site:
  head_extra_html: '<script type="module" src="/demo/extensions.js"></script>'
format:
  widgets:
    settings: { choosers: [theme, reading-font, font-set] }
    minimap: on
    theme-toggle: on
sources:
  - path: content
    static: ["demo/**"]
```

## A second section

Some prose so the minimap and TOC have more than one entry to show.

[^demo]: This footnote opens by scrolling to the definition — the override in
    `demo/extensions.js` replaced the default hover preview.
