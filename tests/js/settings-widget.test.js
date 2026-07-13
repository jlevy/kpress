import { beforeEach, describe, expect, it, vi } from "vitest";

// The widget imports "./runtime.js" and "./theme.js" without cache-busting
// queries; share those instances to drive and observe it.
import {
  storage as sharedStorage,
  widgets as sharedWidgets,
} from "../../src/kpress/format/static/js/runtime.js";

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function stubMatchMedia() {
  globalThis.matchMedia = (query) => ({
    matches: false,
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

function settingsMount() {
  const el = document.createElement("div");
  el.className = "kpress-widget kpress-settings kpress-no-print";
  el.id = "kpress-settings";
  el.setAttribute("data-kpress-widget", "settings");
  document.body.appendChild(el);
  return el;
}

beforeEach(() => {
  document.body.innerHTML = "";
  const root = document.documentElement;
  root.removeAttribute("data-kpress-theme");
  root.removeAttribute("data-kpress-resolved-theme");
  root.removeAttribute("data-kpress-prose-font");
  root.removeAttribute("data-kpress-font-set");
  localStorage.clear();
  stubMatchMedia();
  sharedStorage.use({
    get: (key) => localStorage.getItem(key),
    set: (key, value) => localStorage.setItem(key, value),
  });
});

describe("settings widget", () => {
  it("auto-mounts into the server mount with the default theme chooser", async () => {
    const el = settingsMount();
    await importFresh("settings-widget.js");

    expect(el.querySelector(".kpress-settings-btn")).toBeTruthy();
    expect(el.querySelector(".kpress-settings-menu")).toBeTruthy();
    expect(el.querySelectorAll("[data-kpress-theme-choice]")).toHaveLength(3);
    expect(el.querySelectorAll("[data-kpress-prose-choice]")).toHaveLength(0);

    // The gear opens and closes via the menu primitive.
    const button = /** @type {HTMLElement} */ (el.querySelector(".kpress-settings-btn"));
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(el.getAttribute("aria-expanded")).toBe("true");
    document.body.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(el.getAttribute("aria-expanded")).toBe("false");
  });

  it("renders configured choosers in order and re-mounts cleanly", async () => {
    await importFresh("settings-widget.js");
    const el = settingsMount();

    sharedWidgets.mount("settings", el, {
      choosers: ["theme", "reading-font", "font-set"],
    });
    expect(el.querySelectorAll("[data-kpress-theme-choice]")).toHaveLength(3);
    expect(el.querySelectorAll("[data-kpress-prose-choice]")).toHaveLength(2);
    expect(el.querySelector("select.kpress-menu-select")).toBeTruthy();

    // Remount with fewer choosers replaces the markup and keeps the gear working.
    sharedWidgets.mount("settings", el, { choosers: ["theme"] });
    expect(el.querySelectorAll("[data-kpress-prose-choice]")).toHaveLength(0);
    const button = /** @type {HTMLElement} */ (el.querySelector(".kpress-settings-btn"));
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(el.getAttribute("aria-expanded")).toBe("true");
  });

  it("theme segments drive the theme engine", async () => {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme"] });

    const light = /** @type {HTMLElement} */ (
      el.querySelector('[data-kpress-theme-choice="light"]')
    );
    light.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(document.documentElement.dataset.kpressTheme).toBe("light");
    expect(light.getAttribute("aria-checked")).toBe("true");
  });

  it("keeps the settings menu open and focused while switching themes", async () => {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme", "reading-font"] });

    const gear = /** @type {HTMLElement} */ (el.querySelector(".kpress-settings-btn"));
    gear.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    const dark = /** @type {HTMLElement} */ (el.querySelector('[data-kpress-theme-choice="dark"]'));
    dark.focus();
    dark.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(el.getAttribute("aria-expanded")).toBe("true");
    expect(document.activeElement).toBe(dark);
    expect(dark.getAttribute("aria-checked")).toBe("true");
    expect(el.querySelector("[data-kpress-prose-choice]")).toBeTruthy();
  });

  it("reading-font chooser stamps, persists, and marks the prose font", async () => {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["reading-font"] });

    const sans = /** @type {HTMLElement} */ (el.querySelector('[data-kpress-prose-choice="sans"]'));
    sans.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(document.documentElement.dataset.kpressProseFont).toBe("sans");
    expect(localStorage.getItem("kpress.proseFont")).toBe("sans");
    expect(sans.getAttribute("aria-checked")).toBe("true");
    const serif = el.querySelector('[data-kpress-prose-choice="serif"]');
    expect(serif?.getAttribute("aria-checked")).toBe("false");
  });

  it("font-set chooser stamps html and document wrappers and persists", async () => {
    document.body.innerHTML = '<article class="kpress" data-kpress-fonts="custom"></article>';
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["font-set"] });

    const select = /** @type {HTMLSelectElement} */ (el.querySelector("select.kpress-menu-select"));
    select.value = "system";
    select.dispatchEvent(new Event("change", { bubbles: true }));

    expect(document.documentElement.dataset.kpressFontSet).toBe("system");
    expect(document.querySelector(".kpress")?.getAttribute("data-kpress-fonts")).toBe("system");
    expect(localStorage.getItem("kpress.fontSet")).toBe("system");
  });

  it("changing the reading font leaves the active theme segment checked", async () => {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme", "reading-font"] });

    // The active theme segment is marked at mount (default mode: system) and
    // must survive the sibling chooser's own marking.
    const system = el.querySelector('[data-kpress-theme-choice="system"]');
    expect(system?.getAttribute("aria-checked")).toBe("true");

    const serif = /** @type {HTMLElement} */ (
      el.querySelector('[data-kpress-prose-choice="serif"]')
    );
    serif.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(serif.getAttribute("aria-checked")).toBe("true");
    expect(system?.getAttribute("aria-checked")).toBe("true");
  });

  it("changing the theme leaves the active reading-font segment checked", async () => {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme", "reading-font"] });

    const sans = /** @type {HTMLElement} */ (el.querySelector('[data-kpress-prose-choice="sans"]'));
    sans.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(sans.getAttribute("aria-checked")).toBe("true");

    const light = /** @type {HTMLElement} */ (
      el.querySelector('[data-kpress-theme-choice="light"]')
    );
    light.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(light.getAttribute("aria-checked")).toBe("true");
    expect(sans.getAttribute("aria-checked")).toBe("true");
  });

  it("mounts twice (embeds) without duplicate element ids", async () => {
    await importFresh("settings-widget.js");
    const first = settingsMount();
    const second = document.createElement("div");
    document.body.appendChild(second);

    sharedWidgets.mount("settings", first, { choosers: ["theme"] });
    sharedWidgets.mount("settings", second, { choosers: ["theme"] });

    const ids = Array.from(document.querySelectorAll("[id]"), (node) => node.id);
    expect(new Set(ids).size).toBe(ids.length);

    // Both gears stay independently operable.
    const secondButton = /** @type {HTMLElement} */ (second.querySelector(".kpress-settings-btn"));
    secondButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(second.getAttribute("aria-expanded")).toBe("true");
    expect(first.getAttribute("aria-expanded")).toBe("false");
  });

  it("warns and skips unknown chooser ids", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    await importFresh("settings-widget.js");
    const el = settingsMount();

    sharedWidgets.mount("settings", el, { choosers: ["theme", "mystery"] });

    expect(el.querySelectorAll("[data-kpress-theme-choice]")).toHaveLength(3);
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("mystery"));
    warn.mockRestore();
  });
});
