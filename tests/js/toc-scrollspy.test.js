import { afterEach, beforeEach, describe, expect, it } from "vitest";

let importCounter = 0;
let intersectionObserverDescriptor;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function nextFrame() {
  return new Promise((resolve) => requestAnimationFrame(resolve));
}

function scrollspyMarkup(hrefs = ["#intro", "#design", "#implementation"]) {
  document.body.innerHTML = `
    <main data-kpress-viewport>
      <div class="kpress-content-with-toc">
        <button data-kpress-toc-toggle aria-expanded="false">Contents</button>
        <nav data-kpress-toc>
          <ol>
            ${hrefs.map((href, index) => `<li><a href="${href}">Section ${index + 1}</a></li>`).join("")}
          </ol>
        </nav>
        <div class="kpress-long-text">
          <h2 id="intro">Intro</h2>
          <h2 id="design">Design</h2>
          <h2 id="implementation">Implementation</h2>
        </div>
      </div>
    </main>
  `;
  const viewport = document.querySelector("[data-kpress-viewport]");
  const headingOffsets = new Map([
    ["intro", 0],
    ["design", 600],
    ["implementation", 1_200],
  ]);
  let geometryReads = 0;
  Object.defineProperty(viewport, "clientHeight", { configurable: true, value: 800 });
  viewport.getBoundingClientRect = () => ({
    bottom: 900,
    height: 800,
    left: 0,
    right: 1_200,
    top: 100,
    width: 1_200,
    x: 0,
    y: 100,
  });
  for (const heading of document.querySelectorAll("h2")) {
    heading.getBoundingClientRect = () => {
      geometryReads += 1;
      return {
        bottom: 0,
        height: 40,
        left: 0,
        right: 800,
        top: 100 + headingOffsets.get(heading.id) - viewport.scrollTop,
        width: 800,
        x: 0,
        y: 0,
      };
    };
  }
  return { geometryReads: () => geometryReads, viewport };
}

function activeHref() {
  return document.querySelector('[data-kpress-toc] a[data-active="true"]')?.getAttribute("href");
}

beforeEach(() => {
  document.body.innerHTML = "";
  intersectionObserverDescriptor = Object.getOwnPropertyDescriptor(
    globalThis,
    "IntersectionObserver",
  );
  Reflect.deleteProperty(globalThis, "IntersectionObserver");
});

afterEach(() => {
  if (intersectionObserverDescriptor) {
    Object.defineProperty(globalThis, "IntersectionObserver", intersectionObserverDescriptor);
  } else {
    Reflect.deleteProperty(globalThis, "IntersectionObserver");
  }
});

describe("TOC scrollspy", () => {
  it("tracks the reading position without IntersectionObserver and disposes cleanly", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    const { geometryReads, viewport } = scrollspyMarkup();
    const dispose = initKpressToc(document);

    await nextFrame();
    expect(activeHref()).toBe("#intro");

    viewport.scrollTop = 650;
    viewport.dispatchEvent(new Event("scroll"));
    await nextFrame();
    expect(activeHref()).toBe("#design");

    viewport.scrollTop = 1_300;
    viewport.dispatchEvent(new Event("scroll"));
    viewport.dispatchEvent(new Event("scroll"));
    viewport.dispatchEvent(new Event("scroll"));
    const readsBeforeFrame = geometryReads();
    await nextFrame();
    expect(activeHref()).toBe("#implementation");
    expect(geometryReads() - readsBeforeFrame).toBeLessThanOrEqual(2);

    dispose();
    expect(document.querySelector("[data-kpress-toc]")?.hasAttribute("data-kpress-toc-bound")).toBe(
      false,
    );

    viewport.scrollTop = 0;
    viewport.dispatchEvent(new Event("scroll"));
    await nextFrame();
    expect(activeHref()).toBe("#implementation");
  });

  it("uses the fallback when a host declares IntersectionObserver without implementing it", async () => {
    Object.defineProperty(globalThis, "IntersectionObserver", {
      configurable: true,
      value: undefined,
    });
    const { initKpressToc } = await importFresh("toc.js");
    scrollspyMarkup();
    const dispose = initKpressToc(document);

    expect(activeHref()).toBe("#intro");
    dispose();
  });

  it("observes host-rewritten current-document links through the native scrollspy", async () => {
    /** @type {string[]} */
    const observedIds = [];
    let disconnected = false;
    class TestIntersectionObserver {
      /** @param {Element} target */
      observe(target) {
        observedIds.push(target.id);
      }

      disconnect() {
        disconnected = true;
      }
    }
    Object.defineProperty(globalThis, "IntersectionObserver", {
      configurable: true,
      value: TestIntersectionObserver,
    });
    const { initKpressToc } = await importFresh("toc.js");
    window.history.replaceState(null, "", "/reader/page.html");
    scrollspyMarkup([
      "/reader/page.html#intro",
      "/reader/page.html#design",
      "/other/page.html#implementation",
    ]);
    const dispose = initKpressToc(document);

    expect(observedIds).toEqual(["intro", "design"]);
    dispose();
    expect(disconnected).toBe(true);
  });

  it("recognizes host-rewritten links only when they still target this document", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    window.history.replaceState(null, "", "/reader/page.html");
    const { viewport } = scrollspyMarkup([
      "/reader/page.html#intro",
      "/reader/page.html#design",
      "/other/page.html#implementation",
    ]);
    const dispose = initKpressToc(document);

    await nextFrame();
    expect(activeHref()).toBe("/reader/page.html#intro");

    viewport.scrollTop = 650;
    viewport.dispatchEvent(new Event("scroll"));
    await nextFrame();
    expect(activeHref()).toBe("/reader/page.html#design");

    viewport.scrollTop = 1_300;
    viewport.dispatchEvent(new Event("scroll"));
    await nextFrame();
    expect(activeHref()).toBe("/reader/page.html#design");
    dispose();
  });

  it("ignores malformed rewritten links instead of breaking the remaining TOC", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    window.history.replaceState(null, "", "/reader/page.html");
    const { viewport } = scrollspyMarkup([
      "https://[invalid/#intro",
      "#bad%encoding",
      "/reader/page.html#implementation",
    ]);
    const dispose = initKpressToc(document);

    viewport.scrollTop = 1_300;
    viewport.dispatchEvent(new Event("scroll"));
    await nextFrame();
    expect(activeHref()).toBe("/reader/page.html#implementation");
    dispose();
  });
});
