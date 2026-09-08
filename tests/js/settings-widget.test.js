import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  emit as sharedEmit,
  off as sharedOff,
  on as sharedOn,
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

  it("requests a host theme without loading or running the resolver", async () => {
    const requests = [];
    const listener = (detail) => requests.push(detail);
    sharedOn("theme:request", listener);
    document.documentElement.dataset.kpressResolvedTheme = "light";

    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme"] });
    const dark = /** @type {HTMLElement} */ (el.querySelector('[data-kpress-theme-choice="dark"]'));
    dark.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(requests).toEqual([{ mode: "dark" }]);
    expect(document.documentElement.dataset.kpressTheme).toBeUndefined();
    expect(document.documentElement.dataset.kpressResolvedTheme).toBe("light");
    expect(localStorage.getItem("kpress.theme")).toBeNull();

    document.documentElement.dataset.kpressResolvedTheme = "dark";
    sharedEmit("theme:change", { mode: "dark", resolved: "dark" });
    expect(
      el.querySelector('[data-kpress-theme-choice="dark"]')?.getAttribute("aria-checked"),
    ).toBe("true");
    sharedOff("theme:request", listener);
  });

  it("synchronizes host-owned theme state announced after mount", async () => {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme"] });

    document.documentElement.dataset.kpressResolvedTheme = "dark";
    sharedEmit("theme:change", { mode: "dark", resolved: "dark" });

    expect(
      el.querySelector('[data-kpress-theme-choice="dark"]')?.getAttribute("aria-checked"),
    ).toBe("true");
    expect(
      el.querySelector('[data-kpress-theme-choice="system"]')?.getAttribute("aria-checked"),
    ).toBe("false");
  });

  it("theme segments drive the theme engine", async () => {
    await importFresh("settings-widget.js");
    await importFresh("theme.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme"] });

    const light = /** @type {HTMLElement} */ (
      el.querySelector('[data-kpress-theme-choice="light"]')
    );
    light.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(document.documentElement.dataset.kpressTheme).toBe("light");
    expect(
      el.querySelector('[data-kpress-theme-choice="light"]')?.getAttribute("aria-checked"),
    ).toBe("true");
  });

  it("keeps the settings menu open and focused while switching themes", async () => {
    await importFresh("settings-widget.js");
    await importFresh("theme.js");
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

  // The font set is also the switch for the math text face, and that face is
  // half CSS and half metrics: katex-init.js hands KaTeX its tables once, at
  // load, through a setter with no getter, over TeX that is gone as soon as it
  // has been typeset. Flipping the CSS alone would leave every rendered fraction
  // and accent laid out for the face it is no longer drawn in, so a page that has
  // typeset math completes the switch by reloading into the persisted choice.
  async function switchFontSet(value) {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["font-set"] });
    const select = /** @type {HTMLSelectElement} */ (el.querySelector("select.kpress-menu-select"));
    select.value = value;
    select.dispatchEvent(new Event("change", { bubbles: true }));
  }

  it("reloads into the persisted choice when the page has typeset math", async () => {
    const reload = vi.spyOn(globalThis.location, "reload").mockImplementation(() => {});
    document.body.innerHTML =
      '<article class="kpress" data-kpress-fonts="custom"><span class="katex">4</span></article>';

    await switchFontSet("system");

    expect(localStorage.getItem("kpress.fontSet")).toBe("system");
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("reloads in the other direction too, back to the reading face", async () => {
    const reload = vi.spyOn(globalThis.location, "reload").mockImplementation(() => {});
    document.documentElement.dataset.kpressFontSet = "system";
    document.body.innerHTML =
      '<article class="kpress" data-kpress-fonts="system"><span class="katex">4</span></article>';

    await switchFontSet("custom");

    expect(localStorage.getItem("kpress.fontSet")).toBe("custom");
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("switches in place with no math to re-lay-out, and never on a no-op", async () => {
    const reload = vi.spyOn(globalThis.location, "reload").mockImplementation(() => {});
    document.body.innerHTML = '<article class="kpress" data-kpress-fonts="custom"></article>';

    await switchFontSet("system");

    expect(document.documentElement.dataset.kpressFontSet).toBe("system");
    expect(reload).not.toHaveBeenCalled();

    // Nothing changed, so nothing to rebuild even with math on the page.
    document.body.innerHTML =
      '<article class="kpress" data-kpress-fonts="system"><span class="katex">4</span></article>';
    await switchFontSet("system");

    expect(reload).not.toHaveBeenCalled();
  });

  it("switches in place when the text face is off page-wide", async () => {
    // Nothing on the page is laid out from the reading face's tables, so the
    // reload would buy nothing. katex-init.js stamps this itself when the tables
    // cannot be applied, which lands in the same branch.
    const reload = vi.spyOn(globalThis.location, "reload").mockImplementation(() => {});
    document.documentElement.dataset.kpressMathText = "katex";
    document.body.innerHTML =
      '<article class="kpress" data-kpress-fonts="custom"><span class="katex">4</span></article>';

    await switchFontSet("system");

    expect(document.documentElement.dataset.kpressFontSet).toBe("system");
    expect(reload).not.toHaveBeenCalled();
    document.documentElement.removeAttribute("data-kpress-math-text");
  });

  // The reading font is the second switch over the same tables, and the one that
  // is easiest to mistake for text-only: it does not turn the math text face off,
  // it moves the page between the face's two composites. katex-init.js selects
  // `KPress Math Text Sans` for every node inside a sans context, and
  // `[data-kpress-prose-font="sans"]` is one of them, so the stamp alone would
  // redraw prose mathematics in Source Sans while KaTeX went on holding the PT
  // Serif tables it was handed at load. Same guard as the font set, for the same
  // reason.
  async function chooseReadingFont(value) {
    await importFresh("settings-widget.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["reading-font"] });
    const seg = /** @type {HTMLElement} */ (
      el.querySelector(`[data-kpress-prose-choice="${value}"]`)
    );
    seg.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  }

  it("reloads into the persisted reading face when the page has typeset math", async () => {
    const reload = vi.spyOn(globalThis.location, "reload").mockImplementation(() => {});
    document.body.innerHTML =
      '<article class="kpress" data-kpress-fonts="custom"><span class="katex">4</span></article>';

    await chooseReadingFont("sans");

    expect(document.documentElement.dataset.kpressProseFont).toBe("sans");
    expect(localStorage.getItem("kpress.proseFont")).toBe("sans");
    expect(reload).toHaveBeenCalledTimes(1);

    // Choosing the face the page is already in changes nothing, so it rebuilds
    // nothing: a reader clicking the checked segment must not lose their place.
    await chooseReadingFont("sans");

    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("treats the unstamped reading face as serif, so choosing serif is a no-op", async () => {
    // Nothing has stamped <html>, which is the state a first visit is in, and the
    // default that leaves the page in is the serif composite. Reading the missing
    // attribute as a change would reload every page whose reader opened the menu
    // and clicked the segment already marked.
    const reload = vi.spyOn(globalThis.location, "reload").mockImplementation(() => {});
    document.body.innerHTML =
      '<article class="kpress" data-kpress-fonts="custom"><span class="katex">4</span></article>';

    await chooseReadingFont("serif");

    expect(document.documentElement.dataset.kpressProseFont).toBe("serif");
    expect(localStorage.getItem("kpress.proseFont")).toBe("serif");
    expect(reload).not.toHaveBeenCalled();
  });

  it("switches the reading face in place when there is no math to re-lay-out", async () => {
    const reload = vi.spyOn(globalThis.location, "reload").mockImplementation(() => {});
    document.body.innerHTML = '<article class="kpress" data-kpress-fonts="custom"></article>';

    await chooseReadingFont("sans");

    expect(document.documentElement.dataset.kpressProseFont).toBe("sans");
    expect(reload).not.toHaveBeenCalled();
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
    await importFresh("theme.js");
    const el = settingsMount();
    sharedWidgets.mount("settings", el, { choosers: ["theme", "reading-font"] });

    const sans = /** @type {HTMLElement} */ (el.querySelector('[data-kpress-prose-choice="sans"]'));
    sans.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(sans.getAttribute("aria-checked")).toBe("true");

    const light = /** @type {HTMLElement} */ (
      el.querySelector('[data-kpress-theme-choice="light"]')
    );
    light.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(
      el.querySelector('[data-kpress-theme-choice="light"]')?.getAttribute("aria-checked"),
    ).toBe("true");
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
