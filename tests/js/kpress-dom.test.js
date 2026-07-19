import { beforeEach, describe, expect, it, vi } from "vitest";

let importCounter = 0;
const COPY_STATE_RESET_DELAY_MS = 1200;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

beforeEach(() => {
  document.body.innerHTML = "";
  document.body.className = "";
  document.body.removeAttribute("style");
  document.documentElement.removeAttribute("data-kpress-theme");
  document.documentElement.removeAttribute("data-kpress-resolved-theme");
  delete globalThis.mermaid;
  localStorage.clear();
  vi.useRealTimers();
  globalThis.matchMedia = (query) => ({
    matches: query.includes("dark"),
    media: query,
    onchange: null,
    addEventListener() {},
    removeEventListener() {},
    addListener() {},
    removeListener() {},
    dispatchEvent() {
      return true;
    },
  });
});

describe("KPress browser modules", () => {
  it("initializes theme state without a build step", async () => {
    localStorage.setItem("kpress.theme", "dark");

    const { setKpressTheme } = await importFresh("theme.js");

    expect(document.documentElement.dataset.kpressTheme).toBe("dark");
    expect(document.documentElement.dataset.kpressResolvedTheme).toBe("dark");

    setKpressTheme("system");

    expect(document.documentElement.dataset.kpressTheme).toBe("system");
    expect(document.documentElement.dataset.kpressResolvedTheme).toBe("dark");
    expect(localStorage.getItem("kpress.theme")).toBe("system");
  });

  it("wires standalone theme toggle controls and system changes", async () => {
    const listeners = [];
    let prefersDark = false;
    globalThis.matchMedia = (query) => ({
      get matches() {
        return prefersDark;
      },
      media: query,
      onchange: null,
      addEventListener(_type, listener) {
        listeners.push(listener);
      },
      removeEventListener() {},
      addListener(listener) {
        listeners.push(listener);
      },
      removeListener() {},
      dispatchEvent() {
        return true;
      },
    });
    document.body.innerHTML = `
      <div class="kpress-settings" id="kpress-settings" aria-expanded="false">
        <button type="button" class="kpress-settings-btn" id="kpress-settings-btn" aria-haspopup="true">gear</button>
        <div class="kpress-settings-menu kpress-menu" role="menu">
          <div class="kpress-menu-chooser" role="group" aria-label="Theme">
            <button type="button" class="kpress-menu-seg" role="menuitemradio" data-kpress-theme-choice="system" aria-checked="false"></button>
            <button type="button" class="kpress-menu-seg" role="menuitemradio" data-kpress-theme-choice="light" aria-checked="false"></button>
            <button type="button" class="kpress-menu-seg" role="menuitemradio" data-kpress-theme-choice="dark" aria-checked="false"></button>
          </div>
        </div>
      </div>
    `;

    await importFresh("theme.js");

    const system = document.querySelector('[data-kpress-theme-choice="system"]');
    const light = document.querySelector('[data-kpress-theme-choice="light"]');
    const dark = document.querySelector('[data-kpress-theme-choice="dark"]');
    expect(system?.getAttribute("aria-checked")).toBe("true");

    light?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(document.documentElement.dataset.kpressTheme).toBe("light");
    expect(document.documentElement.dataset.kpressResolvedTheme).toBe("light");
    expect(localStorage.getItem("kpress.theme")).toBe("light");
    expect(light?.getAttribute("aria-checked")).toBe("true");
    expect(dark?.getAttribute("aria-checked")).toBe("false");

    system?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    prefersDark = true;
    listeners[0]?.();

    expect(document.documentElement.dataset.kpressTheme).toBe("system");
    expect(document.documentElement.dataset.kpressResolvedTheme).toBe("dark");
    expect(system?.getAttribute("aria-checked")).toBe("true");

    // Gear popover behavior now lives in the menu primitive (menu.js); the
    // settings widget binds it. Bind explicitly here to prove the same markup
    // still opens on click and closes on outside click.
    const { bindMenu } = await importFresh("menu.js");
    const settings = /** @type {HTMLElement} */ (document.querySelector(".kpress-settings"));
    const gear = /** @type {HTMLElement} */ (document.querySelector(".kpress-settings-btn"));
    bindMenu(settings, gear);
    expect(settings?.getAttribute("aria-expanded")).toBe("false");
    gear?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(settings?.getAttribute("aria-expanded")).toBe("true");
    document.body.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(settings?.getAttribute("aria-expanded")).toBe("false");
  });

  it("wraps prose tables once for responsive layout", async () => {
    document.body.innerHTML = `
      <article class="kpress-prose">
        <table><tbody><tr><td>Value</td></tr></tbody></table>
      </article>
    `;

    const { initKpressTables } = await importFresh("tables.js");
    initKpressTables();

    const wrappers = document.querySelectorAll(".kpress-table-wrap");
    const table = document.querySelector("table");
    expect(wrappers).toHaveLength(1);
    expect(table?.classList.contains("kpress-table")).toBe(true);
    expect(wrappers[0]?.firstElementChild).toBe(table);
  });

  it("wraps tables inserted when a tab panel becomes active", async () => {
    document.body.innerHTML = `
      <article class="kpress-prose">
        <div data-kpress-tabs>
          <button role="tab" aria-selected="true" aria-controls="panel-a" tabindex="0">A</button>
          <button role="tab" aria-selected="false" aria-controls="panel-b" tabindex="-1">B</button>
          <section id="panel-a" class="kpress-tab-panel">Alpha</section>
          <section id="panel-b" class="kpress-tab-panel" hidden></section>
        </div>
      </article>
    `;

    await importFresh("tables.js");
    document.getElementById("panel-b").innerHTML =
      "<table><tbody><tr><td>99</td></tr></tbody></table>";
    await importFresh("tabs.js");

    document
      .querySelector('[aria-controls="panel-b"]')
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    const table = document.querySelector("#panel-b table");
    expect(table?.closest(".kpress-table-wrap")).toBeTruthy();
    expect(table?.classList.contains("kpress-table")).toBe(true);
    expect(document.querySelector("#panel-b [data-kpress-numeric='true']")).toBeTruthy();
  });

  it("renders Mermaid diagrams when a host provides Mermaid", async () => {
    const render = vi.fn(async (id, source) => ({
      svg: `<svg data-kpress-test-id="${id}"><text>${source}</text></svg>`,
    }));
    globalThis.mermaid = {
      initialize: vi.fn(),
      render,
    };
    document.body.innerHTML = `
      <figure class="kpress-diagram kpress-mermaid" data-kpress-diagram="mermaid" data-kpress-diagram-status="source">
        <pre class="kpress-diagram-source"><code class="language-mermaid">graph TD
A--&gt;B</code></pre>
      </figure>
    `;

    const { initKpressDiagrams } = await importFresh("diagrams.js");
    await initKpressDiagrams();

    const figure = document.querySelector(".kpress-mermaid");
    const source = document.querySelector(".kpress-diagram-source");
    expect(render).toHaveBeenCalledWith(
      expect.stringMatching(/^kpress-mermaid-/),
      "graph TD\nA-->B",
    );
    expect(figure?.getAttribute("data-kpress-diagram-status")).toBe("rendered");
    expect(source?.hidden).toBe(true);
    expect(document.querySelector(".kpress-diagram-rendered svg")).not.toBeNull();
  });

  it("posts host-ready and resize messages for embedded documents", async () => {
    document.title = "Host fixture";
    document.body.innerHTML = `
      <article class="kpress" data-kpress-document-id="doc-1">
        <p>Embedded body</p>
      </article>
    `;
    Object.defineProperty(document.documentElement, "scrollHeight", {
      configurable: true,
      value: 900,
    });
    Object.defineProperty(document.documentElement, "clientWidth", {
      configurable: true,
      value: 720,
    });
    const messages = [];
    const targetWindow = {
      postMessage(message, targetOrigin) {
        messages.push({ message, targetOrigin });
      },
    };

    const { initKpressHost } = await importFresh("host.js");
    const controller = initKpressHost(document, {
      embedded: true,
      targetWindow,
      targetOrigin: "https://host.example",
    });

    controller.postResize();

    expect(messages[0]).toEqual({
      targetOrigin: "https://host.example",
      message: {
        source: "kpress",
        version: 1,
        type: "kpress:ready",
        documentId: "doc-1",
        height: 900,
        width: 720,
      },
    });
    expect(messages.at(-1).message.type).toBe("kpress:resize");
    expect(messages.at(-1).message.height).toBe(900);
  });

  it("posts host expand and close messages with Escape close opt-in", async () => {
    document.body.innerHTML = `
      <article class="kpress" data-kpress-document-id="doc-actions">
        <button type="button" data-kpress-host-action="expand" aria-pressed="false">Expand</button>
        <button type="button" data-kpress-host-action="close">Close</button>
      </article>
    `;
    const messages = [];
    const targetWindow = {
      postMessage(message) {
        messages.push(message);
      },
    };

    const { initKpressHost } = await importFresh("host.js");
    initKpressHost(document, {
      embedded: true,
      targetWindow,
      escapeClose: true,
    });

    document
      .querySelector('[data-kpress-host-action="expand"]')
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
    document
      .querySelector('[data-kpress-host-action="close"]')
      ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));

    expect(messages.map((message) => message.type)).toEqual([
      "kpress:ready",
      "kpress:resize",
      "kpress:expand",
      "kpress:close",
      "kpress:close",
    ]);
    expect(messages[2]).toMatchObject({
      documentId: "doc-actions",
      expanded: true,
    });
    expect(
      document.querySelector('[data-kpress-host-action="expand"]')?.getAttribute("aria-pressed"),
    ).toBe("true");
    expect(messages[3]).toMatchObject({ reason: "control" });
    expect(messages[4]).toMatchObject({ reason: "escape" });
  });

  it("toggles table-of-contents disclosure state", async () => {
    document.body.innerHTML = `
      <nav data-kpress-toc>
        <button class="kpress-toc-toggle" aria-expanded="false">Contents</button>
        <ol><li><a href="#intro">Intro</a></li></ol>
      </nav>
    `;

    await importFresh("toc.js");

    const button = document.querySelector(".kpress-toc-toggle");
    const toc = document.querySelector("[data-kpress-toc]");
    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    // The drawer open/close is driven by the kpress-mobile-visible class (+ CSS),
    // NOT by hiding the <ol>: in the wide sidebar there is no toggle to reopen a
    // collapsed list, so the list must never be display:none'd.
    expect(button?.getAttribute("aria-expanded")).toBe("true");
    expect(toc?.classList.contains("kpress-mobile-visible")).toBe(true);

    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(button?.getAttribute("aria-expanded")).toBe("false");
    expect(toc?.classList.contains("kpress-mobile-visible")).toBe(false);
  });

  it("tracks active TOC links and closes the mobile drawer on navigation", async () => {
    document.body.innerHTML = `
      <nav data-kpress-toc>
        <button class="kpress-toc-toggle" aria-expanded="false">Contents</button>
        <ol hidden><li><a href="#intro">Intro</a></li></ol>
      </nav>
      <h2 id="intro">Intro</h2>
    `;

    await importFresh("toc.js");

    const button = document.querySelector(".kpress-toc-toggle");
    const list = document.querySelector("ol");
    const link = document.querySelector(".kpress-toc a");
    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    link?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(link?.getAttribute("data-active")).toBe("true");
    expect(button?.getAttribute("aria-expanded")).toBe("false");
    expect(list?.hidden).toBe(true);
    expect(document.body.classList.contains("kpress-toc-open")).toBe(false);
  });

  it("locks the document viewport and shows the backdrop while the drawer is open", async () => {
    document.body.innerHTML = `
      <main data-kpress-viewport>
        <div class="kpress-content-with-toc">
          <button class="kpress-toc-toggle" data-kpress-toc-toggle aria-expanded="false">Contents</button>
          <div class="kpress-toc-backdrop" data-kpress-toc-backdrop></div>
          <nav data-kpress-toc>
            <ol hidden><li><a href="#intro">Intro</a></li></ol>
          </nav>
        </div>
        <h2 id="intro">Intro</h2>
      </main>
    `;

    await importFresh("toc.js");

    const viewport = document.querySelector("[data-kpress-viewport]");
    const button = document.querySelector(".kpress-toc-toggle");
    const backdrop = document.querySelector(".kpress-toc-backdrop");
    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(backdrop?.classList.contains("kpress-visible")).toBe(true);
    // The viewport element is the scroll lock — no document.body mutation.
    expect(viewport?.style.overflow).toBe("hidden");
    expect(document.body.style.top).toBe("");

    backdrop?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(backdrop?.classList.contains("kpress-visible")).toBe(false);
    expect(viewport?.style.overflow).toBe("");
  });

  it("leaves TOC link activation to native hash navigation and closes the drawer", async () => {
    document.body.innerHTML = `
      <main data-kpress-viewport>
        <div class="kpress-content-with-toc">
          <button class="kpress-toc-toggle" data-kpress-toc-toggle aria-expanded="false">Contents</button>
          <div class="kpress-toc-backdrop" data-kpress-toc-backdrop></div>
          <nav data-kpress-toc>
            <ol hidden><li><a href="#intro">Intro</a></li></ol>
          </nav>
        </div>
        <h2 id="intro">Intro</h2>
      </main>
    `;

    const scrollIntoView = vi.fn();

    await importFresh("toc.js");
    document.getElementById("intro").scrollIntoView = scrollIntoView;

    const viewport = document.querySelector("[data-kpress-viewport]");
    const button = document.querySelector(".kpress-toc-toggle");
    const link = document.querySelector(".kpress-toc a");
    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(viewport?.style.overflow).toBe("hidden");

    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    link?.dispatchEvent(event);

    // toc.js itself never claims the click — section-link navigation is
    // owned by the history behavior (not loaded here), which pushes the
    // entry and glides the pane.
    expect(event.defaultPrevented).toBe(false);
    expect(scrollIntoView).not.toHaveBeenCalled();
    expect(link?.getAttribute("data-active")).toBe("true");
    // Selecting a link closes the drawer and releases the viewport lock.
    expect(viewport?.style.overflow).toBe("");
  });

  it("leaves the Contents (top) link to native bare-# navigation and scrolls the pane", async () => {
    document.body.innerHTML = `
      <main data-kpress-viewport>
        <div class="kpress-content-with-toc">
          <button class="kpress-toc-toggle" data-kpress-toc-toggle aria-expanded="false">Contents</button>
          <nav data-kpress-toc>
            <a href="#" class="kpress-toc-title toc-link toc-title" data-kpress-toc-top>Contents</a>
            <ol hidden><li><a href="#intro">Intro</a></li></ol>
          </nav>
        </div>
        <h2 id="intro">Intro</h2>
      </main>
    `;

    await importFresh("toc.js");

    const viewport = document.querySelector("[data-kpress-viewport]");
    viewport.scrollTop = 1500;
    const top = document.querySelector("[data-kpress-toc-top]");
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    top?.dispatchEvent(event);

    // Native bare-"#" navigation owns the URL (clears any section hash) and the
    // history entry; the browser only scrolls the *document* for an empty
    // fragment, so the handler still scrolls the pane itself (smoothly, hence
    // the wait).
    expect(event.defaultPrevented).toBe(false);
    await vi.waitFor(() => expect(viewport?.scrollTop).toBe(0));
  });

  it("initKpressToc returns a disposer that unbinds and tears down the TOC", async () => {
    document.body.innerHTML = `
      <main data-kpress-viewport><div class="kpress-content-with-toc"></div></main>
    `;
    const mod = await importFresh("toc.js");
    const scope = document.querySelector(".kpress-content-with-toc");
    scope.innerHTML = `
      <button class="kpress-toc-toggle" data-kpress-toc-toggle aria-expanded="false">Contents</button>
      <nav data-kpress-toc><ol hidden><li><a href="#intro">Intro</a></li></ol></nav>
    `;

    const dispose = mod.initKpressToc(document);
    const toc = document.querySelector("[data-kpress-toc]");
    expect(toc.getAttribute("data-kpress-toc-bound")).toBe("true");

    dispose();
    expect(toc.getAttribute("data-kpress-toc-bound")).toBe(null);
    // After teardown a toggle click no longer drives drawer state.
    const button = document.querySelector(".kpress-toc-toggle");
    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(toc.classList.contains("kpress-mobile-visible")).toBe(false);
  });

  it("shows the mobile TOC toggle after scrolling past the threshold, then hides it near the top", async () => {
    document.body.innerHTML = `
      <nav data-kpress-toc>
        <button class="kpress-toc-toggle" aria-expanded="false">Contents</button>
        <ol hidden>
          <li><a href="#intro">Intro</a></li>
          <li><a href="#details">Details</a></li>
        </ol>
      </nav>
      <h2 id="intro">Intro</h2>
      <h2 id="details">Details</h2>
    `;

    await importFresh("toc.js");

    const button = document.querySelector(".kpress-toc-toggle");
    const links = document.querySelectorAll(".kpress-toc a");
    // Scrolled past the threshold while the FIRST section is still active: in
    // narrow mode the floating toggle is the only way to reach the TOC, so it
    // appears regardless of which section is active.
    links[0]?.setAttribute("data-active", "true");
    links[0]?.classList.add("active");
    Object.defineProperty(window, "pageYOffset", { configurable: true, value: 160 });
    window.dispatchEvent(new Event("scroll"));

    expect(button?.classList.contains("show-toggle")).toBe(true);

    // Back near the top: the toggle hides again.
    Object.defineProperty(window, "pageYOffset", { configurable: true, value: 0 });
    window.dispatchEvent(new Event("scroll"));

    expect(button?.classList.contains("show-toggle")).toBe(false);
  });

  it("prevents mobile TOC overscroll at drawer boundaries", async () => {
    document.body.innerHTML = `
      <nav data-kpress-toc>
        <button class="kpress-toc-toggle" aria-expanded="false">Contents</button>
        <ol hidden><li><a href="#intro">Intro</a></li></ol>
      </nav>
    `;

    await importFresh("toc.js");

    const toc = document.querySelector("[data-kpress-toc]");
    Object.defineProperty(toc, "scrollTop", { configurable: true, value: 0 });
    Object.defineProperty(toc, "scrollHeight", { configurable: true, value: 600 });
    Object.defineProperty(toc, "clientHeight", { configurable: true, value: 300 });

    const start = new Event("touchstart", { bubbles: true, cancelable: true });
    Object.defineProperty(start, "touches", { value: [{ clientY: 100 }] });
    toc?.dispatchEvent(start);

    const move = new Event("touchmove", { bubbles: true, cancelable: true });
    Object.defineProperty(move, "touches", { value: [{ clientY: 140 }] });
    toc?.dispatchEvent(move);

    expect(move.defaultPrevented).toBe(true);
  });

  it("creates internal-link and footnote tooltip previews", async () => {
    document.body.innerHTML = `
      <p><a href="#target">Target</a></p>
      <h2 id="target">Target Heading</h2>
      <p>Nearby <strong>preview</strong> text.</p>
      <sup class="kpress-footnote-ref"><a href="#fn-note" id="fnref-note">[note]</a></sup>
      <section class="kpress-footnotes"><ol><li id="fn-note">Footnote <em>body</em></li></ol></section>
    `;

    await importFresh("tooltips.js");

    document
      .querySelector('a[href="#target"]')
      ?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")?.textContent).toContain("Target Heading");
    expect(document.querySelector(".kpress-tooltip")?.innerHTML).toContain("Nearby preview text.");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")).toBeNull();

    const footnoteLink = document.querySelector(".kpress-footnote-ref a");
    footnoteLink?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")?.textContent).toContain("Footnote body");
    expect(document.querySelector(".kpress-tooltip")?.innerHTML).toContain("<em>body</em>");

    const touch = new TouchEvent("touchstart", { bubbles: true, cancelable: true });
    footnoteLink?.dispatchEvent(touch);
    expect(touch.defaultPrevented).toBe(true);
  });

  it("suppresses tooltips on table-of-contents links but not elsewhere", async () => {
    document.body.innerHTML = `
      <nav class="kpress-toc kpress-no-print" data-kpress-toc>
        <ol class="toc-list"><li><a href="#target">Target Heading</a></li></ol>
      </nav>
      <p><a href="#target">jump</a></p>
      <h2 id="target">Target Heading</h2>
      <p>Nearby preview text.</p>
    `;

    await importFresh("tooltips.js");

    // A TOC link already shows the heading's text, so hovering it adds nothing.
    document
      .querySelector('.kpress-toc a[href="#target"]')
      ?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")).toBeNull();

    // The same internal link in the body still previews the target.
    document
      .querySelector('p a[href="#target"]')
      ?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")?.textContent).toContain("Target Heading");
  });

  it("wires footnote anchors injected after load (host fragment)", async () => {
    document.body.innerHTML = "";
    await importFresh("tooltips.js");

    // An embedding host app injects the rendered document after
    // tooltips.js has loaded and self-initialized, so its footnote anchors
    // appear later. The MutationObserver must wire them.
    const host = document.createElement("div");
    host.innerHTML = `
      <sup class="kpress-footnote-ref"><a href="#fn-late" id="fnref-late">[late]</a></sup>
      <section class="kpress-footnotes"><ol><li id="fn-late">Late footnote body</li></ol></section>
    `;
    document.body.appendChild(host);
    await new Promise((resolve) => setTimeout(resolve, 0));

    host
      .querySelector(".kpress-footnote-ref a")
      ?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")?.textContent).toContain("Late footnote body");
  });

  it("creates typed previews for rich internal-link targets", async () => {
    document.body.innerHTML = `
      <main id="main-content">
        <p>
          <a href="#figure-a">Figure</a>
          <a href="#table-a">Table</a>
          <a href="#code-a">Code</a>
          <a href="#details-a">Details</a>
        </p>
        <figure id="figure-a"><img src="chart.png"><figcaption>Revenue chart</figcaption></figure>
        <table id="table-a"><caption>Quarterly table</caption><tbody><tr><th>Revenue</th></tr></tbody></table>
        <pre id="code-a"><code>const value = 42;\\nconsole.log(value);</code></pre>
        <details id="details-a"><summary>Model assumptions</summary><p>Body</p></details>
      </main>
    `;

    await importFresh("tooltips.js");

    for (const [href, expected] of [
      ["#figure-a", "Figure: Revenue chart"],
      ["#table-a", "Table: Quarterly table"],
      ["#code-a", "Code: const value = 42;"],
      ["#details-a", "Details: Model assumptions"],
    ]) {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
      document
        .querySelector(`a[href="${href}"]`)
        ?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
      const tooltip = document.querySelector(".kpress-tooltip");
      expect(tooltip?.textContent?.replace(/\s+/g, " ").trim()).toContain(expected);
      expect(tooltip?.getAttribute("data-kpress-tooltip-position")).toBeTruthy();
    }
  });

  it("clamps tooltip placement to an embedded viewport", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1000 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 800 });
    document.body.innerHTML = `
      <main data-kpress-viewport>
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Nearby preview text.</p>
      </main>
    `;
    const viewport = document.querySelector("[data-kpress-viewport]");
    const trigger = document.querySelector('a[href="#target"]');
    viewport.getBoundingClientRect = () => ({
      left: 200,
      right: 560,
      top: 50,
      bottom: 350,
      width: 360,
      height: 300,
      x: 200,
      y: 50,
      toJSON() {},
    });
    trigger.getBoundingClientRect = () => ({
      left: 230,
      right: 290,
      top: 110,
      bottom: 130,
      width: 60,
      height: 20,
      x: 230,
      y: 110,
      toJSON() {},
    });

    await importFresh("tooltips.js");

    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    const tooltip = document.querySelector(".kpress-tooltip");

    expect(tooltip?.getAttribute("data-kpress-tooltip-position")).toBe("mobile-bottom");
    expect(tooltip?.style.insetInlineStart).toBe("210px");
    expect(tooltip?.style.insetInlineEnd).toBe("450px");
    expect(tooltip?.style.bottom).toBe("460px");
    expect(tooltip?.style.maxWidth).toBe("340px");
  });

  it("adds footnote truncation and navigation controls to tooltip previews", async () => {
    document.body.innerHTML = `
      <sup class="kpress-footnote-ref"><a href="#fn-long" id="fnref-long">[long]</a></sup>
      <section class="kpress-footnotes"><ol><li id="fn-long">${"Long footnote text ".repeat(
        40,
      )}<a class="kpress-footnote-backref" href="#fnref-long">Back</a></li></ol></section>
    `;

    await importFresh("tooltips.js");

    const footnoteLink = document.querySelector(".kpress-footnote-ref a");
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    footnoteLink?.dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);

    footnoteLink?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    const tooltip = document.querySelector(".kpress-tooltip");
    expect(tooltip?.classList.contains("kpress-tooltip-footnote")).toBe(true);
    expect(tooltip?.textContent).toContain("...");
    expect(tooltip?.querySelector(".kpress-footnote-nav-link")?.getAttribute("href")).toBe(
      "#fn-long",
    );
    expect(tooltip?.innerHTML).not.toContain("kpress-footnote-backref");
  });

  it("keeps tooltips open across the trigger-to-tooltip hover bridge", async () => {
    vi.useFakeTimers();
    document.body.innerHTML = `
      <p><a href="#target">Target</a></p>
      <h2 id="target">Target Heading</h2>
      <p>Nearby preview text.</p>
    `;

    await importFresh("tooltips.js");

    const trigger = document.querySelector('a[href="#target"]');
    trigger?.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
    vi.advanceTimersByTime(500);
    const tooltip = document.querySelector(".kpress-tooltip");
    expect(tooltip?.textContent).toContain("Target Heading");

    trigger?.dispatchEvent(
      new MouseEvent("mouseleave", {
        bubbles: true,
        clientX: 0,
        clientY: 0,
      }),
    );
    vi.advanceTimersByTime(2499);
    expect(document.querySelector(".kpress-tooltip")).toBe(tooltip);

    tooltip?.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
    vi.advanceTimersByTime(1000);
    expect(document.querySelector(".kpress-tooltip")).toBe(tooltip);

    tooltip?.dispatchEvent(new MouseEvent("mouseleave", { bubbles: true }));
    vi.advanceTimersByTime(2499);
    expect(document.querySelector(".kpress-tooltip")).toBe(tooltip);

    vi.advanceTimersByTime(1);
    // The hide timer fires, but fadeOutAndRemove waits for transitionend
    // (or a 700ms safety timeout) before removing the DOM node.
    vi.advanceTimersByTime(700);
    expect(document.querySelector(".kpress-tooltip")).toBeNull();
  });

  it("uses Kash-compatible tooltip hide delays for pointer direction and wide placement", async () => {
    vi.useFakeTimers();
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1300 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 800 });
    document.body.innerHTML = `
      <main id="main-content">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Nearby preview text.</p>
      </main>
    `;
    const mainContent = document.getElementById("main-content");
    mainContent.getBoundingClientRect = () => ({
      left: 0,
      right: 900,
      top: 0,
      bottom: 600,
      width: 900,
      height: 600,
      x: 0,
      y: 0,
      toJSON() {},
    });

    await importFresh("tooltips.js");

    const trigger = document.querySelector('a[href="#target"]');
    trigger.getBoundingClientRect = () => ({
      left: 100,
      right: 160,
      top: 100,
      bottom: 120,
      width: 60,
      height: 20,
      x: 100,
      y: 100,
      toJSON() {},
    });

    trigger.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
    vi.advanceTimersByTime(500);
    const wideTooltip = document.querySelector(".kpress-tooltip");
    expect(wideTooltip?.getAttribute("data-kpress-tooltip-position")).toBe("wide-right");
    trigger.dispatchEvent(new MouseEvent("mouseleave", { bubbles: true }));
    vi.advanceTimersByTime(3999);
    expect(document.querySelector(".kpress-tooltip")).toBe(wideTooltip);

    vi.advanceTimersByTime(1);
    vi.advanceTimersByTime(700);
    expect(document.querySelector(".kpress-tooltip")).toBeNull();

    mainContent.getBoundingClientRect = () => ({
      left: 0,
      right: 1100,
      top: 0,
      bottom: 600,
      width: 1100,
      height: 600,
      x: 0,
      y: 0,
      toJSON() {},
    });
    trigger.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
    vi.advanceTimersByTime(500);
    const bridgeTooltip = document.querySelector(".kpress-tooltip");
    expect(bridgeTooltip?.getAttribute("data-kpress-tooltip-position")).toBe("bottom-right");

    trigger.dispatchEvent(
      new MouseEvent("mouseleave", {
        bubbles: true,
        clientX: 120,
        clientY: 130,
      }),
    );
    vi.advanceTimersByTime(499);
    expect(document.querySelector(".kpress-tooltip")).toBe(bridgeTooltip);

    vi.advanceTimersByTime(1);
    vi.advanceTimersByTime(700);
    expect(document.querySelector(".kpress-tooltip")).toBeNull();
  });

  it("does not cancel a pending tooltip hide when a broken hash link is hovered", async () => {
    vi.useFakeTimers();
    document.body.innerHTML = `
      <p><a href="#target">Target</a> <a href="#missing">Missing</a></p>
      <h2 id="target">Target Heading</h2>
      <p>Nearby preview text.</p>
    `;

    await importFresh("tooltips.js");

    const trigger = document.querySelector('a[href="#target"]');
    trigger?.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
    vi.advanceTimersByTime(500);
    const tooltip = document.querySelector(".kpress-tooltip");
    expect(tooltip?.textContent).toContain("Target Heading");

    trigger?.dispatchEvent(new MouseEvent("mouseleave", { bubbles: true }));
    document
      .querySelector('a[href="#missing"]')
      ?.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));

    vi.advanceTimersByTime(2500);
    vi.advanceTimersByTime(700);

    expect(document.querySelector(".kpress-tooltip")).toBeNull();
  });

  it("marks numeric table cells for styling and alignment", async () => {
    document.body.innerHTML = `
      <article class="kpress-prose">
        <table><tbody><tr><td>42.5</td><td>Text</td></tr></tbody></table>
      </article>
    `;

    const { initKpressTables } = await importFresh("tables.js");
    initKpressTables();

    const cells = document.querySelectorAll("td");
    expect(cells[0]?.getAttribute("data-kpress-numeric")).toBe("true");
    expect(cells[1]?.hasAttribute("data-kpress-numeric")).toBe(false);
  });

  it("scopes numeric marking to whole columns, accepting the typographic minus", async () => {
    document.body.innerHTML = `
      <article class="kpress-prose">
        <table>
          <thead><tr><th>Metric</th><th>Change</th><th>Mixed</th></tr></thead>
          <tbody>
            <tr><td>Revenue</td><td>−35%</td><td>12</td></tr>
            <tr><td>Margin</td><td>+45%</td><td>n/a</td></tr>
          </tbody>
        </table>
      </article>
    `;

    const { initKpressTables } = await importFresh("tables.js");
    initKpressTables();

    const marked = [...document.querySelectorAll("[data-kpress-numeric='true']")].map(
      (cell) => cell.textContent,
    );
    // The Change column aligns as one unit, header included; the Mixed column
    // (numbers and text) gets no marks at all.
    expect(marked).toEqual(["Change", "−35%", "+45%"]);
  });

  it("clears stale numeric marks and skips tables with row or column spans", async () => {
    document.body.innerHTML = `
      <article class="kpress-prose">
        <table>
          <tbody>
            <tr><td data-kpress-numeric="true">stale text</td><td>1</td></tr>
            <tr><td>more text</td><td></td></tr>
          </tbody>
        </table>
        <table id="span">
          <tbody>
            <tr><td rowspan="2">42</td><td>7</td></tr>
            <tr><td>8</td></tr>
          </tbody>
        </table>
      </article>
    `;

    const { initKpressTables } = await importFresh("tables.js");
    initKpressTables();

    const [first, span] = document.querySelectorAll("table");
    // Re-running converges: the stale mark on a text cell is removed, the numeric
    // column is marked, and its empty cell is marked with the column.
    const firstMarks = [...first.querySelectorAll("td")].map((cell) =>
      cell.hasAttribute("data-kpress-numeric"),
    );
    expect(firstMarks).toEqual([false, true, false, true]);
    // Spans shift cell positions, so span tables get no numeric marks.
    expect(span.querySelector("[data-kpress-numeric]")).toBeNull();
  });

  it("switches tab panels through ARIA-selected tabs", async () => {
    document.body.innerHTML = `
      <section data-kpress-tabs>
        <button role="tab" aria-selected="true" aria-controls="panel-a">A</button>
        <button role="tab" aria-selected="false" aria-controls="panel-b">B</button>
        <div id="panel-a" class="kpress-tab-panel">Alpha</div>
        <div id="panel-b" class="kpress-tab-panel" hidden>Beta</div>
      </section>
    `;

    await importFresh("tabs.js");

    const tabs = document.querySelectorAll("[role='tab']");
    const panelA = document.querySelector("#panel-a");
    const panelB = document.querySelector("#panel-b");
    tabs[1]?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(tabs[0]?.getAttribute("aria-selected")).toBe("false");
    expect(tabs[1]?.getAttribute("aria-selected")).toBe("true");
    expect(panelA?.hidden).toBe(true);
    expect(panelB?.hidden).toBe(false);
  });

  it("hydrates authored tab panels into an ARIA tablist", async () => {
    document.body.innerHTML = `
      <section class="kpress-tabs" data-kpress-tabs>
        <section class="kpress-tab-panel" data-kpress-tab-title="Overview">Alpha</section>
        <section class="kpress-tab-panel" data-kpress-tab-title="Details">Beta</section>
      </section>
    `;

    await importFresh("tabs.js");

    const tabList = document.querySelector("[role='tablist']");
    const tabs = document.querySelectorAll("[role='tab']");
    const panels = document.querySelectorAll(".kpress-tab-panel");
    expect(tabList?.classList.contains("kpress-tab-list")).toBe(true);
    expect(tabs).toHaveLength(2);
    expect(tabs[0]?.textContent).toBe("Overview");
    expect(tabs[0]?.getAttribute("aria-selected")).toBe("true");
    expect(tabs[1]?.getAttribute("tabindex")).toBe("-1");
    expect(panels[0]?.getAttribute("role")).toBe("tabpanel");
    expect(panels[0]?.hidden).toBe(false);
    expect(panels[1]?.hidden).toBe(true);

    tabs[1]?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(tabs[1]?.getAttribute("aria-selected")).toBe("true");
    expect(panels[0]?.hidden).toBe(true);
    expect(panels[1]?.hidden).toBe(false);
  });

  it("adds copy controls without duplicating existing buttons", async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    document.body.innerHTML = `<pre class="kpress-code"><code>const answer = 42;</code></pre>`;

    const { initKpressCodeCopy } = await importFresh("code-copy.js");
    initKpressCodeCopy();

    const buttons = document.querySelectorAll(".kpress-code-copy");
    expect(buttons).toHaveLength(1);
    expect(buttons[0]?.getAttribute("aria-live")).toBe("polite");

    buttons[0]?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await Promise.resolve();

    expect(writeText).toHaveBeenCalledWith("const answer = 42;");
    // Icon-only: state + accessible label, no visible text on the button.
    expect(buttons[0]?.textContent).toBe("");
    expect(buttons[0]?.querySelector("svg")).not.toBeNull();
    expect(buttons[0]?.getAttribute("aria-label")).toBe("Code copied");
    expect(buttons[0]?.getAttribute("data-kpress-copy-state")).toBe("copied");

    vi.advanceTimersByTime(COPY_STATE_RESET_DELAY_MS);

    expect(buttons[0]?.getAttribute("aria-label")).toBe("Copy code");
    expect(buttons[0]?.querySelector("svg")).not.toBeNull();
    expect(buttons[0]?.getAttribute("data-kpress-copy-state")).toBe("idle");
  });

  it("shows a recoverable code-copy error when clipboard access fails", async () => {
    vi.useFakeTimers();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
    });
    document.body.innerHTML = `<pre class="kpress-code"><code>const answer = 42;</code></pre>`;

    const { initKpressCodeCopy } = await importFresh("code-copy.js");
    initKpressCodeCopy();

    const button = document.querySelector(".kpress-code-copy");
    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await Promise.resolve();
    await Promise.resolve();

    expect(button?.textContent).toBe("");
    expect(button?.querySelector("svg")).not.toBeNull();
    expect(button?.getAttribute("aria-label")).toContain("failed");
    expect(button?.getAttribute("data-kpress-copy-state")).toBe("error");

    vi.advanceTimersByTime(COPY_STATE_RESET_DELAY_MS);

    expect(button?.getAttribute("aria-label")).toBe("Copy code");
    expect(button?.getAttribute("data-kpress-copy-state")).toBe("idle");
  });

  it("embeds a server video placeholder as an inline YouTube player on load", async () => {
    document.body.innerHTML = `
      <article class="kpress-long-text">
        <button type="button" class="kpress-video-placeholder" data-kpress-video-id="dQw4w9WgXcQ" data-kpress-video-start="42" data-kpress-video-title="Watch clip">
          <span class="kpress-video-placeholder-action" aria-hidden="true">Play</span>
        </button>
      </article>
    `;

    await importFresh("video-popover.js");

    // The placeholder is replaced by an inline player on load — no popup.
    expect(document.querySelector("[data-kpress-video-id]")).toBeNull();
    const iframe = document.querySelector("figure.kpress-video iframe.kpress-video-embed");
    expect(iframe).not.toBeNull();
    expect(iframe?.getAttribute("src")).toContain(
      "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
    );
    expect(iframe?.getAttribute("src")).toContain("start=42");
    expect(iframe?.getAttribute("title")).toBe("Watch clip");
    expect(iframe?.hasAttribute("allowfullscreen")).toBe(true);
  });

  it("embeds video placeholders injected into the DOM after load (host fragment)", async () => {
    await importFresh("video-popover.js");

    const host = document.createElement("div");
    host.innerHTML =
      '<button class="kpress-video-placeholder" data-kpress-video-id="abc123" data-kpress-video-title="Late"></button>';
    document.body.appendChild(host);

    // The MutationObserver embeds host-injected placeholders (host apps
    // inject the document fragment after this module loads).
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(host.querySelector("[data-kpress-video-id]")).toBeNull();
    const iframe = host.querySelector("figure.kpress-video iframe.kpress-video-embed");
    expect(iframe?.getAttribute("src")).toContain("https://www.youtube-nocookie.com/embed/abc123");
  });

  it("supports keyboard navigation for tabbed content", async () => {
    document.body.innerHTML = `
      <section data-kpress-tabs>
        <button role="tab" aria-selected="true" aria-controls="panel-a">A</button>
        <button role="tab" aria-selected="false" aria-controls="panel-b">B</button>
        <div id="panel-a" class="kpress-tab-panel">Alpha</div>
        <div id="panel-b" class="kpress-tab-panel" hidden>Beta</div>
      </section>
    `;

    await importFresh("tabs.js");

    const tabs = document.querySelectorAll("[role='tab']");
    tabs[0]?.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));

    expect(tabs[0]?.getAttribute("aria-selected")).toBe("false");
    expect(tabs[1]?.getAttribute("aria-selected")).toBe("true");
  });
});
