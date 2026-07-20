import {
  dismissOnEscape,
  dismissOnResize,
  OVERLAY_DEFAULT_GAP_PX,
  OVERLAY_VIEWPORT_MARGIN_PX,
} from "./overlay.js";
import { behaviors } from "./runtime.js";
import { rectRelativeToViewport, resolveKpressViewport, viewportBounds } from "./viewport.js";

const TOOLTIP_VIEWPORT_MARGIN_PX = OVERLAY_VIEWPORT_MARGIN_PX;
const TOOLTIP_GAP_PX = OVERLAY_DEFAULT_GAP_PX;
export const TOOLTIP_SHOW_DELAY_MS = 500;
const TOOLTIP_HIDE_DELAY_MS = 2500;
const TOOLTIP_WIDE_RIGHT_HIDE_DELAY_MS = 4000;
const TOOLTIP_MOVING_TOWARD_HIDE_DELAY_MS = 500;
const TOOLTIP_MOUSE_TRACK_MARGIN_PX = 20;
const MOBILE_TOOLTIP_BREAKPOINT_PX = 640;
const WIDE_TOOLTIP_BREAKPOINT_PX = 1200;
// Minimum free space to the right of the reading column before a margin
// (wide-right) tooltip is used instead of an adjacent popover.
const MARGIN_TOOLTIP_MIN_WIDTH_PX = 320;
// Per-kind max widths in px, matching the CSS caps (.kpress-tooltip 20rem,
// .kpress-tooltip-footnote 25rem, .kpress-tooltip-wide-right 24rem, at a 16px
// root). The JS must not exceed these — otherwise the tooltip grows to its
// max-content width and runs off the viewport.
const TOOLTIP_MAX_WIDTH_PX = 320;
const FOOTNOTE_TOOLTIP_MAX_WIDTH_PX = 400;
const WIDE_RIGHT_TOOLTIP_MAX_WIDTH_PX = 384;
const WIDE_RIGHT_TOOLTIP_GAP_PX = 16;
const FOOTNOTE_MAX_CHARS = 400;
const INTERNAL_LINK_MAX_CHARS = 1000;

// Placement modes (behavior flags). "auto" is the responsive ladder: a margin
// tooltip beside the reading column on wide screens with room, else an adjacent
// popover, and a bottom bar on narrow screens. "margin"/"inline"/"mobile" force
// or bias a mode. Settings are per-kind, taken from each behavior's config —
// e.g. kpress.behaviors.configure("tooltip", { placement: "margin" }).
const DEFAULT_PLACEMENT = "auto";

/** @type {Map<string, { placement?: string; showDelayMs?: number }>} */
const kindSettings = new Map();

/**
 * @param {string} kind
 * @returns {{ placement?: string; showDelayMs?: number }}
 */
function settingsForKind(kind) {
  return kindSettings.get(kind) || {};
}

const POSITION_CLASSES = [
  "bottom-right",
  "top-right",
  "bottom-left",
  "top-left",
  "bottom",
  "top",
  "left",
  "right",
  "mobile-bottom",
  "wide-right",
];

/** @typedef {{ anchor: HTMLAnchorElement; tooltip: HTMLElement; position: string }} ActiveTooltip */

/** @type {ActiveTooltip | null} */
let activeTooltip = null;
let tooltipHideTimer = 0;
let tooltipShowTimer = 0;

function clearTooltipHideTimer() {
  if (!tooltipHideTimer) {
    return;
  }
  window.clearTimeout(tooltipHideTimer);
  tooltipHideTimer = 0;
}

function clearTooltipShowTimer() {
  if (!tooltipShowTimer) {
    return;
  }
  window.clearTimeout(tooltipShowTimer);
  tooltipShowTimer = 0;
}

/**
 * Fade out and remove a single tooltip element.
 * Removes the visible class, then waits for the CSS transition to end
 * before removing the DOM node. Falls back to immediate removal if the
 * tooltip has no running transition (e.g. already hidden).
 *
 * @param {Element} tooltip
 */
