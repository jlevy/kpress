/**
 * The document-actions widget (registry id `doc-actions`): small text badge
 * buttons for taking the document away — export it as PDF via the browser's
 * print dialog (the printout is the clean `print.css` rendering) and open
 * its Markdown twin. Off by default; a host opts in with
 * `format.widgets: {doc-actions: on}` (or a config map).
 *
 * The badges are hand-drawn "icons" built from type, not glyphs: the format
 * letters ("PDF", "MD") one notch below the TOC "Contents" label, inside a
 * tight currentColor frame (size and corner are the
 * --kpress-doc-actions-badge-* tokens; square by default). Not a printer or
 * generic file glyph — those do not say WHAT an action yields; the format
 * letters do.
 *
 * Config is defined here, in the widget's own JS (schema-with-the-code):
 *
 *   { print: true,            // the Export PDF button
 *     markdown: true,         // the View as Markdown link
 *     markdown_url: "" }      // explicit Markdown URL; empty derives it
 *
 * Markdown URL convention: publish the Markdown twin at the page's own URL
 * with a `.md` suffix — `.html`/`.htm` replaced, anything else appended
 * (`/note.html` → `/note.md`, `/note` → `/note.md`). The widget derives that
 * URL from `location.pathname` by default; `markdown_url` overrides it for
 * hosts with a different twin layout. Print needs no config: the dialog is
 * the browser's own.
 *
 * Placement: when the document renders the content card (`.kpress-long-text`)
 * the widget relocates its mount into the card and pins to its upper-right
 * corner — the same placement embedding hosts give their own document
 * actions. Without a card it stays a fixed cluster at the doc-actions inset
 * tokens (see style-tokens.css). Like every chrome widget it client-renders
 * into its server mount (no-JS rule) from the public layers only.
 */

import { widgets } from "./runtime.js";

/**
 * The default Markdown-twin URL for a page path: `.html`/`.htm` becomes
 * `.md`, an extensionless path gets `.md` appended, and a directory path
 * gets `index.md`.
 *
 * @param {string} pathname
 * @returns {string}
 */
export function markdownTwinUrl(pathname) {
  const base = pathname.replace(/\.x?html?$/i, "");
  return base.endsWith("/") ? `${base}index.md` : `${base}.md`;
}

/**
 * Attribute-escape a URL for interpolation into an href.
 *
 * @param {string} value
 * @returns {string}
 */
function escapeAttr(value) {
  return value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
}

/**
 * @param {HTMLElement} el server mount (or embed-supplied element)
 * @param {Record<string, unknown>} [config]
 */
export function mountDocActions(el, config) {
  const cfg =
    config && typeof config === "object" ? config : /** @type {Record<string, unknown>} */ ({});
  const showPrint = cfg.print !== false;
  const showMarkdown = cfg.markdown !== false;
  const markdownUrl =
    typeof cfg.markdown_url === "string" && cfg.markdown_url !== ""
      ? cfg.markdown_url
      : markdownTwinUrl(window.location.pathname);

  const parts = [];
  if (showPrint) {
    parts.push(
      `<button type="button" class="kpress-doc-actions-btn" data-kpress-doc-print ` +
        `title="Export PDF" aria-label="Export PDF">` +
        `<span class="kpress-doc-actions-badge">PDF</span></button>`,
    );
  }
  if (showMarkdown) {
    parts.push(
      `<a class="kpress-doc-actions-btn" href="${escapeAttr(markdownUrl)}" ` +
        `title="View as Markdown" aria-label="View as Markdown">` +
        `<span class="kpress-doc-actions-badge">MD</span></a>`,
    );
  }
  el.innerHTML = parts.join("");

  // Card documents pin the cluster inside the card's upper-right corner
  // (the .kpress-doc-actions rules in components.css switch on ancestry).
  // Prefer the mount's own document (an embed host mounts inside its
  // .kpress); the standalone page emits the mount as a sibling of the
  // article, so fall back to the page's first card.
  const card =
    el.closest(".kpress")?.querySelector(".kpress-long-text") ??
    document.querySelector(".kpress .kpress-long-text");
  if (card && !card.contains(el)) {
    card.appendChild(el);
  }

  const printButton = el.querySelector("[data-kpress-doc-print]");
  printButton?.addEventListener("click", () => {
    window.print();
  });
}

widgets.register("doc-actions", { mount: mountDocActions });
