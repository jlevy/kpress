import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Pre-apply lifecycle tests: the window between module registration and the
 * runtime's ready pass (DOMContentLoaded -> applyAll). Each test resets the
 * module registry and forces document.readyState to "loading" BEFORE importing
 * the canonical modules, so registrations queue instead of applying
 * immediately — the ordering a real page gives host head scripts.
 *
 * No cache-busting queries here: every import is canonical, so the built-in
 * modules and the test share one runtime instance per test.
 */

const moduleImports = Object.freeze({
  "host.js": () => import("../../src/kpress/format/static/js/host.js"),
  "runtime.js": () => import("../../src/kpress/format/static/js/runtime.js"),
  "tables.js": () => import("../../src/kpress/format/static/js/tables.js"),
  "theme.js": () => import("../../src/kpress/format/static/js/theme.js"),
  "tooltips.js": () => import("../../src/kpress/format/static/js/tooltips.js"),
  "video-popover.js": () => import("../../src/kpress/format/static/js/video-popover.js"),
});

/** Import a module fresh within this test's reset module graph. */
const importJs = (/** @type {keyof typeof moduleImports} */ name) => moduleImports[name]();

function forceLoadingState() {
  Object.defineProperty(document, "readyState", {
    configurable: true,
    value: "loading",
    writable: true,
  });
}

function fireReady() {
  // @ts-expect-error -- writable instance override installed by forceLoadingState
  document.readyState = "interactive";
  document.dispatchEvent(new Event("DOMContentLoaded"));
}

const flushObservers = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  vi.resetModules();
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-kpress-theme");
  document.documentElement.removeAttribute("data-kpress-resolved-theme");
  localStorage.clear();
  delete globalThis.kpress;
  forceLoadingState();
});

afterEach(() => {
  // Remove the instance override so the prototype getter is visible again.
  delete document.readyState;
});

describe("ready-pass fault isolation", () => {
  it("a throwing widget mount or behavior bind does not abort the pass or kpress:ready", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const { widgets, behaviors, on } = await importJs("runtime.js");
    document.body.innerHTML =
      '<div data-kpress-widget="bad"></div><div data-kpress-widget="good"></div>';

    widgets.register("bad", {
      mount: () => {
        throw new Error("widget boom");
      },
    });
    widgets.register("good", { mount: (el) => el.setAttribute("data-mounted", "true") });
    behaviors.register("explodes", {
      bind: () => {
        throw new Error("behavior boom");
      },
    });
    const bound = [];
    behaviors.register("works", { bind: () => bound.push("works") });
    const events = [];
    on("kpress:ready", () => events.push("ready"));

    fireReady();

    expect(events).toEqual(["ready"]);
    expect(globalThis.kpress.isReady).toBe(true);
    expect(bound).toEqual(["works"]);
    expect(document.querySelector("[data-mounted]")).toBeTruthy();
    expect(error).toHaveBeenCalledWith(expect.stringContaining('"bad"'), expect.any(Error));
    expect(error).toHaveBeenCalledWith(expect.stringContaining('"explodes"'), expect.any(Error));
  });

  it("an explicit pre-ready mount on a server mount is not mounted again at ready", async () => {
    const { widgets } = await importJs("runtime.js");

    const mounts = [];
    widgets.register("panel", { mount: (el) => mounts.push(el) });
    const el = document.createElement("div");
    el.setAttribute("data-kpress-widget", "panel");
    document.body.appendChild(el);
    widgets.mount("panel", el);
    expect(mounts).toEqual([el]);

    fireReady();

    expect(mounts).toEqual([el]);
  });
});

describe("host lifecycle", () => {
  it("registers at import and retains teardown through the behavior disposer", async () => {
    const runtime = await importJs("runtime.js");
    const host = await importJs("host.js");
    expect(host.HOST_BEHAVIOR_ID).toBe("host");
    expect(typeof host.initKpressHost).toBe("function");

    const calls = [];
    runtime.behaviors.override("host", {
      bind: () => {
        calls.push("bind");
        return () => calls.push("dispose");
      },
    });
    expect(calls).toEqual([]);

    fireReady();
    expect(calls).toEqual(["bind"]);
    runtime.behaviors.rebind("host");
    expect(calls).toEqual(["bind", "dispose", "bind"]);
  });
});

