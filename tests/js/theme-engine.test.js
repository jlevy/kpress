import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it } from "vitest";

// theme.js imports "./runtime.js" WITHOUT a cache-busting query, so the engine
// binds to this exact module instance: import it statically to share it, and
// reset its adapter between tests.
import { storage as sharedStorage } from "../../src/kpress/format/static/js/runtime.js";

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function stubMatchMedia(prefersDark) {
  globalThis.matchMedia = (query) => ({
    matches: prefersDark && query.includes("dark"),
    media: query,
    onchange: null,
    addEventListener() {},
    removeEventListener() {},
    addListener() {},
    removeListener() {},
    dispatchEvent() {
      return true;
    },
  });
}

beforeEach(async () => {
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-kpress-theme");
  document.documentElement.removeAttribute("data-kpress-resolved-theme");
  document.documentElement.removeAttribute("data-kpress-prose-font");
  document.documentElement.removeAttribute("data-kpress-font-set");
  localStorage.clear();
  delete globalThis.kpress;
  stubMatchMedia(false);
  sharedStorage.use({
    get: (key) => localStorage.getItem(key),
    set: (key, value) => localStorage.setItem(key, value),
  });
});

describe("theme engine (kpress.theme)", () => {
  it("attaches the engine namespace onto the kpress global", async () => {
    await importFresh("runtime.js");
    await importFresh("theme.js");

    const theme = globalThis.kpress.theme;
    expect(typeof theme.set).toBe("function");
    expect(typeof theme.mode).toBe("function");
    expect(typeof theme.resolved).toBe("function");
    expect(typeof theme.onChange).toBe("function");

    theme.set("dark");
    expect(theme.mode()).toBe("dark");
    expect(theme.resolved()).toBe("dark");
    expect(document.documentElement.dataset.kpressTheme).toBe("dark");
  });

  it("persists through the runtime storage adapter, not raw localStorage", async () => {
    const remembered = new Map();
    sharedStorage.use({
      get: (key) => remembered.get(key) ?? null,
      set: (key, value) => remembered.set(key, value),
    });

    const { setKpressTheme } = await importFresh("theme.js");
    setKpressTheme("light");

    expect(remembered.get("kpress.theme")).toBe("light");
    expect(localStorage.getItem("kpress.theme")).toBeNull();
  });

  it("notifies change listeners with mode and resolved theme", async () => {
    await importFresh("runtime.js");
    const { setKpressTheme } = await importFresh("theme.js");

    const seen = [];
    globalThis.kpress.theme.onChange((detail) => seen.push(detail));
    setKpressTheme("dark");

    expect(seen.at(-1)).toEqual({ mode: "dark", resolved: "dark" });
  });
});

describe("pre-paint bootstrap", () => {
  function runBootstrap() {
    // vitest runs from the repo root; the bootstrap is a plain IIFE inlined
    // into <head>, so evaluate its source the way the page would.
    const source = readFileSync("src/kpress/format/static/js/theme-bootstrap.js", "utf-8");
    new Function(source)();
  }

  it("applies all persisted reader-preference attrs before first paint", async () => {
    localStorage.setItem("kpress.theme", "dark");
    localStorage.setItem("kpress.proseFont", "sans");
    localStorage.setItem("kpress.fontSet", "system");

    runBootstrap();

    const root = document.documentElement;
    expect(root.dataset.kpressTheme).toBe("dark");
    expect(root.dataset.kpressResolvedTheme).toBe("dark");
    expect(root.dataset.kpressProseFont).toBe("sans");
    expect(root.dataset.kpressFontSet).toBe("system");
  });

  it("leaves preference attrs unset when nothing is persisted", async () => {
    runBootstrap();

    const root = document.documentElement;
    expect(root.dataset.kpressTheme).toBe("system");
    expect(root.dataset.kpressProseFont).toBeUndefined();
    expect(root.dataset.kpressFontSet).toBeUndefined();
  });
});
