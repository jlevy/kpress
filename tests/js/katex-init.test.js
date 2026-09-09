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
  const source =
    readFileSync(resolve(dirname(SCRIPT_PATH), "katex-math-runtime.js"), "utf8") +
    "\n" +
    readFileSync(SCRIPT_PATH, "utf8");
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
    scale: { "Main-Regular": 0.96, "Math-Italic": 1.102 },
    fonts: [
      "410 1em 'KPress Math Text Sans'",
      "italic 410 1em 'KPress Math Text Sans'",
      "650 1em 'KPress Math Text Sans'",
      "italic 650 1em 'KPress Math Text Sans'",
    ],
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

// Which set was installed when the n-th render ran, over EVERY face rather than one of
// them. `__setFontMetrics` replaces one table per call, so what matters is the last table
// handed over for each face before the render; a set is installed only when they all came
// from the same one. Watching `Main-Regular` alone -- which this helper used to do --
// called a half-installed state "sans" and would have passed a sans render whose
// `Math-Italic` was still the serif table, which is Source Sans letters on PT Serif
// boxes, the one state the design forbids. A mixed result is returned as the per-face
// list so the failure names the face that was left behind.
function setInstalledForRender(index) {
  const installs = globalThis.katex.__setFontMetrics.mock;
  const renderedAt = globalThis.renderMathInElement.mock.invocationCallOrder[index];
  /** @type {Record<string, unknown>} */
  const installed = {};
  installs.calls.forEach(([face, table], call) => {
    if (installs.invocationCallOrder[call] < renderedAt) {
      installed[face] = table;
    }
  });
  const sets = FACES.map((face) => {
    if (installed[face] === METRICS.sans[face]) {
      return "sans";
    }
    return installed[face] === METRICS[face] ? "prose" : `${face}:none`;
  });
  return sets.every((set) => set === sets[0]) ? sets[0] : sets.join(",");
}

