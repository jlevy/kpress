import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

const runtimePath = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../../src/kpress/format/static/katex/katex-math-runtime.js",
);
const serif = { "Main-Regular": { 49: [0, 0.712, 0, 0, 0.533] } };
const sans = { "Main-Regular": { 49: [0, 0.638, 0, 0, 0.497] } };
const original = { "Main-Regular": { 49: [0, 0.64444, 0, 0, 0.5] } };

function boot() {
  new Function(readFileSync(runtimePath, "utf8"))();
  return globalThis.kpressMathText;
}

function node() {
  document.body.innerHTML = '<article class="kpress"><span id="math"></span></article>';
  return document.getElementById("math");
}

function prepared(target) {
  target.dataset.kpressMathPrepared = "true";
  target.dataset.kpressMathSource = "1";
  target.dataset.kpressMathDisplay = "inline";
  target.dataset.kpressMathProfile = "prose";
  target.innerHTML =
    '<span class="katex"><span class="katex-html"><span style="font-family:KaTeX_Main">1</span></span></span>';
  return target.firstElementChild;
}

beforeEach(() => {
  vi.useRealTimers();
  Reflect.deleteProperty(document, "fonts");
  Reflect.deleteProperty(globalThis, "kpressMathFaceWait");
  document.documentElement.removeAttribute("data-kpress-math-text");
  document.body.innerHTML = "";
  globalThis.kpressKatexTextMetrics = { ...serif, sans, katex: original };
  globalThis.katex = {
    __setFontMetrics: vi.fn(),
    render: vi.fn((tex, target) => {
      target.innerHTML = `<span class="katex"><span class="katex-html"><span>${tex}</span></span></span>`;
    }),
  };
});