function fadeOutAndRemove(tooltip) {
  if (!tooltip.classList.contains("kpress-tooltip-visible")) {
    tooltip.remove();
    return;
  }
  tooltip.classList.remove("kpress-tooltip-visible");
  const onEnd = () => {
    tooltip.removeEventListener("transitionend", onEnd);
    tooltip.remove();
  };
  tooltip.addEventListener("transitionend", onEnd);
  // Safety: if transitionend never fires (e.g. display:none, no transition),
  // remove after a generous timeout matching the CSS duration.
  window.setTimeout(() => {
    tooltip.removeEventListener("transitionend", onEnd);
    if (tooltip.parentNode) {
      tooltip.remove();
    }
  }, 700);
}

function removeKpressTooltips() {
  clearTooltipHideTimer();
  clearTooltipShowTimer();
  for (const tooltip of document.querySelectorAll(".kpress-tooltip")) {
    fadeOutAndRemove(tooltip);
  }
  activeTooltip = null;
}

/**
 * @param {string} text
 * @returns {string}
 */
function sanitizeText(text) {
  return text
    .replace(/\s+/g, " ")
    .trim()
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

/**
 * @param {Element} element
 * @returns {Element}
 */
function cloneTooltipContent(element) {
  const clone = /** @type {Element} */ (element.cloneNode(true));
  for (const backLink of clone.querySelectorAll(
    ".kpress-footnote-backref, .footnote, .reversefootnote",
  )) {
    backLink.remove();
  }
  return clone;
}

/**
 * @param {Element} element
 * @returns {string}
 */
function extractTextContent(element) {
  return (cloneTooltipContent(element).textContent || "").replace(/\s+/g, " ").trim();
}

/**
 * @param {Element} element
 * @returns {string}
 */
function extractHtmlContent(element) {
  return cloneTooltipContent(element).innerHTML || "";
}

/**
 * @param {string} text
 * @param {number} maxLength
 * @returns {string}
 */
function truncateText(text, maxLength) {
  const trimmed = text.replace(/\s+/g, " ").trim();
  if (trimmed.length <= maxLength) {
    return trimmed;
  }
  const truncated = trimmed.slice(0, maxLength);
  const lastSpace = truncated.lastIndexOf(" ");
  if (lastSpace > maxLength * 0.8) {
    return `${truncated.slice(0, lastSpace)}...`;
  }
  return `${truncated}...`;
}

/**
 * @param {Element} element
 * @param {number} maxLength
 * @returns {string}
 */
function truncatedHtmlContent(element, maxLength) {
  const text = extractTextContent(element);
  if (text.length <= maxLength) {
    return extractHtmlContent(element);
  }
  return sanitizeText(truncateText(text, maxLength));
}

/**
 * @param {Element} heading
 * @returns {Element | null}
 */
function firstFollowingParagraph(heading) {
  let next = heading.nextElementSibling;
  while (next && !next.matches("p, h1, h2, h3, h4, h5, h6")) {
    next = next.nextElementSibling;
  }
  return next?.matches("p") ? next : null;
}

/**
 * @param {Element} target
 * @returns {{ html: string; text: string } | null}
 */
function internalTooltipContent(target) {
  if (target.matches("h1, h2, h3, h4, h5, h6")) {
    const headingLevel = Number(target.tagName.slice(1));
    const label = headingLevel <= 2 ? "Section" : "Subsection";
    const headingText = extractTextContent(target);
    let html = `<strong>${label}:</strong> ${sanitizeText(headingText)}`;
    const paragraph = firstFollowingParagraph(target);
    if (paragraph) {
      html += `<br><br>${sanitizeText(truncateText(extractTextContent(paragraph), 150))}`;
    }
    return { html, text: headingText };
  }

  if (target.matches("figure, .kpress-figure, .figure")) {
    const caption = target.querySelector("figcaption, .kpress-figcaption, .caption");
    const text = caption ? extractTextContent(caption) : "Figure";
    return { html: `<strong>Figure:</strong> ${sanitizeText(text)}`, text };
  }

  if (target.matches("table, .kpress-table-wrap, .table-container")) {
    const caption = target.querySelector("caption");
    const firstHeader = target.querySelector("th");
    const text = caption
      ? extractTextContent(caption)
      : firstHeader
        ? extractTextContent(firstHeader)
        : "Table";
    return { html: `<strong>Table:</strong> ${sanitizeText(text)}`, text };
  }

  if (target.matches("pre, .kpress-code, .code-block-wrapper")) {
    const code = target.querySelector("code") || target;
    const firstLine = extractTextContent(code).split("\n")[0] || "Code";
    const text = truncateText(firstLine, 100);
    return { html: `<strong>Code:</strong> <code>${sanitizeText(text)}</code>`, text };
  }

  if (target.matches("details")) {
    const summary = target.querySelector("summary");
    if (!summary) {
      return null;
    }
    const text = extractTextContent(summary);
    return { html: `<strong>Details:</strong> ${sanitizeText(text)}`, text };
  }

  if (target.matches("section, article")) {
    const heading = target.querySelector("h1, h2, h3, h4, h5, h6");
    const paragraph = target.querySelector("p");
    if (heading) {
      const headingText = extractTextContent(heading);
      let html = `<strong>Section:</strong> ${sanitizeText(headingText)}`;
      if (paragraph) {
        html += `<br><br>${sanitizeText(truncateText(extractTextContent(paragraph), 150))}`;
      }
      return { html, text: headingText };
    }
  }

  const text = extractTextContent(target);
  if (!text) {
    return null;
  }
  return { html: sanitizeText(truncateText(text, INTERNAL_LINK_MAX_CHARS)), text };
}

/**
 * @param {HTMLAnchorElement} anchor
 * @param {Element} target
 * @returns {{ html: string; text: string; footnoteId?: string } | null}
 */
function tooltipContentForAnchor(anchor, target) {
  const href = anchor.getAttribute("href") || "";
  const isFootnote =
    href.startsWith("#fn-") || Boolean(anchor.closest(".kpress-footnote-ref, .footnote-ref"));
  if (!isFootnote) {
    return internalTooltipContent(target);
  }

  const footnoteId = href.slice(1);
  const html = `${truncatedHtmlContent(
    target,
    FOOTNOTE_MAX_CHARS,
  )}<span class="kpress-footnote-nav"><a href="#${sanitizeText(
    footnoteId,
  )}" class="kpress-footnote-nav-link" data-kpress-footnote-nav="true" title="Go to footnote">&nbsp;↓&nbsp;</a></span>`;
  return { html, text: extractTextContent(target), footnoteId };
}

/**
 * Resolve the reading column used to place margin (wide-right) tooltips. kpress
 * assembles the document body as `<div class="kpress-prose">`; a margin tooltip
 * floats just to the right of that column. Falls back to the first prose column
 * in the document, then to the legacy `#main-content` id some embedding hosts
 * still use. (The legacy id is why this mode was dead in kpress: kpress emits no
 * `#main-content`, so the old lookup always returned null and every tooltip fell
 * back to an adjacent popover.)
 *
 * @param {Element} trigger
 * @returns {Element | null}
 */
function resolveReadingColumn(trigger) {
  return (
    trigger.closest?.(".kpress-prose") ||
    document.querySelector(".kpress-prose") ||
    document.getElementById("main-content")
  );
}

/**
 * @param {Element} trigger
 * @returns {string}
 */
export function chooseTooltipPosition(trigger) {
  const kind = isFootnoteAnchor(trigger) ? "footnote" : "link";
  const placement = settingsForKind(kind).placement || DEFAULT_PLACEMENT;
  const viewport = resolveKpressViewport(trigger);
  const bounds = viewportBounds(viewport);
  // A narrow viewport always uses the bottom bar; "mobile" forces it everywhere.
  if (placement === "mobile" || bounds.width <= MOBILE_TOOLTIP_BREAKPOINT_PX) {
    return "mobile-bottom";
  }
  if (trigger.closest("table")) {
    return "bottom-right";
  }
  // Margin (wide-right) tooltip beside the reading column: used by the default
  // ("auto") and "margin" modes when there is room; "inline" skips it.
  if (placement === "auto" || placement === "margin") {
    const readingColumn = resolveReadingColumn(trigger);
    if (readingColumn && bounds.width >= WIDE_TOOLTIP_BREAKPOINT_PX) {
      const contentRect = rectRelativeToViewport(readingColumn.getBoundingClientRect(), viewport);
      if (bounds.width - contentRect.right >= MARGIN_TOOLTIP_MIN_WIDTH_PX) {
        return "wide-right";
      }
    }
  }
  const rect = rectRelativeToViewport(trigger.getBoundingClientRect(), viewport);
  return rect.bottom + 220 + TOOLTIP_VIEWPORT_MARGIN_PX <= bounds.height
    ? "bottom-right"
    : "top-right";
}

/**
 * @param {HTMLElement} tooltip
 * @param {string} position
 */
function setPositionClass(tooltip, position) {
  for (const className of POSITION_CLASSES) {
    tooltip.classList.remove(`kpress-tooltip-${className}`);
  }
  tooltip.classList.add(`kpress-tooltip-${position}`);
  tooltip.setAttribute("data-kpress-tooltip-position", position);
}

/**
 * @param {HTMLAnchorElement} anchor
 * @param {HTMLElement} tooltip
 */
export function positionTooltip(anchor, tooltip) {
  const viewport = resolveKpressViewport(anchor);
  const bounds = viewportBounds(viewport);
  const margin = TOOLTIP_VIEWPORT_MARGIN_PX;
  tooltip.style.insetInlineStart = "";
  tooltip.style.insetInlineEnd = "";
  tooltip.style.top = "";
  tooltip.style.bottom = "";
  // Width is set per kind below. Do NOT widen it to the full viewport here — that
  // would override the component's CSS max-width and let the tooltip grow to its
  // max-content width, running off the right edge on medium and small screens.
  tooltip.style.maxWidth = "";

  const position = chooseTooltipPosition(anchor);
  setPositionClass(tooltip, position);
  if (position === "mobile-bottom") {
    // The bottom bar spans the viewport (minus margins); width comes from the two
    // insets, and the bar legitimately fills the width.
    tooltip.style.maxWidth = `${Math.max(0, bounds.width - margin * 2)}px`;
    tooltip.style.insetInlineStart = `${bounds.left + margin}px`;
    tooltip.style.insetInlineEnd = `${Math.max(0, window.innerWidth - bounds.right + margin)}px`;
    tooltip.style.bottom = `${Math.max(0, window.innerHeight - bounds.bottom + margin)}px`;
    return;
  }

  const rect = rectRelativeToViewport(anchor.getBoundingClientRect(), viewport);

  if (position === "wide-right") {
    const readingColumn = resolveReadingColumn(anchor);
    const contentRect = readingColumn
      ? rectRelativeToViewport(readingColumn.getBoundingClientRect(), viewport)
      : null;
    // Reserve the margin tooltip's own width so its right edge never crosses the
    // viewport, then cap the width to the room actually left beside the column.
    const maxLeft = Math.max(margin, bounds.width - WIDE_RIGHT_TOOLTIP_MAX_WIDTH_PX - margin);
    const left = Math.min((contentRect?.right || rect.right) + WIDE_RIGHT_TOOLTIP_GAP_PX, maxLeft);
    tooltip.style.maxWidth = `${Math.min(
      WIDE_RIGHT_TOOLTIP_MAX_WIDTH_PX,
      Math.max(0, bounds.width - left - margin),
    )}px`;
    const tooltipRect = tooltip.getBoundingClientRect();
    tooltip.style.insetInlineStart = `${bounds.left + left}px`;
    tooltip.style.top = `${
      bounds.top + Math.max(margin, rect.top + rect.height / 2 - (tooltipRect.height || 160) / 2)
    }px`;
    return;
  }

  // Adjacent popover (bottom-right / top-right): cap to the component's max width
  // (shrinking only when the viewport is narrower than that), then clamp the box
  // fully on-screen so neither edge overflows.
  const componentMaxPx = tooltip.classList.contains("kpress-tooltip-footnote")
    ? FOOTNOTE_TOOLTIP_MAX_WIDTH_PX
    : TOOLTIP_MAX_WIDTH_PX;
  tooltip.style.maxWidth = `${Math.min(componentMaxPx, Math.max(0, bounds.width - margin * 2))}px`;
  const tooltipRect = tooltip.getBoundingClientRect();
  const left = Math.min(
    Math.max(margin, rect.left),
    Math.max(margin, bounds.width - (tooltipRect.width || componentMaxPx) - margin),
  );
  tooltip.style.insetInlineStart = `${bounds.left + left}px`;
  tooltip.style.top =
    position === "top-right"
      ? `${bounds.top + Math.max(margin, rect.top - (tooltipRect.height || 160) - TOOLTIP_GAP_PX)}px`
      : `${bounds.top + Math.max(margin, rect.bottom + TOOLTIP_GAP_PX)}px`;
}

/**
 * @param {DOMRect} anchorRect
 * @param {number} mouseX
 * @param {number} mouseY
 * @param {string} position
 * @returns {boolean}
 */
function isMouseMovingTowardTooltip(anchorRect, mouseX, mouseY, position) {
  if (position === "wide-right" || position === "mobile-bottom") {
    return false;
  }
  const xWithinBridge =
    mouseX >= anchorRect.left - TOOLTIP_MOUSE_TRACK_MARGIN_PX &&
    mouseX <= anchorRect.right + TOOLTIP_MOUSE_TRACK_MARGIN_PX;
  if (position.startsWith("bottom")) {
    return mouseY > anchorRect.bottom && xWithinBridge;
  }
  if (position.startsWith("top")) {
    return mouseY < anchorRect.top && xWithinBridge;
  }
  return false;
}

/**
 * @param {ActiveTooltip} tooltipState
 * @param {MouseEvent | null} event
 * @returns {number}
 */
function tooltipHideDelay(tooltipState, event) {
  if (tooltipState.position === "wide-right") {
    return TOOLTIP_WIDE_RIGHT_HIDE_DELAY_MS;
  }
  if (
    event &&
    isMouseMovingTowardTooltip(
      tooltipState.anchor.getBoundingClientRect(),
      event.clientX,
      event.clientY,
      tooltipState.position,
    )
  ) {
    return TOOLTIP_MOVING_TOWARD_HIDE_DELAY_MS;
  }
  return TOOLTIP_HIDE_DELAY_MS;
}

/**
 * @param {ActiveTooltip} tooltipState
 * @param {MouseEvent | null} event
 */
function scheduleTooltipHide(tooltipState, event = null) {
  clearTooltipHideTimer();
  tooltipHideTimer = window.setTimeout(
    () => {
      tooltipHideTimer = 0;
      if (activeTooltip?.tooltip === tooltipState.tooltip) {
        fadeOutAndRemove(tooltipState.tooltip);
        activeTooltip = null;
      }
    },
    tooltipHideDelay(tooltipState, event),
  );
}

/**
 * @param {HTMLAnchorElement} anchor
 */
function showKpressTooltip(anchor) {
  const href = anchor.getAttribute("href");
  if (!href?.startsWith("#") || href.length <= 1) {
    return;
  }

  const target = document.getElementById(decodeURIComponent(href.slice(1)));
  if (!target) {
    return;
  }

  const content = tooltipContentForAnchor(anchor, target);
  if (!content?.text.trim()) {
    return;
  }

  removeKpressTooltips();

  const tooltip = document.createElement("aside");
  // Create WITHOUT kpress-tooltip-visible; the class is added after a rAF
  // double-pump so the CSS transition from opacity:0 to opacity:1 fires.
  tooltip.className = "kpress-tooltip kpress-no-print";
  tooltip.setAttribute("role", "tooltip");
  if (content.footnoteId) {
    tooltip.classList.add("kpress-tooltip-footnote");
  }
  tooltip.innerHTML = content.html;

  tooltip.querySelector("[data-kpress-footnote-nav]")?.addEventListener("click", (event) => {
    event.stopPropagation();
    removeKpressTooltips();
  });

  // A tooltip is never a dead end. A link inside it (e.g. a section link in a
  // footnote's text) is a real link: native navigation runs (suppression above
  // keeps the wiring off it) and the popover dismisses instead of lingering
  // over the destination. Tapping anywhere else on a section-preview tooltip
  // navigates to the previewed target itself — on touch the anchor's own tap
  // only opens the preview, so the preview must complete the journey.
  tooltip.addEventListener("click", (event) => {
    const link = event.target instanceof Element ? event.target.closest("a") : null;
    if (link) {
      removeKpressTooltips();
      return;
    }
    if (!content.footnoteId) {
      removeKpressTooltips();
      window.location.hash = href;
    }
  });

  document.body.append(tooltip);
  positionTooltip(anchor, tooltip);

  // Apply mobile-bottom specific inline styles (section 3.34).
  const position = tooltip.getAttribute("data-kpress-tooltip-position") || "bottom-right";
  if (position === "mobile-bottom") {
    tooltip.style.padding = "0.75rem 1rem";
    tooltip.style.boxShadow = "0 -4px 12px rgba(0,0,0,0.15)";
  }

  activeTooltip = {
    anchor,
    tooltip,
    position,
  };
  tooltip.addEventListener("mouseenter", clearTooltipHideTimer);
  tooltip.addEventListener("mouseleave", () => {
    if (activeTooltip?.tooltip === tooltip) {
      scheduleTooltipHide(activeTooltip);
    }
  });

  // Double requestAnimationFrame pump: the first rAF fires after the browser
  // has committed the "hidden" layout; the second fires in the next frame, at
  // which point adding the visible class triggers the CSS transition.
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      tooltip.classList.add("kpress-tooltip-visible");
    });
  });
}

