import { toggleBackdrop } from "./overlay.js";
import { behaviors } from "./runtime.js";
import { resolveKpressViewport, viewportScrollContext } from "./viewport.js";

/**
 * Scroll distance after which the narrow-mode floating toggle appears.
 * Exported as a part (see kpress-design.md "Component Authoring Contract"):
 * hosts wrap or replace the visibility policy rather than asking for a flag.
 */
export const TOC_TOGGLE_SCROLL_THRESHOLD_PX = 100;

/**
 * Within this distance of the viewport's scroll top, the document counts as
 * "at the top" and the first TOC entry is highlighted unconditionally — the
 * scroll-spy band can't see a first heading that sits above it.
 */
export const TOC_AT_TOP_EPSILON_PX = 8;

/**
 * How long the active entry must stay inside one top-level group before the
 * collapsible TOC hands the expanded group off to it. Rapid scrolling (or the
 * smooth glide after a TOC click) sweeps the scroll-spy across intermediate
 * sections; deferring the handoff until the position settles keeps the TOC
 * from churning open and closed mid-sweep.
 */
const TOC_SCROLL_FOLLOW_SETTLE_MS = 250;

/**
 * Default toggle-visibility policy: reveal the floating button once the reader
 * has scrolled past the threshold. Replaceable per page via
 * `kpress.behaviors.configure("toc", { visible: (ctx) => ... })` (e.g.
 * `() => true` for an always-visible toggle), or wrappable by importing this
 * default and delegating to it.
 *
 * @param {{ scrollTop(): number }} ctx viewport scroll context
 * @returns {boolean}
 */
export function defaultTocToggleVisible(ctx) {
  return ctx.scrollTop() > TOC_TOGGLE_SCROLL_THRESHOLD_PX;
}

/**
 * @param {Element} link
 * @returns {string | null}
 */
function tocLinkId(link) {
  const href = link.getAttribute("href");
  if (!href?.startsWith("#") || href.length <= 1) {
    return null;
  }
  return decodeURIComponent(href.slice(1));
}

/**
 * @param {Element} toc
 * @returns {Element[]}
 */
function tocContentLinks(toc) {
  return Array.from(toc.querySelectorAll('ol a[href^="#"]'));
}

/**
 * Wire one TOC. Idempotent per `[data-kpress-toc]` element.
 *
 * @param {Element} toc
 * @returns {() => void} disposer that removes all listeners/observers
 */
