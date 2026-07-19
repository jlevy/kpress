import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The history behavior: viewport-aware scroll restoration for in-document hash
 * navigation. The KPress document scrolls in the `[data-kpress-viewport]` pane,
 * which browsers exclude from native history scroll restoration — the behavior
 * stamps the pane offset into the session-history entry state and restores it
 * on traversal.
 *
 * happy-dom really performs the anchor's hash navigation after dispatch (a new
 * entry with null state, as in a browser), so tests that assert on the stamped
 * state cancel the default action in the bubble phase — the behavior's capture
 * listener has already stamped by then.
 */

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

/**
 * Import a fresh history module and immediately neutralize the instance the
 * module self-registered on the shared runtime, so each test drives exactly
 * one explicit instance.
 */
async function freshHistoryModule() {
  const mod = await importFresh("history.js");
  const { behaviors } = await import("../../src/kpress/format/static/js/runtime.js");
  behaviors.override("history", { bind: () => undefined });
  return mod;
}

function documentMarkup() {
  document.body.innerHTML = `
    <main data-kpress-viewport>
      <article class="kpress">
        <p><a id="section-link" href="#sec">Jump</a></p>
        <h2 id="sec">Section</h2>
      </article>
    </main>
  `;
  return /** @type {HTMLElement} */ (document.querySelector("[data-kpress-viewport]"));
}

/** Cancel navigation in the bubble phase, after capture listeners ran. */
function suppressNavigation() {
  document.addEventListener("click", (event) => event.preventDefault(), { once: true });
}

function clickSectionLink() {
  suppressNavigation();
  const click = new MouseEvent("click", { bubbles: true, cancelable: true });
  document.getElementById("section-link")?.dispatchEvent(click);
}

beforeEach(() => {
  document.body.innerHTML = "";
  // Reset the URL fragment too: tests that let the behavior own navigation
  // really push a "#sec" entry, and a leaked fragment changes what popstate
  // handling does in later tests.
  history.replaceState(null, "", location.pathname + location.search);
});