// Tooltips are suppressed inside the table of contents (the TOC already shows
// each heading's text, so a preview just repeats it and is distracting), inside
// site chrome (the document header and any host header/footer), inside an open
// tooltip itself (a link tapped in a footnote popover must NAVIGATE — stacking
// a second preview over the first traps the reader, most visibly on touch,
// where the wiring's preventDefault would swallow the tap), and on anything
// an author opts out with `data-kpress-no-tooltip` (on the link or any
// ancestor). Everything else in the document keeps tooltips — those point at
// content the reader can't already see.
const TOOLTIP_SUPPRESS_SELECTOR =
  ".kpress-toc, .kpress-doc-header, .kpress-site-header, .kpress-site-footer, .kpress-tooltip, [data-kpress-no-tooltip]";

/**
 * @param {Element} anchor
 * @returns {boolean}
 */
function isTooltipSuppressed(anchor) {
  return Boolean(anchor.closest(TOOLTIP_SUPPRESS_SELECTOR));
}

/**
 * @param {Element} anchor
 * @returns {anchor is HTMLAnchorElement}
 */
function isHashAnchor(anchor) {
  return (
    anchor instanceof HTMLAnchorElement &&
    Boolean(anchor.getAttribute("href")?.startsWith("#")) &&
    !isTooltipSuppressed(anchor)
  );
}

