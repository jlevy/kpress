import { beforeEach, describe, expect, it } from "vitest";

// A preview is a CLONE of already-rendered math, mounted OUTSIDE the `.kpress`
// wrapper it came from — on the viewport pane, or on the body. The metric tables
// KaTeX was typeset from are one page-global setting, so the overlay has to be
// drawn and sized in the same mode as the document or the boxes and the glyphs
// disagree. tooltips.js therefore resolves the originating wrapper's mode and
// stamps it on the overlay, and katex-text-face.css and components.css scope on
// the stamp. These tests pin the resolution, including the three opt-outs read
// on the wrapper itself — the placement `closest()` accepts and the stylesheet's
// `:not()` list must match.

let importCounter = 3000;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

/** A document with a footnote-style preview link inside a `.kpress` wrapper. */
function buildDocument() {
  document.body.innerHTML = `
    <main class="kpress-page-main kpress-viewport" data-kpress-viewport>
      <article class="kpress">
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
        <p>Preview text with \\(4 + 1\\).</p>
      </article>
    </main>
  `;
  return {
    wrapper: document.querySelector(".kpress"),
    trigger: document.querySelector('a[href="#target"]'),
  };
}

async function openPreview(trigger) {
  await importFresh("tooltips.js");
  trigger.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
  return document.querySelector(".kpress-tooltip");
}

beforeEach(() => {
  document.body.innerHTML = "";
  const root = document.documentElement;
  root.removeAttribute("data-kpress-math-text");
  root.removeAttribute("data-kpress-font-set");
  root.removeAttribute("data-kpress-fonts");
});

describe("preview overlays carry the document's math text mode", () => {
  it("stamps the reading-face mode when the wrapper has not opted out", async () => {
    const { trigger } = buildDocument();

    const tooltip = await openPreview(trigger);

    expect(tooltip?.getAttribute("data-kpress-math-text")).toBe("prose");
  });

  it("stamps KaTeX's own mode when the page shell opted out", async () => {
    document.documentElement.dataset.kpressMathText = "katex";
    const { trigger } = buildDocument();

    const tooltip = await openPreview(trigger);

    expect(tooltip?.getAttribute("data-kpress-math-text")).toBe("katex");
  });

  it("stamps KaTeX's own mode when the reader's persisted font set is system", async () => {
    document.documentElement.dataset.kpressFontSet = "system";
    const { trigger } = buildDocument();

    const tooltip = await openPreview(trigger);

    expect(tooltip?.getAttribute("data-kpress-math-text")).toBe("katex");
  });

  it("reads every opt-out on the wrapper itself, not only above it", async () => {
    // `closest()` matches the element it starts from, and the stylesheet's scope
    // excludes each attribute both bare and as an ancestor for the same reason.
    for (const [name, value] of [
      ["data-kpress-fonts", "system"],
      ["data-kpress-font-set", "system"],
      ["data-kpress-math-text", "katex"],
    ]) {
      const { wrapper, trigger } = buildDocument();
      wrapper.setAttribute(name, value);

      const tooltip = await openPreview(trigger);

      expect(tooltip?.getAttribute("data-kpress-math-text"), name).toBe("katex");
    }
  });

  it("stamps KaTeX's own mode outside any KPress document", async () => {
    document.body.innerHTML = `
      <main class="kpress-page-main kpress-viewport" data-kpress-viewport>
        <p><a href="#target">Target</a></p>
        <h2 id="target">Target Heading</h2>
      </main>
    `;

    const tooltip = await openPreview(document.querySelector('a[href="#target"]'));

    expect(tooltip?.getAttribute("data-kpress-math-text")).toBe("katex");
  });
});