/** The mark katex-init.js stamps, read off the n-th math node. */
function markOf(index) {
  return mathNodes()[index].dataset.kpressMathFace;
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
  ["KPress Math Text Sans", "normal", "400"],
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

  it("marks the caption node for the stylesheet and leaves the prose node unmarked", () => {
    // The mark is what katex-text-face.css draws the sans composite on, so it and the
    // table set have to come out of the same decision. Absence is what "serif" means.
    mountProseAndCaption();

    runInitScript();

    expect(markOf(0)).toBeUndefined();
    expect(markOf(1)).toBe("sans");
  });

  it("marks every node under the reader's sans reading face", () => {
    // The reading face used to be a CSS scope of its own, seven more rules. It is the
    // last entry of SANS_CONTEXT instead, so the mark already covers it.
    mountProseAndCaption({ wrapper: 'data-kpress-prose-font="sans"' });

    runInitScript();

    expect(markOf(0)).toBe("sans");
    expect(markOf(1)).toBe("sans");
  });

  it("marks nothing when the tables are not ours to install", () => {
    // Face without metrics is the forbidden state, and a mark without metrics is the
    // same thing said in CSS: it would draw Source Sans over Computer Modern's numbers.
    globalThis.kpressKatexTextMetrics = undefined;
    mountProseAndCaption();

    runInitScript();

    expect(markOf(0)).toBeUndefined();
    expect(markOf(1)).toBeUndefined();
  });

  it("gives a host one call that installs the tables and marks the node together", () => {
    // The documented re-render path: a host that calls katex.render after load would
    // otherwise always get the serif set, since the loop restores it, and in a caption
    // that is Source Sans drawn over PT Serif's numbers on a path the ops doc invites.
    mountProseAndCaption();

    runInitScript();
    globalThis.katex.__setFontMetrics.mockClear();
    const caption = mathNodes()[1];
    const installed = globalThis.kpressMathText.installTablesFor(caption);

    expect(installed).toBe("sans");
    expect(caption.dataset.kpressMathFace).toBe("sans");
    const tables = Object.fromEntries(globalThis.katex.__setFontMetrics.mock.calls);
    for (const face of FACES) {
      expect(tables[face]).toBe(METRICS.sans[face]);
    }
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

describe("explicit mathematics font warmup", () => {
  function warmMath() {
    runInitScript();
    return globalThis.kpressMathText.ready(mathNodes());
  }

  it("warms the selected composite and the KaTeX fallback faces", async () => {
    const loads = stubFontFaceSet();
    mountMath();
    const warming = warmMath();

    // Native rendering is independent of this optional batch preparation. Its
    // mock emits no glyphs, so there are no actual render-time font requests.
    expect(globalThis.renderMathInElement).toHaveBeenCalledTimes(1);
    const requests = loads.map((load) => load.request);
    expect(requests.slice(0, KATEX_REQUESTS.length)).toEqual(KATEX_REQUESTS);
    expect(requests.join(" ")).not.toContain("KaTeX_Size1");
    expect(requests.join(" ")).not.toContain("PT Serif");
    expect(requests.join(" ")).not.toContain("KPress Math Text|");

    const specs = loads.filter((load) => load.text !== undefined);
    expect(specs.map((load) => load.request)).toEqual([
      "400 1em 'KPress Math Text'",
      "italic 400 1em 'KPress Math Text'",
      "700 1em 'KPress Math Text'",
      "italic 700 1em 'KPress Math Text'",
    ]);
    // Reach both unicode-range halves of each composite slot.
    for (const load of specs) {
      expect(load.text).toMatch(/[a-z]/);
      expect(load.text).toMatch(/[0-9]/);
      expect(load.text).toContain("α");
      expect(load.text).toContain("Ω");
      load.settle(true);
    }
    for (const load of loads.filter((load) => load.text === undefined)) {
      load.settle(true);
    }
    expect(await warming).toEqual({ status: "ready" });
    expect(Object.values(waitRecord())).toEqual(Array(loads.length).fill("loaded"));
  });

  it("includes the sans slots when the batch has sans-role mathematics", async () => {
    const loads = stubFontFaceSet();
    mountProseAndCaption();
    const warming = warmMath();
    expect(loads.filter((load) => load.text !== undefined).map((load) => load.request)).toEqual([
      "400 1em 'KPress Math Text'",
      "italic 400 1em 'KPress Math Text'",
      "700 1em 'KPress Math Text'",
      "italic 700 1em 'KPress Math Text'",
      "410 1em 'KPress Math Text Sans'",
      "italic 410 1em 'KPress Math Text Sans'",
      "650 1em 'KPress Math Text Sans'",
      "italic 650 1em 'KPress Math Text Sans'",
    ]);
    for (const load of loads) {
      load.settle(true);
    }
    expect(await warming).toEqual({ status: "ready" });
  });

  it("warms only the sans composite under the reader's sans reading face", async () => {
    const loads = stubFontFaceSet();
    mountProseAndCaption({ wrapper: 'data-kpress-prose-font="sans"' });
    const warming = warmMath();
    expect(loads.filter((load) => load.text !== undefined).map((load) => load.request)).toEqual([
      "410 1em 'KPress Math Text Sans'",
      "italic 410 1em 'KPress Math Text Sans'",
      "650 1em 'KPress Math Text Sans'",
      "italic 650 1em 'KPress Math Text Sans'",
    ]);
    for (const load of loads) {
      load.settle(true);
    }
    await warming;
  });

  it("warms no sans slot when all mathematics is prose", async () => {
    const loads = stubFontFaceSet();
    mountMath();
    const warming = warmMath();
    expect(loads.map((load) => load.request).join(" ")).not.toContain("Text Sans");
    for (const load of loads) {
      load.settle(true);
    }
    await warming;
  });

  it("warms no composite face when the document opts out", async () => {
    document.documentElement.dataset.kpressMathText = "katex";
    const loads = stubFontFaceSet();
    mountMath();
    const warming = warmMath();
    expect(loads.map((load) => load.request)).toEqual(KATEX_REQUESTS);
    for (const load of loads) {
      load.settle(true);
    }
    await warming;
  });

  it("reports a failed optional face without undoing rendered mathematics", async () => {
    const loads = stubFontFaceSet();
    mountMath();
    const warming = warmMath();
    loads[0].settle(false);
    for (const load of loads.slice(1)) {
      load.settle(true);
    }
    expect(await warming).toEqual({ status: "error" });
    expect(waitRecord()[loads[0].request]).toBe("error");
    expect(globalThis.kpressMathFaceWait[0].detail).toContain("the face did not load");
    expect(document.querySelector("[data-kpress-math]").dataset.kpressMathRendered).toBe("true");
  });

  it("reports a timeout at the three-second ceiling", async () => {
    vi.useFakeTimers();
    const loads = stubFontFaceSet();
    mountMath();
    const warming = warmMath();
    const settled = vi.fn();
    void warming.then(settled);
    await vi.advanceTimersByTimeAsync(2999);
    expect(settled).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1);
    expect(await warming).toEqual({ status: "timeout" });
    expect(Object.values(waitRecord())).toEqual(Array(loads.length).fill("pending"));
  });

  it("reports a description that matched no face as empty", async () => {
    const loads = stubFontFaceSet();
    mountMath();
    const warming = warmMath();
    const empty = loads.find((load) => load.request === "700 1em 'KPress Math Text'");
    empty.settle(true, []);
    for (const load of loads.filter((load) => load !== empty)) {
      load.settle(true);
    }
    expect(await warming).toEqual({ status: "empty" });
    expect(waitRecord()["700 1em 'KPress Math Text'"]).toBe("empty");
    expect(waitRecord()["400 1em 'KPress Math Text'"]).toBe("loaded");
  });
});

describe("native mathematics enhancement", () => {
  it("renders straight away where there is no font loading API", () => {
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
