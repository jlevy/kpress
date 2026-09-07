import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

// katex-init.js is a classic deferred <script>, not an ESM module (it runs after
// the UMD KaTeX globals and must not carry an `export`). It cannot be imported,
// so it is evaluated the way the browser evaluates it: as a function body over
// the page globals. The trailing `return` hands back the script's own top-level
// functions so a test can drive them directly, and each evaluation gets a fresh
// scope -- which is also how the once-only metrics flag is tested.
// Resolved through node:path, not the global URL: the happy-dom environment
// replaces `URL` with its own class, which fileURLToPath does not accept.
const SCRIPT_PATH = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../../src/kpress/format/static/katex/katex-init.js",
);

function runInitScript() {
  const source = readFileSync(SCRIPT_PATH, "utf8");
  return new Function(`${source}\nreturn { enhanceMath, applyTextMetrics };`)();
}

const METRICS = {
  "Main-Regular": { 48: [0, 0.64444, 0, 0, 0.53299] },
  "Main-Bold": { 48: [0, 0.64444, 0, 0, 0.5748] },
  "Math-Italic": { 97: [0, 0.43056, 0, 0, 0.52859] },
  scale: { "Main-Regular": 1.025, "Math-Italic": 1.15 },
};

const FACES = ["Main-Regular", "Main-Bold", "Math-Italic"];

const MATH = `
  <span class="kpress-math kpress-math-inline" data-kpress-math="inline">
    <span class="kpress-math-render">\\(x^2\\)</span>
  </span>`;

function mountMath({ fonts = "custom", wrapper = "" } = {}) {
  document.body.innerHTML = `
    <div ${wrapper}>
      <article class="kpress" data-kpress-fonts="${fonts}">${MATH}</article>
    </div>`;
}

function mathNodes() {
  return document.querySelectorAll(".kpress-math-render");
}

beforeEach(() => {
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-kpress-math-text");
  document.documentElement.removeAttribute("data-kpress-font-set");
  globalThis.kpressKatexTextMetrics = METRICS;
  globalThis.katex = { __setFontMetrics: vi.fn() };
  globalThis.renderMathInElement = vi.fn();
  vi.spyOn(console, "warn").mockImplementation(() => {});
});

describe("katex-init.js math text metrics", () => {
  it("installs every face table before the first render", () => {
    mountMath();

    runInitScript();

    const setFontMetrics = globalThis.katex.__setFontMetrics;
    const render = globalThis.renderMathInElement;
    expect(setFontMetrics).toHaveBeenCalledTimes(FACES.length);
    expect(setFontMetrics.mock.calls.map((call) => call[0]).sort()).toEqual([...FACES].sort());
    // `scale` belongs to the stylesheet's size-adjust, not to KaTeX.
    expect(setFontMetrics.mock.calls.map((call) => call[0])).not.toContain("scale");
    expect(setFontMetrics).toHaveBeenCalledWith("Main-Regular", METRICS["Main-Regular"]);
    expect(render).toHaveBeenCalledTimes(1);
    expect(Math.max(...setFontMetrics.mock.invocationCallOrder)).toBeLessThan(
      render.mock.invocationCallOrder[0],
    );
    expect(document.querySelector("[data-kpress-math]").dataset.kpressMathRendered).toBe("true");
    expect(document.documentElement.dataset.kpressMathText).toBeUndefined();
  });

  it("applies the tables once even when the script is driven again", () => {
    mountMath();

    const script = runInitScript();
    script.enhanceMath();
    script.applyTextMetrics(mathNodes());

    expect(globalThis.katex.__setFontMetrics).toHaveBeenCalledTimes(FACES.length);
  });

  it("leaves KaTeX's own metrics alone when the document opts out", () => {
    document.documentElement.dataset.kpressMathText = "katex";
    mountMath();

    runInitScript();

    expect(globalThis.katex.__setFontMetrics).not.toHaveBeenCalled();
    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
  });

  it("honours the opt-out on any ancestor, as the stylesheet does", () => {
    mountMath({ wrapper: 'data-kpress-math-text="katex"' });

    runInitScript();

    expect(globalThis.katex.__setFontMetrics).not.toHaveBeenCalled();
    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
  });

  it("leaves them alone in system font mode, where no reading face is loaded", () => {
    mountMath({ fonts: "system" });

    runInitScript();

    expect(globalThis.katex.__setFontMetrics).not.toHaveBeenCalled();
  });

  it("leaves them alone under the reader's persisted system font set", () => {
    document.documentElement.dataset.kpressFontSet = "system";
    mountMath();

    runInitScript();

    expect(globalThis.katex.__setFontMetrics).not.toHaveBeenCalled();
    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
  });

  it("turns the face off when the tables cannot be applied", () => {
    // Faces without metrics is the state the design forbids: the stylesheet reads
    // the stamped opt-out and restores KaTeX's own faces, and the page says why.
    globalThis.kpressKatexTextMetrics = undefined;
    mountMath();

    runInitScript();

    expect(globalThis.katex.__setFontMetrics).not.toHaveBeenCalled();
    expect(document.documentElement.dataset.kpressMathText).toBe("katex");
    expect(console.warn).toHaveBeenCalledTimes(1);
    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
  });

  it("turns the face off when KaTeX no longer exposes the setter", () => {
    globalThis.katex = {};
    mountMath();

    runInitScript();

    expect(document.documentElement.dataset.kpressMathText).toBe("katex");
    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
  });
});
