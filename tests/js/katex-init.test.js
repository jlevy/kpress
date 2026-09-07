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

// happy-dom ships no `document.fonts`, which is the script's own no-font-loading
// path: it renders straight away, exactly as it did before the wait existed. The
// tests that exercise the wait install this stub, whose promises settle only when
// the test says so, and every other test in the file runs without it.
function stubFontFaceSet() {
  /** @type {{ spec: string, text: string, settle: (ok: boolean) => void }[]} */
  const loads = [];
  const fonts = {
    load: vi.fn(
      (spec, text) =>
        new Promise((resolve, reject) => {
          loads.push({
            spec,
            text,
            settle: (ok) => (ok ? resolve([]) : reject(new Error("the face did not load"))),
          });
        }),
    ),
  };
  Object.defineProperty(document, "fonts", { value: fonts, configurable: true });
  return loads;
}

beforeEach(() => {
  document.body.innerHTML = "";
  Reflect.deleteProperty(document, "fonts");
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

describe("katex-init.js paints the mathematics once", () => {
  it("renders only once the composite and the KaTeX faces have loaded", async () => {
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    // KaTeX renders into the live DOM, so a formula typeset before its faces
    // decode is painted in the next family of the stack and repainted when the
    // reading face arrives. Nothing is typeset while the loads are pending.
    expect(globalThis.renderMathInElement).not.toHaveBeenCalled();

    const specs = loads.map((load) => load.spec);
    // The composite's four slots, and the two KaTeX families every rule in
    // katex-text-face.css names after it.
    expect(specs.filter((spec) => spec.includes("KPress Math Text"))).toHaveLength(4);
    expect(specs.filter((spec) => spec.includes("KaTeX_Main"))).toHaveLength(4);
    expect(specs.filter((spec) => spec.includes("KaTeX_Math"))).toHaveLength(2);
    // `document.fonts.load` loads a face only for a code point its
    // `unicode-range` covers, so the sample reaches both faces of every slot:
    // Latin and digits for the reading face, and Greek in both cases for the
    // KaTeX halves, whose upright slots carry the capitals alone.
    for (const load of loads) {
      expect(load.text).toMatch(/[a-z]/);
      expect(load.text).toMatch(/[0-9]/);
      expect(load.text).toContain("α");
      expect(load.text).toContain("Ω");
    }

    for (const load of loads) {
      load.settle(true);
    }

    await vi.waitFor(() => expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1));
    expect(globalThis.katex.__setFontMetrics).toHaveBeenCalledTimes(FACES.length);
  });

  it("waits for no composite face when the document opts out", async () => {
    document.documentElement.dataset.kpressMathText = "katex";
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    expect(loads).toHaveLength(6);
    expect(loads.map((load) => load.spec).join(" ")).not.toContain("KPress Math Text");

    for (const load of loads) {
      load.settle(true);
    }

    await vi.waitFor(() => expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1));
  });

  it("renders anyway when a face fails to load", async () => {
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    loads[0].settle(false);
    for (const load of loads.slice(1)) {
      load.settle(true);
    }

    await vi.waitFor(() => expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1));
  });

  it("renders straight away where there is no font loading API", () => {
    // No stub: a browser without `document.fonts` has no `font-display` either,
    // and behaves exactly as it did before the wait existed.
    mountMath();

    runInitScript();

    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
  });

  it("loads no face on a page with no mathematics", () => {
    const loads = stubFontFaceSet();

    runInitScript();

    expect(loads).toHaveLength(0);
    expect(globalThis.renderMathInElement).not.toHaveBeenCalled();
  });
});
