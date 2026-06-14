import { beforeEach, describe, expect, it, vi } from "vitest";

// Phase 1 tooltip work: the widescreen margin presentation keyed off the real
// reading column (.kpress-prose, not the absent #main-content), first-class
// suppression (TOC/chrome + data-kpress-no-tooltip), and the small placement /
// show-delay behavior flags. See
// docs/project/specs/active/plan-2026-06-12-kpress-tooltips.md.

let importCounter = 1000;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function mockRect(rect) {
  return () => ({ x: 0, y: 0, toJSON() {}, ...rect });
}

beforeEach(() => {
  document.body.innerHTML = "";
  document.body.className = "";
  document.body.removeAttribute("style");
  vi.useRealTimers();
});

describe("KPress tooltips — Phase 1 (placement, suppression, flags)", () => {
  it("places internal-link tooltips in the margin (wide-right) beside .kpress-prose on wide screens", async () => {
    // Regression guard: this mode was dead in kpress because it keyed off an
    // absent #main-content. It must now fire off the real .kpress-prose column.
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1300 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 800 });
    document.body.innerHTML = `
      <div class="kpress-prose">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Nearby preview text.</p>
      </div>
    `;
    const column = document.querySelector(".kpress-prose");
    // Reading column ends at x=900; 1300 - 900 = 400px of margin >= 320 threshold.
    column.getBoundingClientRect = mockRect({
      left: 0,
      right: 900,
      top: 0,
      bottom: 600,
      width: 900,
      height: 600,
    });

    await importFresh("tooltips.js");

    const trigger = document.querySelector('a[href="#target"]');
    trigger.getBoundingClientRect = mockRect({
      left: 100,
      right: 160,
      top: 100,
      bottom: 120,
      width: 60,
      height: 20,
    });
    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));

    const tooltip = document.querySelector(".kpress-tooltip");
    expect(tooltip?.getAttribute("data-kpress-tooltip-position")).toBe("wide-right");
  });

  it("falls back to an adjacent popover when the reading column leaves no margin room", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1300 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 800 });
    document.body.innerHTML = `
      <div class="kpress-prose">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Nearby preview text.</p>
      </div>
    `;
    const column = document.querySelector(".kpress-prose");
    // Only 100px to the right of the column (< 320 threshold) -> no margin mode.
    column.getBoundingClientRect = mockRect({
      left: 0,
      right: 1200,
      top: 0,
      bottom: 600,
      width: 1200,
      height: 600,
    });

    await importFresh("tooltips.js");

    const trigger = document.querySelector('a[href="#target"]');
    trigger.getBoundingClientRect = mockRect({
      left: 100,
      right: 160,
      top: 100,
      bottom: 120,
      width: 60,
      height: 20,
    });
    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));

    const tooltip = document.querySelector(".kpress-tooltip");
    expect(tooltip?.getAttribute("data-kpress-tooltip-position")).toBe("bottom-right");
  });

  it("suppresses tooltips in the TOC, in chrome, and on data-kpress-no-tooltip — but not in body content", async () => {
    document.body.innerHTML = `
      <header class="kpress-doc-header"><a href="#target">title link</a></header>
      <nav class="kpress-toc" data-kpress-toc><a href="#target">toc link</a></nav>
      <div class="kpress-prose">
        <p><a href="#target" data-kpress-no-tooltip>opted out</a></p>
        <div data-kpress-no-tooltip><p><a href="#target">opted out via ancestor</a></p></div>
        <p><a href="#target" id="ok">normal body link</a></p>
      </div>
      <h2 id="target">Target Heading</h2>
      <p>Preview.</p>
    `;
    await importFresh("tooltips.js");

    for (const sel of [
      ".kpress-doc-header a",
      ".kpress-toc a",
      "a[data-kpress-no-tooltip]",
      "[data-kpress-no-tooltip] a",
    ]) {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
      document.querySelector(sel)?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
      expect(
        document.querySelector(".kpress-tooltip"),
        `expected no tooltip for ${sel}`,
      ).toBeNull();
    }

    document.querySelector("#ok")?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")?.textContent).toContain("Target Heading");
  });

  it("placement flag selects (margin) or skips (inline) the wide-right mode", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1300 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 800 });
    document.body.innerHTML = `
      <div class="kpress-prose">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Nearby preview text.</p>
      </div>
    `;
    const column = document.querySelector(".kpress-prose");
    column.getBoundingClientRect = mockRect({
      left: 0,
      right: 900,
      top: 0,
      bottom: 600,
      width: 900,
      height: 600,
    });

    const mod = await importFresh("tooltips.js");
    const trigger = document.querySelector('a[href="#target"]');
    trigger.getBoundingClientRect = mockRect({
      left: 100,
      right: 160,
      top: 100,
      bottom: 120,
      width: 60,
      height: 20,
    });

    // Drive the placement decision through the exported chooser so the
    // assertion is independent of runtime auto-bind/module-cache timing.
    mod.initKpressTooltips(document, { only: "link", placement: "margin" });
    expect(mod.chooseTooltipPosition(trigger)).toBe("wide-right");

    mod.initKpressTooltips(document, { only: "link", placement: "inline" });
    const inline = mod.chooseTooltipPosition(trigger);
    expect(inline).not.toBe("wide-right");
    expect(["bottom-right", "top-right"]).toContain(inline);
  });

  it("caps tooltip width to the component max instead of the full viewport", async () => {
    // Regression guard for the overflow bug: positionTooltip used to set
    // maxWidth = viewportWidth - margins, overriding the CSS 20rem cap and letting
    // the tooltip grow to its max-content width, running off the right edge.
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 800 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
    document.body.innerHTML = `
      <div class="kpress-prose">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>A long preview paragraph so the tooltip would grow wide if uncapped.</p>
      </div>
    `;
    await importFresh("tooltips.js");
    const trigger = document.querySelector('a[href="#target"]');
    trigger.getBoundingClientRect = mockRect({
      left: 100,
      right: 160,
      top: 100,
      bottom: 120,
      width: 60,
      height: 20,
    });
    trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    const tooltip = document.querySelector(".kpress-tooltip");
    // 20rem cap (320px), not the ~780px the old full-viewport override allowed.
    expect(tooltip?.style.maxWidth).toBe("320px");
  });
});