/**
 * Wire one hash anchor for tooltip behavior. Idempotent: an anchor is wired at
 * most once, so re-running init or the MutationObserver re-seeing an anchor is
 * a no-op.
 *
 * @param {Element} anchor
 */
function wireTooltipAnchor(anchor) {
  if (!isHashAnchor(anchor)) {
    return;
  }
  const href = anchor.getAttribute("href") || "";
  if (href === "#") {
    return;
  }
  const bound = /** @type {{ __kpressTooltipBound?: boolean }} */ (anchor);
  if (bound.__kpressTooltipBound) {
    return;
  }
  bound.__kpressTooltipBound = true;
  const isFootnote = href.startsWith("#fn-") || Boolean(anchor.closest(".kpress-footnote-ref"));
  if (isFootnote) {
    anchor.addEventListener("click", (event) => {
      event.preventDefault();
    });
    anchor.addEventListener("touchend", (event) => {
      event.preventDefault();
    });
  }
  anchor.addEventListener("mouseenter", () => {
    clearTooltipShowTimer();
    const showDelay = settingsForKind(isFootnote ? "footnote" : "link").showDelayMs;
    tooltipShowTimer = window.setTimeout(
      () => {
        tooltipShowTimer = 0;
        showKpressTooltip(anchor);
      },
      typeof showDelay === "number" ? showDelay : TOOLTIP_SHOW_DELAY_MS,
    );
  });
  anchor.addEventListener("focus", () => showKpressTooltip(anchor));
  anchor.addEventListener(
    "touchstart",
    (event) => {
      event.preventDefault();
      showKpressTooltip(anchor);
    },
    { passive: false },
  );
  anchor.addEventListener("mouseleave", (event) => {
    clearTooltipShowTimer();
    if (activeTooltip?.anchor === anchor) {
      scheduleTooltipHide(activeTooltip, event);
    }
  });
  anchor.addEventListener("blur", removeKpressTooltips);
}

