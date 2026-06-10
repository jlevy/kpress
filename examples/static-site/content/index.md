---
title: KPress Static Site Example
---
# KPress Static Site Example

**[Home](/)** · [Getting started](/guides/getting-started.html) ·
[Markdown features](/guides/markdown-features.html) · [API reference](/reference/api/)

This whole site was produced from a folder of Markdown files by a single call to
`kpress.publish.build_site`. There is no outer framework and no template engine; KPress
acts as a complete static site generator.

## What You Get Out of the Box

- Styled, responsive HTML with light and dark themes
- Self-contained CSS, JavaScript, and web fonts (no CDN required)
- Automatic table of contents, syntax highlighting, math, and diagrams
- Clean URLs derived from the `content/` directory layout

## Pages in This Site

- [Getting started](guides/getting-started.html)
- [Markdown features](guides/markdown-features.html)
- [API reference](reference/api/) (note the custom URL)

> KPress owns the *entire* page here.
> To keep your own page shell instead (your navigation, your branding, your framework),
> see the `wrapped-site/` example, which embeds KPress-rendered documents inside an
> outer template.
