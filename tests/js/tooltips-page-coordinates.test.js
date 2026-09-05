import { beforeEach, describe, expect, it, vi } from "vitest";

// The popover's coordinate frame. A callout belongs to a place in the text, so
// it is appended inside the KPress scroller and placed in page coordinates
// (screen position + the scroller's scroll offset) — it travels with the
// paragraph that owns it. The narrow-screen sheet is the exception: it has no
// anchor to stay beside, so it stays window-fixed on the body.

let importCounter = 2000;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function mockRect(rect) {
  return () => ({ x: 0, y: 0, toJSON() {}, ...rect });
}

function setScrollTop(viewport, value) {
  Object.defineProperty(viewport, "scrollTop", { configurable: true, value });
}

/** Build a document that scrolls inside a marked pane, as the page shell does. */
function buildPaneDocument(paneRect, anchorRect) {
  document.body.innerHTML = `
    <main class="kpress-page-main kpress-viewport" data-kpress-viewport>
      <div class="kpress-prose">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Nearby preview text.</p>
      </div>
    </main>
  `;
  const viewport = document.querySelector("[data-kpress-viewport]");
  viewport.getBoundingClientRect = mockRect(paneRect);
  setScrollTop(viewport, 0);
  const trigger = document.querySelector('a[href="#target"]');
  trigger.getBoundingClientRect = mockRect(anchorRect);
  return { viewport, trigger };
}

const ANCHOR_RECT = { left: 100, right: 160, top: 100, bottom: 120, width: 60, height: 20 };

beforeEach(() => {
  document.body.innerHTML = "";
  document.body.className = "";
  document.body.removeAttribute("style");
  vi.useRealTimers();
});

describe("KPress tooltips — page coordinates", () => {
  it("mounts a callout inside the scroller and offsets it by the scroll position", async () => {
    // The anchor sits 120px down the pane in both passes, so the popover's page
    // position must differ by exactly the scroll offset: on screen it is in the
    // same place beside the same word, which is what "scrolls with the text"
    // means once the scroller is the coordinate frame.
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1000 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
    const { viewport, trigger } = buildPaneDocument(
      { left: 0, right: 1000, top: 0, bottom: 700, width: 1000, height: 700 },
      ANCHOR_RECT,
    );

    await importFresh("tooltips.js");

    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    const unscrolled = document.querySelector(".kpress-tooltip");
    expect(unscrolled?.parentElement).toBe(viewport);
    expect(unscrolled?.getAttribute("data-kpress-tooltip-position")).toBe("bottom-right");
    // anchor bottom (120) + the 10px gap, with no scroll to add.
    expect(unscrolled?.style.top).toBe("130px");
    expect(unscrolled?.style.insetInlineStart).toBe("100px");

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    setScrollTop(viewport, 500);
    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    const scrolled = document.querySelector(".kpress-tooltip");
    expect(scrolled?.parentElement).toBe(viewport);
    expect(scrolled?.getAttribute("data-kpress-tooltip-position")).toBe("bottom-right");
    expect(scrolled?.style.top).toBe("630px");
    expect(scrolled?.style.insetInlineStart).toBe("100px");
  });

  it("keeps the narrow-screen sheet on the body, in window coordinates", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 500 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
    const { viewport, trigger } = buildPaneDocument(
      { left: 0, right: 500, top: 0, bottom: 700, width: 500, height: 700 },
      ANCHOR_RECT,
    );
    setScrollTop(viewport, 500);

    await importFresh("tooltips.js");

    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    const tooltip = document.querySelector(".kpress-tooltip");
    expect(tooltip?.getAttribute("data-kpress-tooltip-position")).toBe("mobile-bottom");
    expect(tooltip?.parentElement).toBe(document.body);
    // Held against the bottom of the pane by the viewport margin, and unmoved
    // by the 500px of scroll that shifted the callout above.
    expect(tooltip?.style.bottom).toBe("10px");
    expect(tooltip?.style.top).toBe("");
  });

  it("falls back to the body when the document itself is the scroller", async () => {
    // No [data-kpress-viewport] pane: the initial containing block plus the page
    // scroll offset is the same page frame, and body is where it is anchored.
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1000 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
    Object.defineProperty(window, "pageYOffset", { configurable: true, value: 400 });
    document.body.innerHTML = `
      <div class="kpress-prose">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Nearby preview text.</p>
      </div>
    `;
    const trigger = document.querySelector('a[href="#target"]');
    trigger.getBoundingClientRect = mockRect(ANCHOR_RECT);

    await importFresh("tooltips.js");

    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    const tooltip = document.querySelector(".kpress-tooltip");
    expect(tooltip?.parentElement).toBe(document.body);
    expect(tooltip?.style.top).toBe("530px");
  });
});
