# Welcome to Acme Docs

This page lives inside **Acme Docs**, an outer site shell with its own sidebar, top bar,
and branding. Everything in *this* content column was rendered by KPress from a Markdown
file.

That is the whole idea of the wrapper pattern:

- The **outer builder** (here, a tiny hand-written one that stands in for your CMS or
  static-site framework) owns the page shell, navigation, and routing.
- **KPress** is the *inner library*: it turns each Markdown document into a styled,
  self-contained HTML block plus the CSS, JS, and fonts it needs.

Browse the sidebar to see more documents, each one embedded the same way.
