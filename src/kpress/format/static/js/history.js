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
 * leave the reader where they were. This behavior records the pane offset
 * in the session-history entry state and replays it on traversal.
 *
 * It also owns plain in-document section navigation: Chromium performs
 * fragment navigation with an instant scroll when the scroller is a
 * non-root pane (the pane's CSS `scroll-behavior: smooth` is not
 * consulted), so native hash clicks jump while explicit UI scrolls (the
 * TOC title) glide. Plain section links are therefore handled here — push
 * the entry, then glide to the target — while footnote references keep
 * their popover owner, and modified/prevented clicks and anchors that
 * request non-default anchor semantics (`download`, a non-`_self`
 * `target`) stay native.
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

  /**
   * The single eligibility predicate for owned section navigation: a plain,
   * unclaimed, unmodified primary-button click on a same-document fragment
   * link that keeps default anchor semantics (no `download`, no non-`_self`
   * browsing target) and resolves to a target inside the pane. Footnote
   * references keep their popover owner. Everything that fails the
   * predicate stays fully native.
   *
   * @param {MouseEvent} event
   * @returns {{ href: string, dest: HTMLElement } | null}
   */
  const ownedSectionTarget = (event) => {
    if (event.defaultPrevented || event.button !== 0) {
      return null;
    }
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return null;
    }
    const target = /** @type {{ closest?: (selector: string) => Element | null }} */ (event.target);
    const anchor = typeof target?.closest === "function" ? target.closest('a[href^="#"]') : null;
    const href = anchor?.getAttribute("href") ?? "";
    if (!anchor || href.length <= 1) {
      return null;
    }
    if (anchor.hasAttribute("download")) {
      return null;
    }
    const browsingTarget = anchor.getAttribute("target");
    if (browsingTarget && browsingTarget.toLowerCase() !== "_self") {
      return null;
    }
    if (href.startsWith("#fn-") || anchor.closest(".kpress-footnote-ref, .footnote-ref")) {
      return null;
    }
    // fragmentId's guarded decoding: a malformed fragment (e.g. "#%") falls
    // back to the raw id instead of throwing out of the listener.
    const dest = document.getElementById(fragmentId(href));
    if (!dest || !viewport.contains(dest)) {
      return null;
    }
    return { href, dest };
  };

  /**
   * Native fragment navigation moves the sequential focus-navigation
   * starting point to the target; reproduce that when owning the click so
   * keyboard activation continues from the destination. A target that is
   * not natively focusable gets a temporary `tabindex="-1"` that is
   * dropped again on blur; an authored tabindex is left untouched.
   *
   * @param {HTMLElement} dest
   */
  const focusDestination = (dest) => {
    if (!dest.hasAttribute("tabindex")) {
      dest.setAttribute("tabindex", "-1");
      dest.addEventListener("blur", () => dest.removeAttribute("tabindex"), { once: true });
    }
    try {
      dest.focus({ preventScroll: true });
    } catch {
      // A host element that refuses focus still gets the scroll.
    }
  };

  /**
   * Glide plain section links inside the pane. Listens on `window` — the
   * end of the bubble path — so every document-level owner that claims the
   * click first (the footnote popover, a host's own interceptor) has
   * already spoken, and `defaultPrevented` defers to all of them
   * regardless of registration order. pushState writes the entry the
   * browser would have pushed; the new entry starts unstamped and picks up
   * its offset from the debounced scroll stamp, so traversal behaves
   * exactly as with native navigation. Re-activating the current fragment
   * matches native history too: the browser pushes no entry when the
   * destination URL is already current, so neither does this path — it
   * only performs the scroll.
   *
   * @param {MouseEvent} event
   */
  const onNavClick = (event) => {
    const owned = ownedSectionTarget(event);
    if (!owned) {
      return;
    }
    if (new URL(owned.href, location.href).href !== location.href) {
      try {
        history.pushState(null, "", owned.href);
      } catch {
        // Embedders that reject pushState keep fully native navigation.
        return;
      }
    }
    event.preventDefault();
    focusDestination(owned.dest);
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    owned.dest.scrollIntoView({ behavior: reduceMotion ? "instant" : "smooth", block: "start" });
  };

  let stampTimer = 0;
  const onScroll = () => {
    clearTimeout(stampTimer);
    stampTimer = window.setTimeout(() => stampScroll(ctx), HISTORY_STAMP_DEBOUNCE_MS);
  };

  document.addEventListener("click", onClick, true);
  window.addEventListener("click", onNavClick);
  window.addEventListener("popstate", onPopState);
  ctx.onScroll(onScroll);

  return () => {
    document.removeEventListener("click", onClick, true);
    window.removeEventListener("click", onNavClick);
    window.removeEventListener("popstate", onPopState);
    ctx.offScroll(onScroll);
    clearTimeout(stampTimer);
  };
}

behaviors.register("history", {
  bind: (root, config) => initKpressHistory(root, config),
});
