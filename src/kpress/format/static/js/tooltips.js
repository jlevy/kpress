import {
  dismissOnEscape,
  dismissOnResize,
  OVERLAY_DEFAULT_GAP_PX,
  OVERLAY_VIEWPORT_MARGIN_PX,
} from "./overlay.js";
import { rectRelativeToViewport, resolveKpressViewport, viewportBounds } from "./viewport.js";

const TOOLTIP_VIEWPORT_MARGIN_PX = OVERLAY_VIEWPORT_MARGIN_PX;
const TOOLTIP_GAP_PX = OVERLAY_DEFAULT_GAP_PX;
const TOOLTIP_SHOW_DELAY_MS = 500;
const TOOLTIP_HIDE_DELAY_MS = 2500;
const TOOLTIP_WIDE_RIGHT_HIDE_DELAY_MS = 4000;
const TOOLTIP_MOVING_TOWARD_HIDE_DELAY_MS = 500;
const TOOLTIP_MOUSE_TRACK_MARGIN_PX = 20;
const MOBILE_TOOLTIP_BREAKPOINT_PX = 640;
const WIDE_TOOLTIP_BREAKPOINT_PX = 1200;
const FOOTNOTE_MAX_CHARS = 400;
const INTERNAL_LINK_MAX_CHARS = 1000;

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
 * @param {Element} trigger
 * @returns {string}
 */
function chooseTooltipPosition(trigger) {
  const viewport = resolveKpressViewport(trigger);
  const bounds = viewportBounds(viewport);
  if (bounds.width <= MOBILE_TOOLTIP_BREAKPOINT_PX) {
    return "mobile-bottom";
  }
  if (trigger.closest("table")) {
    return "bottom-right";
  }
  const mainContent = document.getElementById("main-content");
  if (mainContent && bounds.width >= WIDE_TOOLTIP_BREAKPOINT_PX) {
    const contentRect = rectRelativeToViewport(mainContent.getBoundingClientRect(), viewport);
    if (bounds.width - contentRect.right >= 320) {
      return "wide-right";
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
function positionTooltip(anchor, tooltip) {
  const viewport = resolveKpressViewport(anchor);
  const bounds = viewportBounds(viewport);
  tooltip.style.insetInlineStart = "";
  tooltip.style.insetInlineEnd = "";
  tooltip.style.top = "";
  tooltip.style.bottom = "";
  tooltip.style.maxWidth = `${Math.max(0, bounds.width - TOOLTIP_VIEWPORT_MARGIN_PX * 2)}px`;

  const position = chooseTooltipPosition(anchor);
  setPositionClass(tooltip, position);
  if (position === "mobile-bottom") {
    tooltip.style.insetInlineStart = `${bounds.left + TOOLTIP_VIEWPORT_MARGIN_PX}px`;
    tooltip.style.insetInlineEnd = `${Math.max(
      0,
      window.innerWidth - bounds.right + TOOLTIP_VIEWPORT_MARGIN_PX,
    )}px`;
    tooltip.style.bottom = `${Math.max(
      0,
      window.innerHeight - bounds.bottom + TOOLTIP_VIEWPORT_MARGIN_PX,
    )}px`;
    return;
  }

  const rect = rectRelativeToViewport(anchor.getBoundingClientRect(), viewport);
  const tooltipRect = tooltip.getBoundingClientRect();
  if (position === "wide-right") {
    const mainContent = document.getElementById("main-content");
    const contentRect = mainContent
      ? rectRelativeToViewport(mainContent.getBoundingClientRect(), viewport)
      : null;
    const left = (contentRect?.right || rect.right) + 16;
    const clampedLeft = Math.min(left, Math.max(TOOLTIP_VIEWPORT_MARGIN_PX, bounds.width - 336));
    tooltip.style.insetInlineStart = `${bounds.left + clampedLeft}px`;
    tooltip.style.top = `${
      bounds.top +
      Math.max(
        TOOLTIP_VIEWPORT_MARGIN_PX,
        rect.top + rect.height / 2 - (tooltipRect.height || 160) / 2,
      )
    }px`;
    return;
  }

  const left = Math.min(
    Math.max(TOOLTIP_VIEWPORT_MARGIN_PX, rect.left),
    Math.max(
      TOOLTIP_VIEWPORT_MARGIN_PX,
      bounds.width - (tooltipRect.width || 320) - TOOLTIP_VIEWPORT_MARGIN_PX,
    ),
  );
  tooltip.style.insetInlineStart = `${bounds.left + left}px`;
  tooltip.style.top =
    position === "top-right"
      ? `${
          bounds.top +
          Math.max(
            TOOLTIP_VIEWPORT_MARGIN_PX,
            rect.top - (tooltipRect.height || 160) - TOOLTIP_GAP_PX,
          )
        }px`
      : `${bounds.top + Math.max(TOOLTIP_VIEWPORT_MARGIN_PX, rect.bottom + TOOLTIP_GAP_PX)}px`;
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

/**
 * @param {Element} anchor
 * @returns {anchor is HTMLAnchorElement}
 */
function isHashAnchor(anchor) {
  return (
    anchor instanceof HTMLAnchorElement &&
    Boolean(anchor.getAttribute("href")?.startsWith("#")) &&
    // Skip table-of-contents links: the TOC already shows each heading's text,
    // so a hover tooltip there just repeats it. Internal-link tooltips elsewhere
    // in the document stay — those point at content the reader can't already see.
    !anchor.closest(".kpress-toc")
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
    tooltipShowTimer = window.setTimeout(() => {
      tooltipShowTimer = 0;
      showKpressTooltip(anchor);
    }, TOOLTIP_SHOW_DELAY_MS);
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

let tooltipGlobalsBound = false;

/**
 * Wire every hash anchor under `root` for tooltips and register the global
 * dismiss handlers once. Anchor wiring is idempotent, so a host that re-mounts
 * a document can call this repeatedly without leaking listeners.
 *
 * @param {ParentNode} [root]
 */
export function initKpressTooltips(root = document) {
  if (!tooltipGlobalsBound) {
    tooltipGlobalsBound = true;
    dismissOnEscape(removeKpressTooltips);
    dismissOnResize(removeKpressTooltips);
  }
  for (const anchor of root.querySelectorAll('a[href^="#"]')) {
    wireTooltipAnchor(anchor);
  }
}

initKpressTooltips();

// Embedding host apps inject the document fragment after this
// module loads, so footnote and internal-link anchors appear later. A
// MutationObserver wires them as they arrive (wiring is idempotent).
if (typeof MutationObserver !== "undefined" && typeof document !== "undefined" && document.body) {
  const observer = new MutationObserver((records) => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (!(node instanceof Element)) {
          continue;
        }
        if (node.matches('a[href^="#"]')) {
          wireTooltipAnchor(node);
        }
        for (const nested of node.querySelectorAll('a[href^="#"]')) {
          wireTooltipAnchor(nested);
        }
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}