/**
 * @param {Element} anchor
 * @returns {boolean}
 */
function isFootnoteAnchor(anchor) {
  const href = anchor.getAttribute("href") || "";
  return href.startsWith("#fn-") || Boolean(anchor.closest(".kpress-footnote-ref"));
}

/**
 * Anchor kinds with built-in wiring currently active. The shared
 * MutationObserver (started by the first active bind) auto-wires only these
 * kinds; a bind's disposer removes its kinds again, so after an override the
 * built-in leaves late anchors of that kind entirely to the host's binding.
 *
 * @type {Set<string>}
 */
const activeTooltipKinds = new Set();

/** @type {MutationObserver | null} */
let anchorObserver = null;

let tooltipGlobalsBound = false;

/**
 * @param {Element} anchor
 */
function wireObservedAnchor(anchor) {
  const kind = isFootnoteAnchor(anchor) ? "footnote" : "link";
  if (activeTooltipKinds.has(kind)) {
    wireTooltipAnchor(anchor);
  }
}

/**
 * Start the shared late-anchor observer (embedding host apps inject the
 * document fragment after load, so anchors appear later). Started lazily by
 * the first active kind; disconnected again when no kind is active.
 */
function ensureAnchorObserver() {
  if (
    anchorObserver ||
    typeof MutationObserver === "undefined" ||
    typeof document === "undefined" ||
    !document.body
  ) {
    return;
  }
  anchorObserver = new MutationObserver((records) => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (!(node instanceof Element)) {
          continue;
        }
        if (node.matches('a[href^="#"]')) {
          wireObservedAnchor(node);
        }
        for (const nested of node.querySelectorAll('a[href^="#"]')) {
          wireObservedAnchor(nested);
        }
      }
    }
  });
  anchorObserver.observe(document.body, { childList: true, subtree: true });
}

