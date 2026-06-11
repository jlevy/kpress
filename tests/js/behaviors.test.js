import { beforeEach, describe, expect, it, vi } from "vitest";

// Built-in behavior modules import "./runtime.js" without a cache-busting
// query: this static import is that exact shared registry instance.
import { behaviors as sharedBehaviors } from "../../src/kpress/format/static/js/runtime.js";
// The doc's part-import mechanism: pinned exports are importable directly so a
// host can wrap one aspect of a built-in (see PUBLIC_JS_EXPORTS).
import {
  defaultTocToggleVisible,
  TOC_TOGGLE_SCROLL_THRESHOLD_PX,
} from "../../src/kpress/format/static/js/toc.js";

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function tocMarkup() {
  document.body.innerHTML = `
    <div class="kpress-content-with-toc">
      <button class="kpress-toc-toggle" type="button" data-kpress-toc-toggle aria-expanded="false">
        <svg data-default-icon="1"></svg>
      </button>
      <div class="kpress-toc-backdrop" data-kpress-toc-backdrop aria-hidden="true"></div>
      <nav data-kpress-toc>
        <ol><li><a href="#a">A</a></li></ol>
      </nav>
      <div class="kpress-long-text"><h2 id="a">A</h2></div>
    </div>
  `;
}

beforeEach(() => {
  document.body.innerHTML = "";
});

describe("behavior overrides and exported parts", () => {
  it("toc visibility policy is replaceable via callback config (always-visible)", async () => {
    await importFresh("toc.js");
    tocMarkup();

    // Default policy: hidden until scrolled past the threshold.
    sharedBehaviors.rebind("toc");
    const button = document.querySelector(".kpress-toc-toggle");
    expect(button?.classList.contains("show-toggle")).toBe(false);

    // Callback config (JS channel): always visible, no scroll needed.
    sharedBehaviors.configure("toc", { visible: () => true });
    sharedBehaviors.rebind("toc");
    expect(button?.classList.contains("show-toggle")).toBe(true);
  });

  it("toc toggle icon is replaceable via config", async () => {
    await importFresh("toc.js");
    tocMarkup();

    sharedBehaviors.configure("toc", { icon: '<svg data-custom-icon="1"></svg>' });
    sharedBehaviors.rebind("toc");

    const button = document.querySelector(".kpress-toc-toggle");
    expect(button?.querySelector("[data-custom-icon]")).toBeTruthy();
    expect(button?.querySelector("[data-default-icon]")).toBeNull();
  });

  it("the default visibility policy is an exported, wrappable part", async () => {
    const { defaultTocToggleVisible, TOC_TOGGLE_SCROLL_THRESHOLD_PX } = await importFresh("toc.js");

    expect(defaultTocToggleVisible({ scrollTop: () => 0 })).toBe(false);
    expect(defaultTocToggleVisible({ scrollTop: () => TOC_TOGGLE_SCROLL_THRESHOLD_PX + 1 })).toBe(
      true,
    );
  });

  it("footnote-preview can be overridden without touching link tooltips", async () => {
    await importFresh("tooltips.js");
    document.body.innerHTML = `
      <p><sup class="kpress-footnote-ref"><a href="#fn-x">1</a></sup>
      <a href="#section">internal</a></p>
    `;

    const hostBind = vi.fn();
    sharedBehaviors.override("footnote-preview", hostBind);
    sharedBehaviors.rebind("footnote-preview");

    expect(hostBind).toHaveBeenCalledWith(document, expect.any(Object));
    // The sibling behavior id still has its built-in binding.
    sharedBehaviors.rebind("tooltip");
  });

  it("a post-ready footnote-preview override detaches built-in handling for late anchors", async () => {
    await importFresh("tooltips.js");
    document.body.innerHTML = `
      <section class="kpress-footnotes"><ol><li id="fn-x">Footnote body</li></ol></section>
    `;

    // The built-in bound at registration (post-ready registry); the override
    // must run its disposer, so late footnote anchors are the host's alone.
    sharedBehaviors.override("footnote-preview", () => {});

    const host = document.createElement("div");
    host.innerHTML = '<sup class="kpress-footnote-ref"><a href="#fn-x" id="late-fn">1</a></sup>';
    document.body.appendChild(host);
    await new Promise((resolve) => setTimeout(resolve, 0));

    document.getElementById("late-fn")?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")).toBeNull();
  });

  it("mechanical behaviors are registered and rebind over markup (code-copy)", async () => {
    await importFresh("code-copy.js");
    document.body.innerHTML = '<pre class="kpress-code"><code>x = 1</code></pre>';

    sharedBehaviors.rebind("code-copy");

    expect(document.querySelector(".kpress-code-copy")).toBeTruthy();
  });

  it("registered behaviors cover the built-in catalog ids", async () => {
    await importFresh("toc.js");
    await importFresh("tooltips.js");
    await importFresh("code-copy.js");
    await importFresh("tables.js");
    await importFresh("tabs.js");
    await importFresh("diagrams.js");
    await importFresh("video-popover.js");
    await importFresh("theme.js");

    // rebind warns and no-ops on unknown ids, so zero warnings across the
    // catalog genuinely pins that every id has a binding registered (a
    // no-throw check would also pass for unregistered ids).
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    for (const id of [
      "toc",
      "tooltip",
      "footnote-preview",
      "code-copy",
      "tables",
      "tabs",
      "diagrams",
      "video",
      "theme",
    ]) {
      sharedBehaviors.rebind(id);
    }
    expect(warn).not.toHaveBeenCalled();
  });
});

describe("part imports (wrap one aspect)", () => {
  it("a host wraps the default TOC visibility policy via an imported part", async () => {
    await importFresh("toc.js");
    tocMarkup();
    Object.defineProperty(window, "pageYOffset", { configurable: true, value: 0 });

    // Import the pinned part, wrap it, hand the wrapper back as callback
    // config — change one aspect without forking the behavior.
    sharedBehaviors.configure("toc", {
      visible: (ctx) => !defaultTocToggleVisible(ctx),
    });
    sharedBehaviors.rebind("toc");

    const button = document.querySelector(".kpress-toc-toggle");
    // Inverted policy: visible before the scroll threshold...
    expect(button?.classList.contains("show-toggle")).toBe(true);

    // ...and hidden once scrolled past it (the wrapped default flips).
    Object.defineProperty(window, "pageYOffset", {
      configurable: true,
      value: TOC_TOGGLE_SCROLL_THRESHOLD_PX + 60,
    });
    window.dispatchEvent(new Event("scroll"));
    expect(button?.classList.contains("show-toggle")).toBe(false);
  });
});
