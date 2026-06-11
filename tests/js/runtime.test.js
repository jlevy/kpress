import { beforeEach, describe, expect, it } from "vitest";

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function setPageModel(model) {
  const script = document.createElement("script");
  script.type = "application/json";
  script.id = "kpress-page-model";
  script.textContent = JSON.stringify(model);
  document.body.appendChild(script);
}

beforeEach(() => {
  document.body.innerHTML = "";
  localStorage.clear();
  delete globalThis.kpress;
});

describe("kpress client runtime", () => {
  it("assembles the kpress global namespace", async () => {
    const runtime = await importFresh("runtime.js");

    expect(globalThis.kpress).toBeDefined();
    expect(globalThis.kpress.widgets).toBe(runtime.widgets);
    expect(globalThis.kpress.behaviors).toBe(runtime.behaviors);
    expect(globalThis.kpress.storage).toBe(runtime.storage);
    expect(typeof globalThis.kpress.on).toBe("function");
    expect(typeof globalThis.kpress.emit).toBe("function");
    expect(typeof globalThis.kpress.model).toBe("function");
  });

  it("parses the page-model block once and falls back to an empty model", async () => {
    setPageModel({ version: 1, title: "Doc", widgets: { settings: { choosers: ["theme"] } } });
    const { getModel } = await importFresh("runtime.js");

    expect(getModel().title).toBe("Doc");
    expect(getModel().widgets.settings.choosers).toEqual(["theme"]);

    document.body.innerHTML = "";
    // Cached: removing the block does not lose the model.
    expect(getModel().title).toBe("Doc");

    const fresh = await importFresh("runtime.js");
    expect(fresh.getModel().widgets).toEqual({});
  });

  it("persists through localStorage by default and honors a swapped adapter", async () => {
    const { storage } = await importFresh("runtime.js");

    storage.set("kpress.test", "value");
    expect(localStorage.getItem("kpress.test")).toBe("value");
    expect(storage.get("kpress.test")).toBe("value");

    const remembered = new Map();
    storage.use({
      get: (key) => remembered.get(key) ?? null,
      set: (key, value) => remembered.set(key, value),
    });
    storage.set("kpress.test", "cookie-value");
    expect(remembered.get("kpress.test")).toBe("cookie-value");
    expect(storage.get("kpress.test")).toBe("cookie-value");
    // The default store is untouched after the swap.
    expect(localStorage.getItem("kpress.test")).toBe("value");
  });

  it("delivers events to subscribers until they unsubscribe", async () => {
    const { on, off, emit } = await importFresh("runtime.js");
    const seen = [];
    const listener = (detail) => seen.push(detail);

    on("widget:change", listener);
    emit("widget:change", { id: "settings", key: "theme", value: "dark" });
    off("widget:change", listener);
    emit("widget:change", { id: "settings", key: "theme", value: "light" });

    expect(seen).toEqual([{ id: "settings", key: "theme", value: "dark" }]);
  });

  it("applies registered behaviors on ready and binds late registrations immediately", async () => {
    document.body.innerHTML = '<p data-x="1"></p>';
    const { behaviors } = await importFresh("runtime.js");

    const bound = [];
    behaviors.register("early", { bind: (root) => bound.push(["early", root]) });
    // happy-dom documents are already interactive, so apply happens on import;
    // a registration right after import is "late" and must bind immediately.
    expect(bound.map((entry) => entry[0])).toContain("early");

    behaviors.register("late", { bind: () => bound.push(["late"]) });
    expect(bound.map((entry) => entry[0])).toContain("late");
  });

  it("override replaces a behavior binding and rebind re-runs one id", async () => {
    const { behaviors } = await importFresh("runtime.js");

    const calls = [];
    behaviors.register("toc-like", { bind: () => calls.push("builtin") });
    behaviors.override("toc-like", () => calls.push("host"));

    expect(calls.at(-1)).toBe("host");
    behaviors.rebind("toc-like");
    expect(calls.filter((name) => name === "host").length).toBeGreaterThanOrEqual(2);
    expect(calls.filter((name) => name === "builtin").length).toBeLessThanOrEqual(1);
  });

  it("passes configure() config to behavior binds", async () => {
    const { behaviors } = await importFresh("runtime.js");

    const seen = [];
    behaviors.register("configurable", { bind: (_root, config) => seen.push(config) });
    behaviors.configure("configurable", { visible: true });
    behaviors.rebind("configurable");

    expect(seen.at(-1)).toEqual({ visible: true });
  });

  it("mounts widgets into server mounts with page-model config under configure()", async () => {
    setPageModel({
      version: 1,
      widgets: { settings: { choosers: ["theme"], extra: "model" } },
    });
    document.body.innerHTML += '<div data-kpress-widget="settings"></div>';
    const { widgets, getModel } = await importFresh("runtime.js");

    const mounts = [];
    widgets.register("settings", {
      mount: (el, config, model) => mounts.push({ el, config, model }),
    });

    expect(mounts).toHaveLength(1);
    expect(mounts[0].el.dataset.kpressWidget).toBe("settings");
    expect(mounts[0].config).toEqual({ choosers: ["theme"], extra: "model" });
    expect(mounts[0].model).toBe(getModel());

    // configure() overrides page-model config keys on the next mount.
    widgets.configure("settings", { extra: "host" });
    widgets.mount("settings", document.querySelector("[data-kpress-widget]"));
    expect(mounts.at(-1).config).toEqual({ choosers: ["theme"], extra: "host" });
  });

  it("explicit mount works for embeds with no server mount and no page model", async () => {
    const { widgets } = await importFresh("runtime.js");

    const mounts = [];
    widgets.register("minimap", { mount: (el, config) => mounts.push({ el, config }) });
    const host = document.createElement("div");
    widgets.mount("minimap", host, { depth: 2 });

    expect(mounts).toEqual([{ el: host, config: { depth: 2 } }]);
  });

  it("emits kpress:ready after applying registrations", async () => {
    const { on } = await importFresh("runtime.js");
    const events = [];
    on("kpress:ready", () => events.push("ready"));

    // Already-ready documents have applied before listeners attach; the flag
    // records it so late code can check rather than wait.
    expect(globalThis.kpress.isReady).toBe(true);
    expect(events).toEqual([]);
  });
});
