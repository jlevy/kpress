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
  history.replaceState(null, "");
});

describe("history behavior", () => {
  it("stamps the pane scroll offset into the current entry before hash navigation", async () => {
    const viewport = documentMarkup();
    const { initKpressHistory } = await freshHistoryModule();
    const dispose = initKpressHistory();

    viewport.scrollTop = 1234;
    clickSectionLink();

    // Navigation itself stays native; the behavior only records where the
    // reader left from, so Back can return there.
    expect(history.state?.kpressScroll).toBe(1234);
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