describe("pre-apply overrides really replace built-ins", () => {
  it('override("video") suppresses built-in embedding of late-injected placeholders', async () => {
    const { behaviors } = await importJs("runtime.js");
    await importJs("video-popover.js");

    behaviors.override("video", () => {});
    fireReady();

    const host = document.createElement("div");
    host.innerHTML =
      '<button class="kpress-video-placeholder" data-kpress-video-id="abc123"></button>';
    document.body.appendChild(host);
    await flushObservers();

    // The placeholder stays a placeholder: no built-in observer embeds it.
    expect(host.querySelector("[data-kpress-video-id]")).not.toBeNull();
    expect(document.querySelector("iframe.kpress-video-embed")).toBeNull();
  });

  it('override("tables") suppresses built-in wrapping on kpress:tabchange', async () => {
    const { behaviors } = await importJs("runtime.js");
    await importJs("tables.js");

    behaviors.override("tables", () => {});
    fireReady();

    document.body.innerHTML = `
      <article class="kpress-prose">
        <table><tbody><tr><td>42</td></tr></tbody></table>
      </article>
    `;
    document.dispatchEvent(new CustomEvent("kpress:tabchange"));

    expect(document.querySelector(".kpress-table-wrap")).toBeNull();
    expect(document.querySelector("table")?.classList.contains("kpress-table")).toBe(false);
  });

  it('override("footnote-preview") leaves link tooltips fully working', async () => {
    const { behaviors } = await importJs("runtime.js");
    await importJs("tooltips.js");

    behaviors.override("footnote-preview", () => {});
    document.body.innerHTML = `
      <p><a href="#target">Target</a>
      <sup class="kpress-footnote-ref"><a href="#fn-x">1</a></sup></p>
      <h2 id="target">Target Heading</h2>
      <section class="kpress-footnotes"><ol><li id="fn-x">Footnote body</li></ol></section>
    `;
    fireReady();

    // Internal-link previews (the sibling behavior) still work...
    document
      .querySelector('a[href="#target"]')
      ?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")?.textContent).toContain("Target Heading");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));

    // ...while footnote anchors are the host's: no built-in preview.
    document
      .querySelector('a[href="#fn-x"]')
      ?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")).toBeNull();

    // Late-injected anchors follow the same split: links wired, footnotes not.
    const host = document.createElement("div");
    host.innerHTML = `
      <p><a href="#target" id="late-link">late link</a>
      <sup class="kpress-footnote-ref"><a href="#fn-x" id="late-fn">2</a></sup></p>
    `;
    document.body.appendChild(host);
    await flushObservers();

    document.getElementById("late-fn")?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")).toBeNull();
    document.getElementById("late-link")?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    expect(document.querySelector(".kpress-tooltip")?.textContent).toContain("Target Heading");
  });

  it('override("theme") keeps kpress away from root theme attrs (embed host owns theme)', async () => {
    await importJs("runtime.js");
    await importJs("theme.js");

    globalThis.kpress.behaviors.override("theme", () => {});
    fireReady();

    expect(document.documentElement.dataset.kpressTheme).toBeUndefined();
    expect(document.documentElement.dataset.kpressResolvedTheme).toBeUndefined();
  });
});

describe("theme engine init goes through the live storage adapter", () => {
  it("a pre-ready adapter swap wins the engine's first read and all writes", async () => {
    const { storage } = await importJs("runtime.js");
    await importJs("theme.js");

    // Nothing initialized at import: no root attrs, no storage reads yet.
    expect(document.documentElement.dataset.kpressTheme).toBeUndefined();

    // Stale localStorage must NOT win over the host's adapter.
    localStorage.setItem("kpress.theme", "light");
    const remembered = new Map([["kpress.theme", "dark"]]);
    const reads = [];
    storage.use({
      get: (key) => {
        reads.push(key);
        return remembered.get(key) ?? null;
      },
      set: (key, value) => remembered.set(key, value),
    });

    fireReady();

    expect(reads).toContain("kpress.theme");
    expect(document.documentElement.dataset.kpressTheme).toBe("dark");

    globalThis.kpress.theme.set("system");
    expect(remembered.get("kpress.theme")).toBe("system");
    // The default store is untouched: persistence went through the adapter.
    expect(localStorage.getItem("kpress.theme")).toBe("light");
  });
});