/**
 * Deactivate built-in auto-wiring for the given kinds (already-wired anchors
 * keep their listeners; late anchors of these kinds are left to whatever
 * binding replaced the built-in).
 *
 * @param {string[]} kinds
 */
function releaseTooltipKinds(kinds) {
  for (const kind of kinds) {
    activeTooltipKinds.delete(kind);
  }
  if (activeTooltipKinds.size === 0 && anchorObserver) {
    anchorObserver.disconnect();
    anchorObserver = null;
  }
}

/**
 * Wire every hash anchor under `root` for tooltips and register the global
 * dismiss handlers once. Anchor wiring is idempotent, so a host that re-mounts
 * a document can call this repeatedly without leaking listeners.
 *
 * @param {ParentNode} [root]
 * @returns {() => void} disposer that deactivates late-anchor wiring for the
 *   kinds this call activated
 */
export function initKpressTooltips(
  root = document,
  config = /** @type {Record<string, unknown>} */ ({}),
) {
  if (!tooltipGlobalsBound) {
    tooltipGlobalsBound = true;
    dismissOnEscape(removeKpressTooltips);
    dismissOnResize(removeKpressTooltips);
  }
  const only = typeof config.only === "string" ? config.only : null;
  const kinds = only ? [only] : ["link", "footnote"];
  /** @type {{ placement?: string; showDelayMs?: number }} */
  const settings = {};
  if (typeof config.placement === "string") {
    settings.placement = config.placement;
  }
  if (typeof config.showDelayMs === "number") {
    settings.showDelayMs = config.showDelayMs;
  }
  for (const kind of kinds) {
    activeTooltipKinds.add(kind);
    kindSettings.set(kind, { ...kindSettings.get(kind), ...settings });
  }
  ensureAnchorObserver();
  for (const anchor of root.querySelectorAll('a[href^="#"]')) {
    const kind = isFootnoteAnchor(anchor) ? "footnote" : "link";
    if (only && kind !== only) {
      continue;
    }
    wireTooltipAnchor(anchor);
  }
  return () => releaseTooltipKinds(kinds);
}

// Two registered behaviors over disjoint anchor kinds: hover previews for
// internal links, and footnote previews. Overriding one id leaves the other's
// markup handling untouched (see kpress-design.md, behaviors); each bind
// returns a disposer, so an override (pre- or post-ready) detaches built-in
// handling for that kind's late anchors too.
behaviors.register("tooltip", {
  bind: (root, config) => initKpressTooltips(root, { ...config, only: "link" }),
});
behaviors.register("footnote-preview", {
  bind: (root, config) => initKpressTooltips(root, { ...config, only: "footnote" }),
});
