/**
 * Shared KPress viewport helpers.
 *
 * A KPress document scrolls inside exactly one viewport element. The standalone
 * shell marks the page scroller with `[data-kpress-viewport]`; embedding hosts
 * mark their pane the same way. Floating UI and scroll locks should use that
 * element instead of assuming the browser window is the document boundary.
 */

const VIEWPORT_SELECTOR = "[data-kpress-viewport]";
let warnedMissingViewport = false;

/**
 * Realm-safe node kind checks: an embedding host may hand over a node from
 * another frame (or a DOM emulation), whose classes are not this realm's
 * `Element`/`Document`, so `instanceof` is the wrong test.
 *
 * @param {unknown} node
 * @returns {node is Element}
 */
function isElementNode(node) {
  return Boolean(node) && /** @type {Node} */ (node).nodeType === 1;
}

/**
 * @param {unknown} node
 * @returns {node is Document}
 */
function isDocumentNode(node) {
  return Boolean(node) && /** @type {Node} */ (node).nodeType === 9;
}

/**
 * @typedef {{ top: number; bottom: number; left: number; right: number; width: number; height: number }} ViewportRect
 * @typedef {object} ViewportScrollContext
 * @property {HTMLElement} el
 * @property {() => number} scrollTop
 * @property {(smooth: boolean) => void} scrollToTop
 * @property {(fn: EventListener) => void} onScroll
 * @property {(fn: EventListener) => void} offScroll
 * @property {() => void} lock
 * @property {() => void} unlock
 * @property {() => Element | null} observerRoot
 */

/**
 * @param {Document | Element | null | undefined} [node]
 * @returns {HTMLElement}
 */
export function resolveKpressViewport(node = document) {
  if (isElementNode(node)) {
    const marked = node.matches(VIEWPORT_SELECTOR) ? node : node.closest(VIEWPORT_SELECTOR);
    if (isElementNode(marked)) {
      return /** @type {HTMLElement} */ (marked);
    }
  }

  if (isDocumentNode(node)) {
    const marked = node.querySelector(VIEWPORT_SELECTOR);
    if (isElementNode(marked)) {
      return /** @type {HTMLElement} */ (marked);
    }
  }

  if (!warnedMissingViewport && typeof console !== "undefined") {
    warnedMissingViewport = true;
    console.warn(
      `KPress host-integration warning: no ${VIEWPORT_SELECTOR} ancestor found; using document scroller.`,
    );
  }

  return /** @type {HTMLElement} */ (document.scrollingElement || document.documentElement);
}

/**
 * @param {HTMLElement} viewport
 * @returns {boolean}
 */
export function isDocumentViewport(viewport) {
  return (
    viewport === document.scrollingElement ||
    viewport === document.documentElement ||
    viewport === document.body
  );
}

/**
 * The element that owns viewport-scoped UI state classes/data attributes.
 * Document pages keep legacy body classes; embedded panes keep state local.
 *
 * @param {HTMLElement} viewport
 * @returns {HTMLElement}
 */
export function viewportStateElement(viewport) {
  return isDocumentViewport(viewport) ? document.body : viewport;
}

/**
 * @param {HTMLElement} viewport
 * @returns {ViewportRect}
 */
export function viewportBounds(viewport) {
  if (isDocumentViewport(viewport)) {
    const width = window.innerWidth;
    const height = window.innerHeight;
    return { top: 0, bottom: height, left: 0, right: width, width, height };
  }
  const rect = viewport.getBoundingClientRect();
  return {
    top: rect.top,
    bottom: rect.bottom,
    left: rect.left,
    right: rect.right,
    width: rect.width,
    height: rect.height,
  };
}

/**
 * @param {DOMRect | ViewportRect} rect
 * @param {HTMLElement} viewport
 * @returns {ViewportRect}
 */
export function rectRelativeToViewport(rect, viewport) {
  const bounds = viewportBounds(viewport);
  return {
    top: rect.top - bounds.top,
    bottom: rect.bottom - bounds.top,
    left: rect.left - bounds.left,
    right: rect.right - bounds.left,
    width: rect.width,
    height: rect.height,
  };
}

/**
 * @param {HTMLElement} viewport
 * @param {() => void} callback
 * @returns {() => void}
 */
export function addViewportResizeListener(viewport, callback) {
  window.addEventListener("resize", callback);
  /** @type {ResizeObserver | null} */
  let observer = null;
  if (!isDocumentViewport(viewport) && typeof ResizeObserver !== "undefined") {
    observer = new ResizeObserver(() => callback());
    observer.observe(viewport);
  }
  return () => {
    window.removeEventListener("resize", callback);
    observer?.disconnect();
  };
}

/**
 * @param {HTMLElement} viewport
 * @returns {ViewportScrollContext}
 */
export function viewportScrollContext(viewport) {
  const isDocumentScroller = isDocumentViewport(viewport);
  const scrollTarget = isDocumentScroller ? window : viewport;
  return {
    el: viewport,
    scrollTop: () =>
      isDocumentScroller ? window.pageYOffset || viewport.scrollTop || 0 : viewport.scrollTop,
    scrollToTop: (smooth) => {
      if (isDocumentScroller) {
        window.scrollTo({ top: 0, behavior: smooth ? "smooth" : "auto" });
      } else {
        viewport.scrollTo({ top: 0, behavior: smooth ? "smooth" : "auto" });
      }
    },
    onScroll: (fn) => scrollTarget.addEventListener("scroll", fn, { passive: true }),
    offScroll: (fn) => scrollTarget.removeEventListener("scroll", fn),
    lock: () => {
      viewport.style.overflow = "hidden";
    },
    unlock: () => {
      viewport.style.overflow = "";
    },
    observerRoot: () => (isDocumentScroller ? null : viewport),
  };
}
