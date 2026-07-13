import { beforeEach, describe, expect, it, vi } from "vitest";

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

  it("configure() merges and immediately rebinds a behavior", async () => {
    const { behaviors } = await importFresh("runtime.js");

    const seen = [];
    behaviors.register("configurable", { bind: (_root, config) => seen.push(config) });
    behaviors.configure("configurable", { visible: true });
    behaviors.configure("configurable", { placement: "margin" });

    expect(seen.at(-1)).toEqual({ visible: true, placement: "margin" });
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

    // configure() merges over page-model config and remounts immediately.
    widgets.configure("settings", { extra: "host" });
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

describe("fault isolation", () => {
  it("isolates a throwing emit listener from later listeners", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const { on, emit } = await importFresh("runtime.js");

    const seen = [];
    on("evt", () => {
      throw new Error("listener boom");
    });
    on("evt", (detail) => seen.push(detail));

    expect(() => emit("evt", 1)).not.toThrow();
    expect(seen).toEqual([1]);
    expect(error).toHaveBeenCalledWith(expect.stringContaining('"evt"'), expect.any(Error));
  });

  it("degrades a throwing storage adapter to null get and no-op set", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const { storage } = await importFresh("runtime.js");
    storage.use({
      get() {
        throw new Error("get boom");
      },
      set() {
        throw new Error("set boom");
      },
    });

    expect(storage.get("kpress.test")).toBeNull();
    expect(() => storage.set("kpress.test", "value")).not.toThrow();
    expect(error).toHaveBeenCalledTimes(2);
  });

  it("isolates a throwing behavior bind and reports the id", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const { behaviors } = await importFresh("runtime.js");

    expect(() =>
      behaviors.register("boom", {
        bind: () => {
          throw new Error("bad bind");
        },
      }),
    ).not.toThrow();
    const bound = [];
    behaviors.register("ok", { bind: () => bound.push("ok") });

    expect(bound).toEqual(["ok"]);
    expect(error).toHaveBeenCalledWith(expect.stringContaining('"boom"'), expect.any(Error));
  });

  it("isolates a throwing widget mount and reports the id", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    document.body.innerHTML =
      '<div data-kpress-widget="bad"></div><div data-kpress-widget="good"></div>';
    const { widgets } = await importFresh("runtime.js");

    const mounts = [];
    expect(() =>
      widgets.register("bad", {
        mount: () => {
          throw new Error("bad mount");
        },
      }),
    ).not.toThrow();
    widgets.register("good", { mount: () => mounts.push("good") });

    expect(mounts).toEqual(["good"]);
    expect(error).toHaveBeenCalledWith(expect.stringContaining('"bad"'), expect.any(Error));
  });
});

describe("behavior disposers", () => {
  it("runs a returned disposer before rebind re-binds", async () => {
    const { behaviors } = await importFresh("runtime.js");

    const calls = [];
    behaviors.register("disposable", {
      bind: () => {
        calls.push("bind");
        return () => calls.push("dispose");
      },
    });
    expect(calls).toEqual(["bind"]);

    behaviors.rebind("disposable");
    expect(calls).toEqual(["bind", "dispose", "bind"]);
  });

  it("runs the stored disposer before an override re-binds", async () => {
    const { behaviors } = await importFresh("runtime.js");

    const calls = [];
    behaviors.register("swappable", {
      bind: () => {
        calls.push("builtin");
        return () => calls.push("builtin disposed");
      },
    });
    behaviors.override("swappable", () => calls.push("host"));

    expect(calls).toEqual(["builtin", "builtin disposed", "host"]);
  });

  it("isolates a throwing disposer and still re-binds", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const { behaviors } = await importFresh("runtime.js");

    const calls = [];
    behaviors.register("fragile", {
      bind: () => {
        calls.push("bind");
        return () => {
          throw new Error("dispose boom");
        };
      },
    });
    behaviors.rebind("fragile");

    expect(calls).toEqual(["bind", "bind"]);
    expect(error).toHaveBeenCalledWith(expect.stringContaining('"fragile"'), expect.any(Error));
  });
});

describe("unknown ids are loud", () => {
  it("widgets.mount on an unknown id warns and no-ops", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { widgets } = await importFresh("runtime.js");

    expect(() => widgets.mount("ghost", document.createElement("div"))).not.toThrow();
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('"ghost"'));
  });

  it("widgets.configure on an unknown id warns and stores nothing", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    document.body.innerHTML = '<div data-kpress-widget="late-widget"></div>';
    const { widgets } = await importFresh("runtime.js");

    widgets.configure("late-widget", { extra: "typo-era" });
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('"late-widget"'));

    const configs = [];
    widgets.register("late-widget", { mount: (_el, config) => configs.push(config) });
    expect(configs).toEqual([{}]);
  });

  it("behaviors.rebind on an unknown id warns and no-ops", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { behaviors } = await importFresh("runtime.js");

    expect(() => behaviors.rebind("ghost")).not.toThrow();
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('"ghost"'));
  });

  it("behaviors.configure on an unknown id warns and stores nothing", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { behaviors } = await importFresh("runtime.js");

    behaviors.configure("late-behavior", { flag: true });
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('"late-behavior"'));

    const configs = [];
    behaviors.register("late-behavior", { bind: (_root, config) => configs.push(config) });
    expect(configs).toEqual([{}]);
  });

  it("behaviors.override on an unknown id warns, points at register, and creates nothing", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { behaviors } = await importFresh("runtime.js");

    const hostBind = vi.fn();
    behaviors.override("ghost", hostBind);

    // A typo'd override must not silently create a stray behavior; register is
    // the creation path and the warning says so.
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('"ghost"'));
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("register"));
    behaviors.rebind("ghost");
    expect(hostBind).not.toHaveBeenCalled();
    expect(warn).toHaveBeenCalledTimes(2);
  });
});

describe("explicit mounts set the bound guard", () => {
  it("an explicitly mounted server mount is not mounted again by the ready pass", async () => {
    const { widgets } = await importFresh("runtime.js");

    const mounts = [];
    widgets.register("panel", { mount: (el) => mounts.push(el) });
    const el = document.createElement("div");
    el.setAttribute("data-kpress-widget", "panel");
    document.body.appendChild(el);

    widgets.mount("panel", el);
    expect(mounts).toEqual([el]);
    expect(el.getAttribute("data-kpress-widget-bound")).toBe("true");

    // The loading-state lifecycle suite pins that this guard survives the
    // later ready pass; this already-ready suite pins only the marker itself.
  });
});

describe("post-ready widget mutation", () => {
  it("re-registering a mounted widget disposes and remounts it", async () => {
    document.body.innerHTML = '<div data-kpress-widget="panel"></div>';
    const { widgets } = await importFresh("runtime.js");
    const calls = [];

    widgets.register("panel", {
      mount: () => {
        calls.push("first");
        return () => calls.push("dispose");
      },
    });
    widgets.register("panel", { mount: () => calls.push("second") });

    expect(calls).toEqual(["first", "dispose", "second"]);
  });

  it("an explicit mount config replaces merged config across remounts", async () => {
    const { widgets } = await importFresh("runtime.js");
    const configs = [];
    widgets.register("panel", { mount: (_el, config) => configs.push(config) });
    const el = document.createElement("div");
    document.body.appendChild(el);

    widgets.configure("panel", { merged: true });
    widgets.mount("panel", el, { replacement: true });
    widgets.register("panel", { mount: (_el, config) => configs.push(config) });

    expect(configs.at(-1)).toEqual({ replacement: true });
  });
});
