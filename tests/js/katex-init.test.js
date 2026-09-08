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

// happy-dom ships no `document.fonts`, which is the script's own no-font-loading
// path: it renders straight away, exactly as it did before the wait existed. The
// tests that exercise the wait install this stub, whose promises settle only when
// the test says so, and every other test in the file runs without it.
//
// The set holds the faces the pinned KaTeX bundle declares, plus faces the init
// must leave alone: a construct-specific KaTeX family, the prose face, and the
// composite -- which is asked for through `load()` and never face by face, so
// that a host's own `KPress Math Text` rules are what a page fetches.
const SET_FACES = [
  ["KaTeX_Main", "normal", "700"],
  ["KaTeX_Main", "italic", "700"],
  ["KaTeX_Main", "italic", "400"],
  ["KaTeX_Main", "normal", "400"],
  ["KaTeX_Math", "italic", "700"],
  ["KaTeX_Math", "italic", "400"],
  ["KaTeX_Size1", "normal", "400"],
  ["PT Serif", "normal", "400"],
  ["KPress Math Text", "normal", "400"],
];

/** The identity `katex-init.js` records a face under, and the tests name it by. */
function faceKey({ family, style, weight, unicodeRange }) {
  return [family, style, weight, unicodeRange].join("|");
}

function stubFontFaceSet() {
  /**
   * @type {{ request: string, text?: string,
   *          settle: (ok: boolean, faces?: unknown[]) => void }[]}
   */
  const loads = [];
  const faces = SET_FACES.map(([family, style, weight]) => {
    const face = { family, style, weight, unicodeRange: "U+0-10FFFF" };
    return Object.assign(face, {
      load: vi.fn(
        () =>
          new Promise((resolve, reject) => {
            loads.push({
              request: faceKey(face),
              settle: (ok) => (ok ? resolve(face) : reject(new Error("the face did not load"))),
            });
          }),
      ),
    });
  });
  const fonts = {
    forEach: (callback) => {
      for (const face of faces) {
        callback(face, face, fonts);
      }
    },
    load: vi.fn(
      (spec, text) =>
        new Promise((resolve, reject) => {
          loads.push({
            request: spec,
            text,
            settle: (ok, matched = [{ family: spec, style: "normal", weight: "400" }]) =>
              ok ? resolve(matched) : reject(new Error("the face did not load")),
          });
        }),
    ),
  };
  Object.defineProperty(document, "fonts", { value: fonts, configurable: true });
  return loads;
}

/** What `katex-init.js` recorded about the wait, keyed by request. */
function waitRecord() {
  return Object.fromEntries(
    (globalThis.kpressMathFaceWait ?? []).map((entry) => [entry.request, entry.outcome]),
  );
}