function wireToc(toc, config = /** @type {Record<string, unknown>} */ ({})) {
  // Already wired: return the existing disposer so a host that re-runs
  // initKpressToc() (e.g. after the module's own load-time self-init wired this
  // node) still gets a handle it can tear down, rather than a no-op.
  const bound = /** @type {{ __kpressTocDispose?: () => void }} */ (toc);
  if (typeof bound.__kpressTocDispose === "function") {
    return bound.__kpressTocDispose;
  }
  toc.classList.add("kpress-toc");

  // The toggle and backdrop are siblings of the <nav> (so the narrow drawer can
  // hide/animate as a unit without swallowing the toggle). Find them in the
  // shared layout scope.
  const scope = toc.closest(".kpress-content-with-toc") || toc.parentElement || toc;
  const button = scope.querySelector("[data-kpress-toc-toggle], .kpress-toc-toggle");
  const backdrop = scope.querySelector("[data-kpress-toc-backdrop], .kpress-toc-backdrop");
  const list = toc.querySelector("ol");
  if (!button || !list) {
    return () => {};
  }

  const ctx = viewportScrollContext(resolveKpressViewport(toc));
  const links = tocContentLinks(toc);

  // Collapsible TOC settings: the server stamps them on the nav only when the
  // document has entries deeper than the threshold; JS-channel config
  // (`collapseDepth`/`expandOnScroll`) overrides the attributes, like the
  // toggle's `icon`/`visible`. A config `collapseDepth` of 0 disables collapse.
  const collapseDepthSetting =
    typeof config.collapseDepth === "number"
      ? config.collapseDepth
      : Number.parseInt(toc.getAttribute("data-kpress-toc-collapse-depth") ?? "", 10);
  const collapseDepth =
    Number.isInteger(collapseDepthSetting) && collapseDepthSetting >= 1
      ? collapseDepthSetting
      : null;
  const expandOnScroll =
    typeof config.expandOnScroll === "boolean"
      ? config.expandOnScroll
      : toc.getAttribute("data-kpress-toc-expand-on-scroll") !== "false";

  // Config-tunable aspects (JS-channel config may carry callbacks): a custom
  // toggle icon and the toggle-visibility policy.
  if (typeof config.icon === "string") {
    button.innerHTML = config.icon;
  }
  const visiblePolicy =
    typeof config.visible === "function"
      ? /** @type {(ctx: { scrollTop(): number }) => boolean} */ (config.visible)
      : defaultTocToggleVisible;

  /** @type {Array<() => void>} */
  const cleanups = [];
  /**
   * @param {EventTarget} el
   * @param {string} ev
   * @param {EventListener} fn
   * @param {AddEventListenerOptions} [opts]
   */
  const on = (el, ev, fn, opts) => {
    el.addEventListener(ev, fn, opts);
    cleanups.push(() => el.removeEventListener(ev, fn, opts));
  };

  const updateToggleVisibility = () => {
    // In narrow mode the floating toggle is the *only* way to reach the TOC (the
    // sidebar is hidden by the container query); the policy decides when it
    // shows (default: after scrolling past the threshold, matching the
    // TextPress hover-in behavior). Wide mode hides the toggle entirely via
    // CSS, so toggling this class has no visible effect there.
    button.classList.toggle("show-toggle", visiblePolicy(ctx));
  };

  /**
   * @param {boolean} expanded
   */
  const setExpanded = (expanded) => {
    if (expanded) {
      ctx.lock();
    } else {
      ctx.unlock();
    }
    button.setAttribute("aria-expanded", String(expanded));
    // Drawer visibility is driven entirely by the `kpress-mobile-visible` class
    // + CSS (narrow mode) or the always-visible sidebar (wide mode). Do NOT set
    // `list.hidden` here: in the wide sidebar there is no toggle to reopen it, so
    // collapsing the list (e.g. on a TOC link click) would `display:none` the
    // entries permanently.
    toc.classList.toggle("kpress-mobile-visible", expanded);
    toggleBackdrop(backdrop, expanded);
    updateToggleVisibility();
  };

  on(button, "click", () => {
    setExpanded(button.getAttribute("aria-expanded") !== "true");
  });

  if (backdrop) {
    on(backdrop, "click", () => setExpanded(false));
    on(backdrop, "touchmove", (event) => event.preventDefault(), { passive: false });
  }

  let touchStartY = 0;
  on(
    toc,
    "touchstart",
    (event) => {
      const touchEvent = /** @type {TouchEvent} */ (event);
      touchStartY = touchEvent.touches[0]?.clientY ?? 0;
    },
    { passive: true },
  );
  on(
    toc,
    "touchmove",
    (event) => {
      const touchEvent = /** @type {TouchEvent} */ (event);
      event.stopPropagation();
      const touchY = touchEvent.touches[0]?.clientY ?? touchStartY;
      const maxScrollTop = toc.scrollHeight - toc.clientHeight;
      const scrollingUp = touchY > touchStartY;
      const scrollingDown = touchY < touchStartY;
      if ((scrollingUp && toc.scrollTop <= 0) || (scrollingDown && toc.scrollTop >= maxScrollTop)) {
        event.preventDefault();
      }
    },
    { passive: false },
  );

  on(document, "click", (event) => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    if (!expanded || !(event.target instanceof Node)) {
      return;
    }
    if (!toc.contains(event.target) && !button.contains(event.target)) {
      setExpanded(false);
    }
  });

  const titleTop = toc.querySelector("[data-kpress-toc-top]");
  if (titleTop) {
    // Native bare-"#" navigation owns the URL (clearing any section hash) and
    // the history entry, so the pre-click position stays reachable via Back.
    // The browser only scrolls the *document* for an empty fragment, so the
    // pane's own top scroll stays here.
    on(titleTop, "click", () => {
      setExpanded(false);
      ctx.scrollToTop(true);
    });
  }

  // Depth collapse: partition the flat <li> list into spine groups — each
  // entry at or above the threshold owns the deeper siblings that follow it up
  // to the next spine entry. Entries before the first spine entry (possible
  // after depth normalization) form a head group that stays visible. A row
  // deeper than the threshold is visible iff allExpanded (the button state) or
  // scroll-follow marks its group active; visibility is recomputed from that
  // one predicate on every state change, so the button and scroll-follow can
  // never fight.
  /** @type {(link: Element | undefined) => void} */
  let followActiveGroup = () => {};
  if (collapseDepth !== null) {
    /** @type {(item: Element) => number} */
    const entryLevel = (item) => {
      const match = /(?:^|\s)kpress-toc-level-(\d+)(?:\s|$)/.exec(item.className);
      return match ? Number.parseInt(match[1], 10) : 1;
    };
    /** @type {{ item: Element, deep: boolean, group: Element | null }[]} */
    const rows = [];
    /** @type {Map<Element, Element | null>} */
    const groupOfLink = new Map();
    /** @type {Element | null} */
    let currentGroup = null;
    for (const item of list.querySelectorAll(":scope > li")) {
      const link = item.querySelector("a");
      const deep = entryLevel(item) > collapseDepth;
      if (!deep && link) {
        currentGroup = link;
      }
      const group = deep ? currentGroup : link;
      rows.push({ item, deep, group });
      if (link) {
        groupOfLink.set(link, group);
      }
    }
    if (rows.some((row) => row.deep)) {
      let allExpanded = false;
      /** @type {Element | null} */
      let activeGroup = null;
      const applyCollapseState = () => {
        for (const row of rows) {
          const visible =
            !row.deep ||
            row.group === null ||
            allExpanded ||
            (expandOnScroll && row.group === activeGroup);
          row.item.classList.toggle("kpress-toc-collapsed", !visible);
        }
      };
      const expandAllButton = toc.querySelector("[data-kpress-toc-expand-all]");
      if (expandAllButton) {
        on(expandAllButton, "click", () => {
          allExpanded = !allExpanded;
          expandAllButton.setAttribute("aria-expanded", String(allExpanded));
          expandAllButton.setAttribute(
            "aria-label",
            allExpanded ? "Collapse all sections" : "Expand all sections",
          );
          applyCollapseState();
        });
      }
      // Group handoff waits for the active entry to settle: rapid scrolling
      // (and the smooth glide after a TOC click) sweeps the scroll-spy across
      // every intermediate section, and expanding/collapsing groups mid-sweep
      // makes the whole TOC churn. The highlight still moves instantly; only
      // the expand/collapse handoff is deferred until the reading position has
      // stayed in one group for the settle window. Returning to the current
      // group cancels a pending handoff.
      /** @type {Element | null} */
      let pendingGroup = null;
      /** @type {ReturnType<typeof setTimeout> | null} */
      let settleTimer = null;
      const cancelSettle = () => {
        if (settleTimer !== null) {
          clearTimeout(settleTimer);
          settleTimer = null;
        }
      };
      followActiveGroup = (link) => {
        const group = (link && groupOfLink.get(link)) ?? null;
        if (group === activeGroup) {
          cancelSettle();
          return;
        }
        if (settleTimer !== null && group === pendingGroup) {
          return;
        }
        cancelSettle();
        pendingGroup = group;
        settleTimer = setTimeout(() => {
          settleTimer = null;
          activeGroup = pendingGroup;
          applyCollapseState();
        }, TOC_SCROLL_FOLLOW_SETTLE_MS);
      };
      applyCollapseState();
      cleanups.push(() => {
        cancelSettle();
        for (const row of rows) {
          row.item.classList.remove("kpress-toc-collapsed");
        }
      });
    }
  }

  /**
   * @param {Element | undefined} link
   */
  const setActiveLink = (link) => {
    for (const other of links) {
      other.removeAttribute("data-active");
      other.classList.remove("active");
    }
    link?.setAttribute("data-active", "true");
    link?.classList.add("active");
    // Scroll-follow rides the single active-entry path, so scroll-spy, TOC
    // clicks, and hash arrival all move the expanded group together.
    followActiveGroup(link);
  };

  for (const link of links) {
    // Native hash navigation stays in charge: the browser writes the hash,
    // pushes the history entry (Back/Forward, shareable URLs), and scrolls the
    // viewport — smoothness comes from `scroll-behavior` on .kpress-viewport,
    // which also respects prefers-reduced-motion. The handler only closes the
    // drawer and syncs the highlight.
    on(link, "click", () => {
      setActiveLink(link);
      setExpanded(false);
    });
  }

  if ("IntersectionObserver" in globalThis) {
    const linksById = new Map();
    for (const link of links) {
      const id = tocLinkId(link);
      if (id) {
        linksById.set(id, link);
      }
    }
    const observer = new IntersectionObserver(
      (entries) => {
        // At the top of the document the first heading may sit above the band
        // (or share it with several small sections); the first entry is the
        // only correct highlight there, so it overrides whatever intersects.
        if (ctx.scrollTop() <= TOC_AT_TOP_EPSILON_PX) {
          setActiveLink(links[0]);
          updateToggleVisibility();
          return;
        }
        // A batch can report several headings entering the band at once (small
        // sections, fast scrolls, the initial observation pass). The topmost
        // one is the section the reading position is actually in.
        const topmost = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (!topmost) {
          return;
        }
        setActiveLink(linksById.get(topmost.target.id));
        updateToggleVisibility();
      },
      { root: ctx.observerRoot(), rootMargin: "0px 0px -75% 0px", threshold: 0 },
    );
    for (const id of linksById.keys()) {
      const heading = document.getElementById(id);
      if (heading) {
        observer.observe(heading);
      }
    }
    cleanups.push(() => observer.disconnect());

    const highlightFirstAtTop = () => {
      if (ctx.scrollTop() <= TOC_AT_TOP_EPSILON_PX) {
        setActiveLink(links[0]);
      }
    };
    ctx.onScroll(highlightFirstAtTop);
    cleanups.push(() => ctx.offScroll(highlightFirstAtTop));
    highlightFirstAtTop();
  }

  ctx.onScroll(updateToggleVisibility);
  cleanups.push(() => ctx.offScroll(updateToggleVisibility));

  updateToggleVisibility();

  const dispose = () => {
    for (const cleanup of cleanups) {
      cleanup();
    }
    ctx.unlock();
    toc.removeAttribute("data-kpress-toc-bound");
    delete bound.__kpressTocDispose;
  };
  bound.__kpressTocDispose = dispose;
  toc.setAttribute("data-kpress-toc-bound", "true");
  return dispose;
}

/**
 * Initialize every TOC under `root`. Returns a disposer that tears down all
 * listeners and observers — an embedding host that swaps the document per view
 * calls it on unmount; the standalone page ignores it.
 *
 * @param {ParentNode} [root]
 * @returns {() => void}
 */
export function initKpressToc(
  root = document,
  config = /** @type {Record<string, unknown>} */ ({}),
) {
  /** @type {Array<() => void>} */
  const disposers = [];
  for (const toc of root.querySelectorAll("[data-kpress-toc]")) {
    disposers.push(wireToc(toc, config));
  }
  return () => {
    for (const dispose of disposers) {
      dispose();
    }
  };
}

// The bind returns initKpressToc's disposer, so the runtime owns disposal:
// `configure("toc", ...)` + `rebind("toc")` (or an override) tears down the
// previous wiring before re-binding — the new policy/icon take effect.
behaviors.register("toc", {
  bind: (root, config) => initKpressToc(root, config),
});
