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
        check: () => true,
        load: () => new Promise((resolveLoad) => loads.push(resolveLoad)),
      },
    });
    const api = boot();
    const first = api.render("old", target);
    const last = api.render("latest", target);
    expect(globalThis.katex.render).not.toHaveBeenCalled();
    for (const finish of loads) {
      finish([]);
    }
    await Promise.all([first, last]);
    expect(globalThis.katex.render).toHaveBeenCalledTimes(1);
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
});
