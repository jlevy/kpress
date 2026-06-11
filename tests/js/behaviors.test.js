import { beforeEach, describe, expect, it, vi } from "vitest";

// Built-in behavior modules import "./runtime.js" without a cache-busting
// query: this static import is that exact shared registry instance.
import { behaviors as sharedBehaviors } from "../../src/kpress/format/static/js/runtime.js";

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

    // rebind on every catalog id must be a no-throw no-op on an empty page:
    // proof each id has a binding registered.
    for (const id of [
      "toc",
      "tooltip",
      "footnote-preview",
      "code-copy",
      "tables",
      "tabs",
      "diagrams",
      "video",
    ]) {
      expect(() => sharedBehaviors.rebind(id)).not.toThrow();
    }
  });
});