beforeEach(() => {
  // The deadline case below installs fake timers; every other case in the file
  // measures nothing and waits on real ones.
  vi.useRealTimers();
  document.body.innerHTML = "";
  Reflect.deleteProperty(document, "fonts");
  Reflect.deleteProperty(globalThis, "kpressMathFaceWait");
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

//: The KaTeX faces the init asks for by name: every face of the two families
//: katex-text-face.css names after the composite, and none of the others.
const KATEX_REQUESTS = [
  "KaTeX_Main|normal|700|U+0-10FFFF",
  "KaTeX_Main|italic|700|U+0-10FFFF",
  "KaTeX_Main|italic|400|U+0-10FFFF",
  "KaTeX_Main|normal|400|U+0-10FFFF",
  "KaTeX_Math|italic|700|U+0-10FFFF",
  "KaTeX_Math|italic|400|U+0-10FFFF",
];

describe("katex-init.js paints the mathematics once", () => {
  it("renders only once the composite and the KaTeX faces have loaded", async () => {
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    // KaTeX renders into the live DOM, so a formula typeset before its faces
    // decode is painted in the next family of the stack and repainted when the
    // reading face arrives. Nothing is typeset while the loads are pending.
    expect(globalThis.renderMathInElement).not.toHaveBeenCalled();

    const requests = loads.map((load) => load.request);
    // The two KaTeX families, face by face off `document.fonts`, so no matching
    // stands between the wait and a face the page already holds. Nothing else in
    // the set is touched: not the construct-specific families, not the prose
    // face, and not the composite, which is asked for by description below.
    expect(requests.slice(0, KATEX_REQUESTS.length)).toEqual(KATEX_REQUESTS);
    expect(requests.join(" ")).not.toContain("KaTeX_Size1");
    expect(requests.join(" ")).not.toContain("PT Serif");
    expect(requests.join(" ")).not.toContain("KPress Math Text|");

    // The composite's four slots, as descriptions, so a host that declared its
    // own faces over these gets the ones it declared.
    const specs = loads.filter((load) => load.text !== undefined);
    expect(specs.map((load) => load.request)).toEqual([
      "400 1em 'KPress Math Text'",
      "italic 400 1em 'KPress Math Text'",
      "700 1em 'KPress Math Text'",
      "italic 700 1em 'KPress Math Text'",
    ]);
    // `document.fonts.load` loads a face only for a code point its
    // `unicode-range` covers, so the sample reaches both faces of every slot:
    // Latin and digits for the reading face, and Greek in both cases for the
    // KaTeX halves, whose upright slots carry the capitals alone.
    for (const load of specs) {
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
    // The record a page's mathematics is debugged from says every request was
    // covered by a face that loaded.
    expect(Object.values(waitRecord())).toEqual(Array(loads.length).fill("loaded"));
  });

  it("waits for no composite face when the document opts out", async () => {
    document.documentElement.dataset.kpressMathText = "katex";
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    expect(loads.map((load) => load.request)).toEqual(KATEX_REQUESTS);

    for (const load of loads) {
      load.settle(true);
    }

    await vi.waitFor(() => expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1));
  });

  it("renders anyway when a face fails to load, and records which", async () => {
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    loads[0].settle(false);
    for (const load of loads.slice(1)) {
      load.settle(true);
    }

    await vi.waitFor(() => expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1));
    // A face that cannot be fetched must not take the mathematics with it, and
    // must be legible afterwards as a face the wait did not in fact cover.
    expect(waitRecord()[loads[0].request]).toBe("error");
    expect(globalThis.kpressMathFaceWait[0].detail).toContain("the face did not load");
  });

  it("renders at the three-second ceiling when the faces never settle", async () => {
    // The deadline is what stops a font that hangs from meaning no mathematics at
    // all, and it is the one branch the cases above cannot reach: they settle every
    // load. Here nothing settles, so the render can only come from the race.
    vi.useFakeTimers();
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    expect(globalThis.renderMathInElement).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(2999);
    expect(globalThis.renderMathInElement).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1);

    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
    // Late mathematics in the fallback faces, not no mathematics: the tables are
    // installed and the nodes are stamped exactly as on the settled path.
    expect(globalThis.katex.__setFontMetrics).toHaveBeenCalledTimes(FACES.length);
    expect(document.querySelector("[data-kpress-math]").dataset.kpressMathRendered).toBe("true");
    // Every request is still outstanding, and the record says so: `pending` is how a
    // page that repainted is told apart from one whose faces the wait did cover.
    expect(Object.values(waitRecord())).toEqual(Array(loads.length).fill("pending"));
  });

  it("records a request that matched no face as empty", async () => {
    // A description that matches nothing resolves with no faces, so the wait
    // bought nothing for that slot. It is not an error and must not block the
    // render, but it is the difference between a face the fix covers and one it
    // does not, so the record has to say so.
    const loads = stubFontFaceSet();
    mountMath();

    runInitScript();

    const empty = loads.find((load) => load.request === "700 1em 'KPress Math Text'");
    empty.settle(true, []);
    for (const load of loads.filter((load) => load !== empty)) {
      load.settle(true);
    }

    await vi.waitFor(() => expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1));
    expect(waitRecord()["700 1em 'KPress Math Text'"]).toBe("empty");
    expect(waitRecord()["400 1em 'KPress Math Text'"]).toBe("loaded");
  });

  it("renders straight away where there is no font loading API", () => {
    // No stub: a browser without `document.fonts` has no `font-display` either,
    // and behaves exactly as it did before the wait existed.
    mountMath();

    runInitScript();

    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
    expect(globalThis.kpressMathFaceWait).toBeUndefined();
  });

  it("loads no face on a page with no mathematics", () => {
    const loads = stubFontFaceSet();

    runInitScript();

    expect(loads).toHaveLength(0);
    expect(globalThis.renderMathInElement).not.toHaveBeenCalled();
    expect(globalThis.kpressMathFaceWait).toBeUndefined();
  });
});