describe("the host math runtime", () => {
  it("lays out immediately without waiting for an unrelated declared face", async () => {
    const target = node();
    let releaseUnused;
    const unused = {
      family: "KaTeX_Main",
      style: "italic",
      weight: "700",
      load: vi.fn(
        () =>
          new Promise((resolveLoad) => {
            releaseUnused = resolveLoad;
          }),
      ),
    };
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: {
        forEach(callback) {
          callback(unused);
          callback({ family: "KPress Math Text" });
        },
        check: () => true,
        load: vi.fn(() => Promise.resolve([])),
      },
    });
    const rendering = boot().render("1", target);
    try {
      expect(globalThis.katex.render).toHaveBeenCalledTimes(1);
      expect(unused.load).not.toHaveBeenCalled();
      expect(await rendering).toEqual({ status: "ready" });
    } finally {
      releaseUnused?.(unused);
      await rendering;
    }
  });

  it("hydrates matching prepared markup without replacing its geometry", async () => {
    const target = node();
    const markup = prepared(target);
    await boot().hydrate("1", target);
    expect(target.firstElementChild).toBe(markup);
    expect(globalThis.katex.render).not.toHaveBeenCalled();
    expect(target.dataset.kpressMathPrepared).toBe("true");
  });

  it("keeps prepared geometry hidden until its actual glyphs load", async () => {
    const target = node();
    const markup = prepared(target);
    let release;
    const fonts = {
      forEach: (callback) => callback({ family: "KPress Math Text" }),
      check: () => false,
      load: vi.fn(
        () =>
          new Promise((resolveLoad) => {
            release = resolveLoad;
          }),
      ),
    };
    Object.defineProperty(document, "fonts", { configurable: true, value: fonts });
    const hydration = boot().hydrate("1", target);
    expect(target.style.visibility).toBe("hidden");
    expect(target.firstElementChild).toBe(markup);
    expect(fonts.load).toHaveBeenCalledTimes(1);
    expect(fonts.load.mock.calls[0][1]).toBe("1");
    release([{ family: "KaTeX_Main" }]);
    expect(await hydration).toEqual({ status: "ready" });
    expect(target.style.visibility).toBe("");
    expect(target.firstElementChild).toBe(markup);
  });

  it("cannot reveal an older hydration while a newer render waits", async () => {
    const target = node();
    prepared(target);
    const releases = [];
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: {
        forEach: (callback) => callback({ family: "KPress Math Text" }),
        check: () => false,
        load: () => new Promise((resolveLoad) => releases.push(resolveLoad)),
      },
    });
    globalThis.katex.render.mockImplementation((tex, el) => {
      el.innerHTML = `<span class="katex"><span class="katex-html"><span style="font-family:KaTeX_Main">${tex}</span></span></span>`;
    });
    const api = boot();
    const older = api.hydrate("1", target);
    const newer = api.render("2", target);
    releases[0]([{ family: "KaTeX_Main" }]);
    expect(await older).toEqual({ status: "superseded" });
    expect(target.style.visibility).toBe("hidden");
    expect(target.textContent).toBe("2");
    releases[1]([{ family: "KaTeX_Main" }]);
    expect(await newer).toEqual({ status: "ready" });
    expect(target.style.visibility).toBe("");
  });

  it("checks a print face separately after the screen face settled", async () => {
    const target = node();
    prepared(target);
    let printing = false;
    vi.spyOn(globalThis, "matchMedia").mockImplementation(() => ({ matches: printing }));
    const fonts = {
      forEach: (callback) => callback({ family: "KPress Math Text" }),
      check: () => false,
      load: vi.fn(() => Promise.resolve([{ family: "KaTeX_Main" }])),
    };
    Object.defineProperty(document, "fonts", { configurable: true, value: fonts });
    const api = boot();
    await api.hydrate("1", target);
    printing = true;
    await api.hydrate("1", target);
    expect(fonts.load).toHaveBeenCalledTimes(2);
    expect(fonts.load.mock.calls[0]).toEqual(fonts.load.mock.calls[1]);
  });

  it("rejects a prepared formula when a required font times out", async () => {
    vi.useFakeTimers();
    const target = node();
    prepared(target);
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: {
        forEach: (callback) => callback({ family: "KPress Math Text" }),
        check: () => false,
        load: () => new Promise(() => {}),
      },
    });
    const failed = expect(boot().hydrate("1", target)).rejects.toThrow(
      "required mathematics fonts are unavailable (timeout)",
    );
    await vi.advanceTimersByTimeAsync(2999);
    expect(target.style.visibility).toBe("hidden");
    await vi.advanceTimersByTimeAsync(1);
    await failed;
    expect(target.style.visibility).toBe("");
  });

  it.each([
    {
      name: "source",
      source: "2",
      displayMode: false,
      sans: false,
      stock: false,
      profile: "prose",
    },
    {
      name: "display",
      source: "1",
      displayMode: true,
      sans: false,
      stock: false,
      profile: "prose",
    },
    {
      name: "sans context",
      source: "1",
      displayMode: false,
      sans: true,
      stock: false,
      profile: "sans",
    },
    {
      name: "stock opt-out",
      source: "1",
      displayMode: false,
      sans: false,
      stock: true,
      profile: "katex",
    },
  ])("rerenders prepared markup after a $name change", async (change) => {
    const target = node();
    const markup = prepared(target);
    if (change.stock) {
      target.dataset.kpressMathText = "katex";
    }
    await boot().hydrate(
      change.source,
      target,
      { displayMode: change.displayMode },
      {
        isSansContext: () => change.sans,
      },
    );
    expect(target.firstElementChild).not.toBe(markup);
    expect(globalThis.katex.render).toHaveBeenCalledTimes(1);
    expect(target.dataset.kpressMathPrepared).toBeUndefined();
    expect(target.dataset.kpressMathSource).toBe(change.source);
    expect(target.dataset.kpressMathProfile).toBe(change.profile);
  });

  it("rerenders custom prepared markup when the composite declarations are missing", async () => {
    const target = node();
    prepared(target);
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: { forEach() {}, check: () => true, load: () => Promise.resolve([]) },
    });
    await boot().hydrate("1", target);
    expect(globalThis.katex.render).toHaveBeenCalledTimes(1);
    expect(target.dataset.kpressMathProfile).toBe("katex");
    expect(target.dataset.kpressMathPrepared).toBeUndefined();
  });

  it("initializes and renders a host node without the native enhancement loop", async () => {
    const target = node();
    const api = boot();
    await api.render("1", target, {}, { isSansContext: () => true });
    expect(globalThis.katex.render).toHaveBeenCalledTimes(1);
    expect(target.dataset.kpressMathFace).toBe("sans");
    expect(globalThis.katex.__setFontMetrics).toHaveBeenCalledWith(
      "Main-Regular",
      sans["Main-Regular"],
    );
    expect(globalThis.katex.__setFontMetrics.mock.lastCall).toEqual([
      "Main-Regular",
      serif["Main-Regular"],
    ]);
  });

  it("removes a stale sans mark when an existing node moves to prose", async () => {
    const target = node();
    target.dataset.kpressMathFace = "sans";
    await boot().render("1", target);
    expect(target.dataset.kpressMathFace).toBeUndefined();
  });

  it("restores stock metrics for an opted-out node after a custom render", async () => {
    const target = node();
    const api = boot();
    await api.render("1", target);
    target.dataset.kpressMathText = "katex";
    globalThis.katex.render.mockImplementation(() => {
      expect(globalThis.katex.__setFontMetrics.mock.lastCall).toEqual([
        "Main-Regular",
        original["Main-Regular"],
      ]);
    });
    await api.render("1", target);
  });

  it("gates an early render and keeps the latest queued update", async () => {
    const target = node();
    const loads = [];
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: {
        forEach() {},
        check: () => false,
        load: () => new Promise((resolveLoad) => loads.push(resolveLoad)),
      },
    });
    globalThis.katex.render.mockImplementation((tex, el) => {
      el.innerHTML = `<span class="katex"><span class="katex-html"><span style="font-family:KaTeX_Main">${tex}</span></span></span>`;
    });
    const api = boot();
    const first = api.render("old", target);
    const last = api.render("latest", target);
    expect(globalThis.katex.render).toHaveBeenCalledTimes(2);
    expect(target.style.visibility).toBe("hidden");
    expect(target.textContent).toBe("latest");
    for (const finish of loads) {
      finish([{ family: "KaTeX_Main" }]);
    }
    expect(await Promise.all([first, last])).toEqual([
      { status: "superseded" },
      { status: "ready" },
    ]);
    expect(target.style.visibility).toBe("");
    expect(target.textContent).toBe("latest");
  });

  it("keeps a newly used construct hidden until its own font is ready", async () => {
    const target = node();
    let releaseConstruct;
    const fonts = {
      forEach() {},
      check: (spec) => !spec.includes("KaTeX_Size2"),
      load: vi.fn((spec) =>
        spec.includes("KaTeX_Size2")
          ? new Promise((resolveLoad) => {
              releaseConstruct = resolveLoad;
            })
          : Promise.resolve([]),
      ),
    };
    Object.defineProperty(document, "fonts", { configurable: true, value: fonts });
    globalThis.katex.render.mockImplementation((_tex, el) => {
      el.innerHTML =
        '<span class="katex"><span class="katex-html"><span style="font-family:KaTeX_Size2;font-size:20px">∑</span></span></span>';
    });
    const rendering = boot().render("sum", target);
    await vi.waitFor(() => expect(releaseConstruct).toBeTypeOf("function"));
    expect(target.style.visibility).toBe("hidden");
    releaseConstruct([{ family: "KaTeX_Size2", style: "normal", weight: "400" }]);
    await rendering;
    expect(target.style.visibility).toBe("");
    expect(fonts.load.mock.calls.some(([spec]) => spec.includes("KaTeX_AMS"))).toBe(false);
  });

  it("rejects an unavailable required face and releases the hidden node", async () => {
    const target = node();
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: {
        forEach() {},
        check: () => false,
        load: (spec) =>
          spec.includes("KaTeX_Size2")
            ? Promise.reject(new Error("broken font"))
            : Promise.resolve([]),
      },
    });
    globalThis.katex.render.mockImplementation((_tex, el) => {
      el.innerHTML =
        '<span class="katex"><span class="katex-html"><span style="font-family:KaTeX_Size2">∑</span></span></span>';
    });
    await expect(boot().render("sum", target)).rejects.toThrow("required mathematics fonts");
    expect(target.style.visibility).toBe("");
    expect(target.dataset.kpressMathPending).toBeUndefined();
  });

  it("selects stock metrics when no composite family is declared", async () => {
    const target = node();
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: { forEach() {}, check: () => true, load: () => Promise.resolve([]) },
    });
    globalThis.katex.render.mockImplementation(() => {
      expect(globalThis.katex.__setFontMetrics.mock.lastCall).toEqual([
        "Main-Regular",
        original["Main-Regular"],
      ]);
    });
    await boot().render("1", target);
    expect(target.dataset.kpressMathFace).toBe("katex");
  });

  it("preserves experimental defaults when the entire document explicitly opts out", async () => {
    const target = node();
    document.documentElement.dataset.kpressMathText = "katex";
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: { forEach() {}, check: () => true, load: () => Promise.resolve([]) },
    });
    await boot().render("1", target);
    expect(globalThis.katex.__setFontMetrics).not.toHaveBeenCalled();
    expect(globalThis.katex.render).toHaveBeenCalledTimes(1);
  });

  it("rejects a fallback without stock tables instead of rendering with custom metrics", async () => {
    const target = node();
    Reflect.deleteProperty(globalThis.kpressKatexTextMetrics, "katex");
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: { forEach() {}, check: () => true, load: () => Promise.resolve([]) },
    });
    await expect(boot().render("1", target)).rejects.toThrow(
      "selected mathematics font metrics are unavailable",
    );
    expect(globalThis.katex.render).not.toHaveBeenCalled();
    expect(target.style.visibility).toBe("");
  });
});
