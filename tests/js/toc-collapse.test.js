import { beforeEach, describe, expect, it } from "vitest";

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

/**
 * Server-shaped collapsible TOC: depth 1, a pre-spine head entry (possible
 * after depth normalization), two spine groups (A with two deeper entries —
 * one of them a skipped level — and B with one), mirroring _render_toc.
 */
function collapsibleTocMarkup({
  depthAttr = ' data-kpress-toc-collapse-depth="1"',
  extra = "",
} = {}) {
  document.body.innerHTML = `
    <div class="kpress-content-with-toc">
      <button class="kpress-toc-toggle" type="button" data-kpress-toc-toggle aria-expanded="false">
        <svg></svg>
      </button>
      <div class="kpress-toc-backdrop" data-kpress-toc-backdrop aria-hidden="true"></div>
      <nav class="kpress-toc" data-kpress-toc${depthAttr}${extra}>
        <div class="kpress-toc-header">
          <a href="#" class="kpress-toc-title toc-link toc-title" data-kpress-toc-top>Contents</a>
          <button class="kpress-toc-expand-all" type="button" data-kpress-toc-expand-all
                  aria-expanded="false" aria-label="Expand all sections"><svg></svg><svg></svg></button>
        </div>
        <ol class="toc-list">
          <li class="kpress-toc-level-2 toc-h2"><a class="toc-link" href="#pre">Pre</a></li>
          <li class="kpress-toc-level-1 toc-h1"><a class="toc-link" href="#a">A</a></li>
          <li class="kpress-toc-level-2 toc-h2"><a class="toc-link" href="#a1">A1</a></li>
          <li class="kpress-toc-level-3 toc-h3"><a class="toc-link" href="#a2">A2</a></li>
          <li class="kpress-toc-level-1 toc-h1"><a class="toc-link" href="#b">B</a></li>
          <li class="kpress-toc-level-2 toc-h2"><a class="toc-link" href="#b1">B1</a></li>
        </ol>
      </nav>
      <div class="kpress-long-text">
        <h2 id="pre">Pre</h2>
        <h2 id="a">A</h2><h3 id="a1">A1</h3><h4 id="a2">A2</h4>
        <h2 id="b">B</h2><h3 id="b1">B1</h3>
      </div>
    </div>
  `;
}

function rowFor(href) {
  const link = document.querySelector(`.toc-list a[href="${href}"]`);
  return link ? link.closest("li") : null;
}

function isCollapsed(href) {
  return rowFor(href)?.classList.contains("kpress-toc-collapsed") ?? false;
}

function clickLink(href) {
  document
    .querySelector(`.toc-list a[href="${href}"]`)
    ?.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
}

function expandAllButton() {
  return document.querySelector("[data-kpress-toc-expand-all]");
}

beforeEach(() => {
  document.body.innerHTML = "";
});

describe("collapsible TOC", () => {
  it("starts with deep entries collapsed, spine and pre-spine head visible", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    collapsibleTocMarkup();
    initKpressToc(document);

    expect(isCollapsed("#a")).toBe(false);
    expect(isCollapsed("#b")).toBe(false);
    // Entries before the first spine entry form a head group, always visible.
    expect(isCollapsed("#pre")).toBe(false);
    expect(isCollapsed("#a1")).toBe(true);
    expect(isCollapsed("#a2")).toBe(true);
    expect(isCollapsed("#b1")).toBe(true);
  });

  it("expand-all shows every entry, flips ARIA state, and re-collapses", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    collapsibleTocMarkup();
    initKpressToc(document);
    const button = expandAllButton();

    button.click();
    expect(button.getAttribute("aria-expanded")).toBe("true");
    expect(button.getAttribute("aria-label")).toBe("Collapse all sections");
    expect(isCollapsed("#a1")).toBe(false);
    expect(isCollapsed("#a2")).toBe(false);
    expect(isCollapsed("#b1")).toBe(false);

    button.click();
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(button.getAttribute("aria-label")).toBe("Expand all sections");
    expect(isCollapsed("#a1")).toBe(true);
    expect(isCollapsed("#b1")).toBe(true);
  });

  it("scroll-follow keeps the active group expanded and hands off between groups", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    collapsibleTocMarkup();
    initKpressToc(document);

    // Activating A (via the shared setActiveLink path) expands A's subtree only.
    clickLink("#a");
    expect(isCollapsed("#a1")).toBe(false);
    expect(isCollapsed("#a2")).toBe(false);
    expect(isCollapsed("#b1")).toBe(true);

    // Handoff: activating B collapses A's group and expands B's.
    clickLink("#b");
    expect(isCollapsed("#a1")).toBe(true);
    expect(isCollapsed("#b1")).toBe(false);

    // A deep link activates its owning group.
    clickLink("#a1");
    expect(isCollapsed("#a1")).toBe(false);
    expect(isCollapsed("#b1")).toBe(true);
  });

  it("collapse-all returns to the baseline, which still shows the active group", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    collapsibleTocMarkup();
    initKpressToc(document);
    const button = expandAllButton();

    clickLink("#b");
    button.click();
    expect(isCollapsed("#a1")).toBe(false);

    // Collapse-all: back to "active group only", not "everything hidden".
    button.click();
    expect(isCollapsed("#a1")).toBe(true);
    expect(isCollapsed("#b1")).toBe(false);
  });

  it("expandOnScroll=false (attribute) keeps groups collapsed as the active entry moves", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    collapsibleTocMarkup({ extra: ' data-kpress-toc-expand-on-scroll="false"' });
    initKpressToc(document);

    clickLink("#a");
    expect(isCollapsed("#a1")).toBe(true);

    // The global toggle still works.
    expandAllButton().click();
    expect(isCollapsed("#a1")).toBe(false);
  });

  it("JS-channel config overrides the server attributes", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    // Depth 2 via config: nothing is deeper than 2 except #a2 (level 3).
    collapsibleTocMarkup();
    initKpressToc(document, { collapseDepth: 2 });
    expect(isCollapsed("#a1")).toBe(false);
    expect(isCollapsed("#a2")).toBe(true);

    // expandOnScroll override wins over the (absent = on) attribute.
    document.body.innerHTML = "";
    collapsibleTocMarkup();
    initKpressToc(document, { expandOnScroll: false });
    clickLink("#a");
    expect(isCollapsed("#a1")).toBe(true);

    // collapseDepth: 0 disables collapse entirely.
    document.body.innerHTML = "";
    collapsibleTocMarkup();
    initKpressToc(document, { collapseDepth: 0 });
    expect(isCollapsed("#a1")).toBe(false);
    expect(isCollapsed("#a2")).toBe(false);
  });

  it("without the attribute or config, no entry is ever collapsed", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    collapsibleTocMarkup({ depthAttr: "" });
    initKpressToc(document);
    expect(isCollapsed("#a1")).toBe(false);
    expect(isCollapsed("#b1")).toBe(false);
  });

  it("dispose removes collapsed classes and the expand-all listener", async () => {
    const { initKpressToc } = await importFresh("toc.js");
    collapsibleTocMarkup();
    const dispose = initKpressToc(document);
    expect(isCollapsed("#a1")).toBe(true);

    dispose();
    expect(isCollapsed("#a1")).toBe(false);
    expect(document.querySelectorAll(".kpress-toc-collapsed")).toHaveLength(0);

    // The dead listener must not mutate state after teardown.
    const button = expandAllButton();
    button.click();
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(document.querySelectorAll(".kpress-toc-collapsed")).toHaveLength(0);
  });
});
