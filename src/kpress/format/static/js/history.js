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
 * A plain record is the only state shape the behavior will write into.
 * Spreading a Date, Map, Set, array, or class instance would change its type
 * and discard its data, so anything else is left exactly as the host stored it.
 *
 * @param {unknown} value
 * @returns {value is Record<string, unknown>}
 */
function isPlainRecord(value) {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

/**
 * Compute the stamped state for the current entry, or `null` when the entry's
 * state must not be touched: a non-plain host value, or a plain record whose
 * `kpressScroll` key the host owns (non-numeric). Traversal then relies on the
 * fragment-target fallback.
 *
 * @param {unknown} state
 * @param {number} scrollTop
 * @returns {Record<string, unknown> | null}
 */
function stampedState(state, scrollTop) {
  if (state === null || state === undefined) {
    return { [HISTORY_SCROLL_STATE_KEY]: scrollTop };
  }
  if (
    isPlainRecord(state) &&
    (!(HISTORY_SCROLL_STATE_KEY in state) || typeof state[HISTORY_SCROLL_STATE_KEY] === "number")
  ) {
    return { ...state, [HISTORY_SCROLL_STATE_KEY]: scrollTop };
  }
  return null;
}

/**
 * @param {{ scrollTop(): number }} ctx viewport scroll context
 */
function stampScroll(ctx) {
  const next = stampedState(history.state, ctx.scrollTop());
  if (next === null) {
    return;
  }
  try {
    history.replaceState(next, "");
  } catch {
    // Some embedders (sandboxed frames, exotic URL schemes) reject
    // replaceState; the behavior then degrades to the fragment-target
    // fallback on traversal.
  }
}

/**
 * Decode a location fragment without throwing: a malformed percent-encoding
 * (e.g. `#%`) falls back to the raw fragment text.
 *
 * @param {string} hash
 * @returns {string}
 */
function fragmentId(hash) {
  if (hash.length <= 1) {
    return "";
  }
  const raw = hash.slice(1);
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
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
    // Bare "#" is included deliberately: the TOC "Contents" link navigates to
    // the empty fragment, and Back from it must return to the stamped offset.
    if (!anchor) {
      return;
    }
    stampScroll(ctx);
  };

  /**
   * @param {PopStateEvent} event
   */
  const onPopState = (event) => {
    const state = event.state;
    const top = isPlainRecord(state) ? state[HISTORY_SCROLL_STATE_KEY] : undefined;
    if (typeof top === "number" && Number.isFinite(top)) {
      restorePaneScroll(viewport, top);
      return;
    }
    // No stamped offset (first forward visit into a hash entry, or an entry
    // predating this behavior): land on the fragment target, matching what
    // the browser does for a document-scrolled page. A fragmentless (or
    // bare-#) entry gets document-top semantics.
    const id = fragmentId(location.hash);
    if (!id) {
      restorePaneScroll(viewport, 0);
      return;
    }
    document.getElementById(id)?.scrollIntoView({ behavior: "instant", block: "start" });
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
