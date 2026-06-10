import { toggleBackdrop } from "./overlay.js";
import { resolveKpressViewport, viewportScrollContext } from "./viewport.js";

const TOC_TOGGLE_SCROLL_THRESHOLD_PX = 100;

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
function wireToc(toc) {
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
    // sidebar is hidden by the container query), so reveal it once the reader has
    // scrolled past the threshold — matching the TextPress behavior of a TOC
    // indicator that hovers in after a short scroll. Wide mode hides the toggle
    // entirely via CSS, so toggling this class has no visible effect there.
    const showToggle = ctx.scrollTop() > TOC_TOGGLE_SCROLL_THRESHOLD_PX;
    button.classList.toggle("show-toggle", showToggle);
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
    on(titleTop, "click", (event) => {
      event.preventDefault();
      setExpanded(false);
      ctx.scrollToTop(true);
    });
  }

  for (const link of links) {
    on(link, "click", (event) => {
      event.preventDefault();
      for (const other of links) {
        other.removeAttribute("data-active");
        other.classList.remove("active");
      }
      link.setAttribute("data-active", "true");
      link.classList.add("active");
      setExpanded(false);
      const id = tocLinkId(link);
      const heading = id ? document.getElementById(id) : null;
      heading?.scrollIntoView({ behavior: "smooth", block: "start" });
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
        for (const entry of entries) {
          if (!entry.isIntersecting) {
            continue;
          }
          for (const link of linksById.values()) {
            link.removeAttribute("data-active");
            link.classList.remove("active");
          }
          linksById.get(entry.target.id)?.setAttribute("data-active", "true");
          linksById.get(entry.target.id)?.classList.add("active");
          updateToggleVisibility();
        }
      },
      { root: ctx.observerRoot(), rootMargin: "-20% 0px -65% 0px", threshold: 0 },
    );
    for (const id of linksById.keys()) {
      const heading = document.getElementById(id);
      if (heading) {
        observer.observe(heading);
      }
    }
    cleanups.push(() => observer.disconnect());
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
export function initKpressToc(root = document) {
  /** @type {Array<() => void>} */
  const disposers = [];
  for (const toc of root.querySelectorAll("[data-kpress-toc]")) {
    disposers.push(wireToc(toc));
  }
  return () => {
    for (const dispose of disposers) {
      dispose();
    }
  };
}

initKpressToc();
