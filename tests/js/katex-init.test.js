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

// Two sets, as the generated asset ships them: the serif tables as the object's own face
// keys and the sans ones nested under `sans`. The digits differ because the faces do --
// PT Serif sets `0` on 0.533em and Source Sans on 0.497em -- which is what the per-node
// selection below is checked against.
const METRICS = {
  "Main-Regular": { 48: [0, 0.64444, 0, 0, 0.53299] },
  "Main-Bold": { 48: [0, 0.64444, 0, 0, 0.5748] },
  "Math-Italic": { 97: [0, 0.43056, 0, 0, 0.52859] },
  sans: {
    "Main-Regular": { 48: [0, 0.638, 0, 0, 0.497] },
    "Main-Bold": { 48: [0, 0.636, 0, 0, 0.52] },
    "Math-Italic": { 97: [0, 0.498, 0, 0, 0.525] },
    scale: { "Main-Regular": 0.966, "Math-Italic": 1.102 },
  },
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

// A prose paragraph and a caption, in that DOM order, so one page asks for both sets.
function mountProseAndCaption({ wrapper = "" } = {}) {
  document.body.innerHTML = `
    <div ${wrapper}>
      <article class="kpress" data-kpress-fonts="custom">
        <p>${MATH}</p>
        <figure><figcaption class="kpress-figcaption">${MATH}</figcaption></figure>
      </article>
    </div>`;
}

// Which set was installed when the n-th render ran: `__setFontMetrics` replaces a table
// in the KaTeX singleton, so what matters is the last table handed over before the call.
function setInstalledForRender(index) {
  const installs = globalThis.katex.__setFontMetrics.mock;
  const renderedAt = globalThis.renderMathInElement.mock.invocationCallOrder[index];
  let table = null;
  installs.calls.forEach(([face, value], call) => {
    if (face === "Main-Regular" && installs.invocationCallOrder[call] < renderedAt) {
      table = value;
    }
  });
  if (table === METRICS.sans["Main-Regular"]) {
    return "sans";
  }
  return table === METRICS["Main-Regular"] ? "prose" : null;
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

describe("katex-init.js per-node table selection", () => {
  it("lays out a caption from the sans tables and prose from the reading face's", () => {
    mountProseAndCaption();

    runInitScript();

    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(2);
    expect(setInstalledForRender(0)).toBe("prose");
    expect(setInstalledForRender(1)).toBe("sans");
  });

  it("leaves the serif set installed once the page is rendered", () => {
    // The tables outlive the loop, so a host that calls katex.render afterwards gets
    // the default rather than whichever node happened to be last.
    mountProseAndCaption();

    runInitScript();

    const installs = globalThis.katex.__setFontMetrics.mock.calls;
    const last = installs.filter(([face]) => face === "Main-Regular").at(-1);
    expect(last[1]).toBe(METRICS["Main-Regular"]);
  });

  it("uses the sans tables throughout under the reader's sans reading face", () => {
    mountProseAndCaption({ wrapper: 'data-kpress-prose-font="sans"' });

    runInitScript();

    expect(setInstalledForRender(0)).toBe("sans");
    expect(setInstalledForRender(1)).toBe("sans");
  });

  it("installs no face called `sans` or `scale`", () => {
    mountProseAndCaption();

    runInitScript();

    const faces = globalThis.katex.__setFontMetrics.mock.calls.map(([face]) => face);
    expect(faces).not.toContain("sans");
    expect(faces).not.toContain("scale");
    expect(new Set(faces)).toEqual(new Set(FACES));
  });

  it("turns the face off when only the serif tables are shipped", () => {
    // Sans faces without sans metrics is the same forbidden state as faces without
    // metrics anywhere else: Source Sans drawn, PT Serif laid out, inside every caption.
    globalThis.kpressKatexTextMetrics = { ...METRICS, sans: undefined };
    mountProseAndCaption();

    runInitScript();

    expect(globalThis.katex.__setFontMetrics).not.toHaveBeenCalled();
    expect(document.documentElement.dataset.kpressMathText).toBe("katex");
    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(2);
  });
});
