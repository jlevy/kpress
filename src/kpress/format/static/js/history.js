import { behaviors } from "./runtime.js";
import { resolveKpressViewport, viewportScrollContext } from "./viewport.js";

/**
 * History behavior: viewport-aware scroll restoration for in-document hash
 * navigation.
 *
 * A KPress document scrolls inside the `[data-kpress-viewport]` pane, and
 * browsers persist/restore only the *document* scroller's position across
 * same-document history traversal — the pane is invisible to native scroll
 * restoration, so Back after a section-link jump would revert the URL but
 * leave the reader where they were. This behavior closes that gap without
 * taking over navigation: hash clicks stay native (the browser writes the
 * hash and pushes the entry); the behavior only records the pane offset in
 * the session-history entry state and replays it on traversal.
 */

/**
 * Key under which the pane scroll offset is stamped into `history.state`.
 * Namespaced so host state on the same entry survives untouched.
 */
export const HISTORY_SCROLL_STATE_KEY = "kpressScroll";

/**
 * Trailing debounce for the scroll-driven re-stamp. Keeps the current entry's
 * offset fresh (so Forward restores too) without hammering `replaceState`,
 * which some browsers rate-limit.
 */
export const HISTORY_STAMP_DEBOUNCE_MS = 200;

/**
 * @param {unknown} state
 * @param {number} scrollTop
 * @returns {Record<string, unknown>}
 */
function stampedState(state, scrollTop) {
  const base = typeof state === "object" && state !== null ? state : {};
  return { ...base, [HISTORY_SCROLL_STATE_KEY]: scrollTop };
}

/**
 * @param {{ scrollTop(): number }} ctx viewport scroll context
 */
function stampScroll(ctx) {
  try {
    history.replaceState(stampedState(history.state, ctx.scrollTop()), "");
  } catch {
    // Some embedders (sandboxed frames, exotic URL schemes) reject
    // replaceState; the behavior then degrades to the fragment-target
    // fallback on traversal.
  }
}

/**
 * @param {HTMLElement} viewport
 * @param {number} top
 */
function restorePaneScroll(viewport, top) {
  // Restoration mimics the browser's own instant restore; an explicit
  // "instant" bypasses the pane's CSS `scroll-behavior: smooth`.
  if (typeof viewport.scrollTo === "function") {
    viewport.scrollTo({ top, behavior: "instant" });
  } else {
    viewport.scrollTop = top;
  }
}

/**
 * Wire history-aware scroll restoration for the viewport that owns `root`.
 * Returns a disposer that removes all listeners — an embedding host that
 * swaps the document per view calls it on unmount; the standalone page
 * ignores it.
 *
 * @param {Document | Element} [root]
 * @returns {() => void}
 */
export function initKpressHistory(root = document, _config = /** @type {unknown} */ ({})) {
  const viewport = resolveKpressViewport(root);
  const ctx = viewportScrollContext(viewport);

  /**
   * Record where the reader is leaving from, just before the browser's own
   * hash navigation pushes the next entry. Capture phase, so the stamp lands
   * even when another handler (e.g. the footnote popover) later prevents the
   * navigation — re-stamping the current offset on the current entry is
   * harmless.
   *
   * @param {Event} event
   */
  const onClick = (event) => {
    const target = /** @type {{ closest?: (selector: string) => Element | null }} */ (event.target);
    const anchor = typeof target?.closest === "function" ? target.closest('a[href^="#"]') : null;
    if (!anchor || (anchor.getAttribute("href")?.length ?? 0) <= 1) {
      return;
    }
    stampScroll(ctx);
  };

  /**
   * @param {PopStateEvent} event
   */
  const onPopState = (event) => {
    const state = /** @type {Record<string, unknown> | null} */ (event.state);
    const top = state ? state[HISTORY_SCROLL_STATE_KEY] : undefined;
    if (typeof top === "number") {
      restorePaneScroll(viewport, top);
      return;
    }
    // No stamped offset (first forward visit into a hash entry, or an entry
    // predating this behavior): land on the fragment target, matching what
    // the browser does for a document-scrolled page.
    const hash = location.hash;
    const id = hash.length > 1 ? decodeURIComponent(hash.slice(1)) : "";
    const target = id ? document.getElementById(id) : null;
    target?.scrollIntoView({ behavior: "instant", block: "start" });
  };

  let stampTimer = 0;
  const onScroll = () => {
    clearTimeout(stampTimer);
    stampTimer = window.setTimeout(() => stampScroll(ctx), HISTORY_STAMP_DEBOUNCE_MS);
  };

  document.addEventListener("click", onClick, true);
  window.addEventListener("popstate", onPopState);
  ctx.onScroll(onScroll);

  return () => {
    document.removeEventListener("click", onClick, true);
    window.removeEventListener("popstate", onPopState);
    ctx.offScroll(onScroll);
    clearTimeout(stampTimer);
  };
}

behaviors.register("history", {
  bind: (root, config) => initKpressHistory(root, config),
});