describe("history behavior", () => {
  it("stamps the pane scroll offset into the current entry before hash navigation", async () => {
    const viewport = documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 1234;
    clickSectionLink();

    // A suppressed click (an owner claimed it) leaves navigation alone; the
    // behavior only records where the reader left from, so Back can return
    // there.
    expect(history.state?.kpressScroll).toBe(1234);
    dispose();
  });

  it("owns plain section-link navigation: pushes the entry and glides the pane", async () => {
    documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    const scrollIntoView = vi.fn();
    document.getElementById("sec").scrollIntoView = scrollIntoView;
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    document.getElementById("section-link")?.dispatchEvent(click);

    // The behavior claims the click (Chromium would scroll the pane
    // instantly), pushes the entry the browser would have pushed (new entry,
    // unstamped), and glides to the target.
    expect(click.defaultPrevented).toBe(true);
    expect(location.hash).toBe("#sec");
    expect(history.state).toBe(null);
    expect(scrollIntoView).toHaveBeenCalledWith(
      expect.objectContaining({ behavior: "smooth", block: "start" }),
    );
    dispose();
  });

  it("does not push a duplicate entry when re-activating the current fragment", async () => {
    documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();
    const dest = /** @type {HTMLElement} */ (document.getElementById("sec"));
    const scrollIntoView = vi.fn();
    dest.scrollIntoView = scrollIntoView;

    document
      .getElementById("section-link")
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
    expect(location.hash).toBe("#sec");

    // Native history pushes no entry when the destination URL is already
    // current; re-activation performs only the scroll.
    const pushes = vi.spyOn(history, "pushState");
    const second = new MouseEvent("click", { bubbles: true, cancelable: true });
    document.getElementById("section-link")?.dispatchEvent(second);

    expect(second.defaultPrevented).toBe(true);
    expect(pushes).not.toHaveBeenCalled();
    expect(scrollIntoView).toHaveBeenCalledTimes(2);
    pushes.mockRestore();
    dispose();
  });

  it("leaves download and non-_self target anchors fully native", async () => {
    documentMarkup();
    document.body.insertAdjacentHTML(
      "beforeend",
      '<a id="blank" href="#sec" target="_blank">b</a>' +
        '<a id="named" href="#sec" target="popup">n</a>' +
        '<a id="dl" href="#sec" download>d</a>' +
        '<a id="self" href="#sec" target="_self">s</a>',
    );
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();
    const pushes = vi.spyOn(history, "pushState");

    for (const id of ["blank", "named", "dl"]) {
      const click = new MouseEvent("click", { bubbles: true, cancelable: true });
      document.getElementById(id)?.dispatchEvent(click);
      // Requesting another browsing context (or a download) keeps default
      // anchor semantics: the behavior must not claim the click or touch
      // this tab's history.
      expect(click.defaultPrevented).toBe(false);
      expect(pushes).not.toHaveBeenCalled();
    }

    const selfClick = new MouseEvent("click", { bubbles: true, cancelable: true });
    document.getElementById("self")?.dispatchEvent(selfClick);
    expect(selfClick.defaultPrevented).toBe(true);
    pushes.mockRestore();
    dispose();
  });

  it("moves the focus-navigation origin to the section target", async () => {
    documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();
    const dest = /** @type {HTMLElement} */ (document.getElementById("sec"));
    dest.scrollIntoView = vi.fn();

    document
      .getElementById("section-link")
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));

    // Native fragment navigation continues keyboard traversal from the
    // target; the owned path reproduces that with a temporary tabindex that
    // is dropped again on blur.
    expect(document.activeElement).toBe(dest);
    expect(dest.getAttribute("tabindex")).toBe("-1");
    dest.dispatchEvent(new Event("blur"));
    expect(dest.hasAttribute("tabindex")).toBe(false);
    dispose();
  });

  it("preserves an authored tabindex on the section target", async () => {
    documentMarkup();
    const dest = /** @type {HTMLElement} */ (document.getElementById("sec"));
    dest.setAttribute("tabindex", "0");
    dest.scrollIntoView = vi.fn();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    document
      .getElementById("section-link")
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));

    expect(document.activeElement).toBe(dest);
    expect(dest.getAttribute("tabindex")).toBe("0");
    dest.dispatchEvent(new Event("blur"));
    expect(dest.getAttribute("tabindex")).toBe("0");
    dispose();
  });

  it("handles malformed fragment hrefs without throwing and leaves them native", async () => {
    documentMarkup();
    document.body.insertAdjacentHTML("beforeend", '<a id="bad" href="#%">bad</a>');
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    expect(() => document.getElementById("bad")?.dispatchEvent(click)).not.toThrow();
    // No element matches the raw "%" id, so the click stays native.
    expect(click.defaultPrevented).toBe(false);
    dispose();
  });

  it("leaves footnote references to their popover owner", async () => {
    documentMarkup();
    document.body.insertAdjacentHTML(
      "beforeend",
      '<main data-note><a id="fn-ref" class="kpress-footnote-ref" href="#fn-1">1</a></main>',
    );
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    document.getElementById("fn-ref")?.dispatchEvent(click);

    expect(click.defaultPrevented).toBe(false);
    dispose();
  });

  it("preserves unrelated history state when stamping", async () => {
    const viewport = documentMarkup();
    history.replaceState({ hostKey: "kept" }, "");
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 50;
    clickSectionLink();

    expect(history.state?.hostKey).toBe("kept");
    expect(history.state?.kpressScroll).toBe(50);
    dispose();
  });

  it("ignores clicks on non-hash links", async () => {
    const viewport = documentMarkup();
    document.body.insertAdjacentHTML("beforeend", '<a id="external" href="/elsewhere">x</a>');
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 60;
    suppressNavigation();
    document
      .getElementById("external")
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));

    expect(history.state?.kpressScroll).toBeUndefined();
    dispose();
  });

  it("stamps bare-# clicks (the TOC Contents link) so Back can return", async () => {
    const viewport = documentMarkup();
    document.body.insertAdjacentHTML("beforeend", '<a id="bare" href="#">top</a>');
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 1872;
    suppressNavigation();
    document
      .getElementById("bare")
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));

    expect(history.state?.kpressScroll).toBe(1872);
    dispose();
  });

  it("restores the pane top for an unstamped fragmentless entry", async () => {
    const viewport = documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 900;
    window.dispatchEvent(new PopStateEvent("popstate", { state: null }));

    // Document-top semantics: traversing to an entry with no fragment and no
    // stamp lands at the top, as the browser does for a document scroller.
    expect(viewport.scrollTop).toBe(0);
    dispose();
  });

  it("leaves non-plain host history state untouched (Date)", async () => {
    const viewport = documentMarkup();
    const hostState = new Date("2020-01-02T03:04:05Z");
    history.replaceState(hostState, "");
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 226;
    clickSectionLink();

    expect(history.state instanceof Date || typeof history.state?.getTime === "function").toBe(
      true,
    );
    expect(history.state?.kpressScroll).toBeUndefined();
    dispose();
  });

  it("leaves array host history state untouched", async () => {
    const viewport = documentMarkup();
    history.replaceState([1, 2, 3], "");
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 50;
    clickSectionLink();

    expect(Array.isArray(history.state)).toBe(true);
    expect(history.state?.kpressScroll).toBeUndefined();
    dispose();
  });

  it("leaves a host-owned non-numeric kpressScroll key untouched", async () => {
    const viewport = documentMarkup();
    history.replaceState({ kpressScroll: "host-token" }, "");
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 50;
    clickSectionLink();

    expect(history.state?.kpressScroll).toBe("host-token");
    dispose();
  });

  it("ignores a non-finite stamped offset and falls back to the fragment target", async () => {
    documentMarkup();
    const target = /** @type {HTMLElement} */ (document.getElementById("sec"));
    const scrollIntoView = vi.fn();
    target.scrollIntoView = scrollIntoView;
    location.hash = "#sec";

    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    window.dispatchEvent(new PopStateEvent("popstate", { state: { kpressScroll: Number.NaN } }));

    expect(scrollIntoView).toHaveBeenCalled();
    dispose();
    location.hash = "";
  });

  it("survives a malformed percent-encoded fragment during popstate", async () => {
    const viewport = documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    const happyWindow = /** @type {{ happyDOM?: { setURL?: (url: string) => void } }} */ (window);
    happyWindow.happyDOM?.setURL?.("http://localhost/page#%");
    viewport.scrollTop = 40;

    expect(() =>
      window.dispatchEvent(new PopStateEvent("popstate", { state: null })),
    ).not.toThrow();

    dispose();
    happyWindow.happyDOM?.setURL?.("http://localhost/");
  });

  it("restores the stamped pane offset on popstate", async () => {
    const viewport = documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 4321;
    window.dispatchEvent(new PopStateEvent("popstate", { state: { kpressScroll: 777 } }));

    expect(viewport.scrollTop).toBe(777);
    dispose();
  });

  it("falls back to the fragment target on popstate without a stamped offset", async () => {
    documentMarkup();
    const target = /** @type {HTMLElement} */ (document.getElementById("sec"));
    const scrollIntoView = vi.fn();
    target.scrollIntoView = scrollIntoView;
    location.hash = "#sec";

    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    window.dispatchEvent(new PopStateEvent("popstate", { state: null }));

    expect(scrollIntoView).toHaveBeenCalled();
    dispose();
    location.hash = "";
  });

  it("keeps the stamp fresh as the reader scrolls (debounced)", async () => {
    vi.useFakeTimers();
    const viewport = documentMarkup();
    const mod = await freshHistoryModule();
    const dispose = mod.initKpressHistory();

    viewport.scrollTop = 900;
    viewport.dispatchEvent(new Event("scroll"));
    expect(history.state?.kpressScroll).toBeUndefined();
    vi.advanceTimersByTime(mod.HISTORY_STAMP_DEBOUNCE_MS + 10);

    expect(history.state?.kpressScroll).toBe(900);
    dispose();
    vi.useRealTimers();
  });

  it("disposer removes all listeners", async () => {
    const viewport = documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();
    dispose();

    viewport.scrollTop = 10;
    clickSectionLink();
    expect(history.state?.kpressScroll).toBeUndefined();

    viewport.scrollTop = 55;
    window.dispatchEvent(new PopStateEvent("popstate", { state: { kpressScroll: 5 } }));
    expect(viewport.scrollTop).toBe(55);
  });

  it("registers as the 'history' behavior with a working disposer", async () => {
    const viewport = documentMarkup();
    const { behaviors } = await import("../../src/kpress/format/static/js/runtime.js");
    await importFresh("history.js");

    behaviors.rebind("history");
    viewport.scrollTop = 321;
    clickSectionLink();

    expect(history.state?.kpressScroll).toBe(321);
    // Leave the shared registry inert for any later test file reuse.
    behaviors.override("history", { bind: () => undefined });
  });
});
