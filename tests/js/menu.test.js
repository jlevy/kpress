import { beforeEach, describe, expect, it } from "vitest";

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

function menuMarkup() {
  document.body.innerHTML = `
    <div class="kpress-settings" id="wrap" aria-expanded="false">
      <button type="button" id="btn" aria-haspopup="true">gear</button>
      <div class="kpress-menu" role="menu">
        <div class="kpress-menu-chooser" role="group" id="group">
          <button type="button" role="menuitemradio" data-kpress-theme-choice="system" aria-checked="false"></button>
          <button type="button" role="menuitemradio" data-kpress-theme-choice="light" aria-checked="false"></button>
        </div>
      </div>
    </div>
  `;
  return {
    wrap: /** @type {HTMLElement} */ (document.getElementById("wrap")),
    button: /** @type {HTMLElement} */ (document.getElementById("btn")),
    group: /** @type {HTMLElement} */ (document.getElementById("group")),
  };
}

beforeEach(() => {
  document.body.innerHTML = "";
  delete globalThis.kpress;
});

describe("menu primitive (kpress.menu)", () => {
  it("opens on click, closes on outside click and Escape", async () => {
    const { bindMenu } = await importFresh("menu.js");
    const { wrap, button } = menuMarkup();

    bindMenu(wrap, button);
    expect(wrap.getAttribute("aria-expanded")).toBe("false");

    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(wrap.getAttribute("aria-expanded")).toBe("true");

    document.body.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(wrap.getAttribute("aria-expanded")).toBe("false");

    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(wrap.getAttribute("aria-expanded")).toBe("false");
  });

  it("is idempotent and disposable", async () => {
    const { bindMenu } = await importFresh("menu.js");
    const { wrap, button } = menuMarkup();

    const dispose = bindMenu(wrap, button);
    expect(bindMenu(wrap, button)).toBeNull();

    dispose?.();
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(wrap.getAttribute("aria-expanded")).toBe("false");
  });

  it("marks the checked segment within a group", async () => {
    const { markChecked } = await importFresh("menu.js");
    const { group } = menuMarkup();

    markChecked(group, "kpressThemeChoice", "light");

    const system = document.querySelector('[data-kpress-theme-choice="system"]');
    const light = document.querySelector('[data-kpress-theme-choice="light"]');
    expect(system?.getAttribute("aria-checked")).toBe("false");
    expect(light?.getAttribute("aria-checked")).toBe("true");
  });

  it("attaches the kpress.menu namespace", async () => {
    const mod = await importFresh("menu.js");
    expect(globalThis.kpress.menu.bindMenu).toBe(mod.bindMenu);
    expect(globalThis.kpress.menu.markChecked).toBe(mod.markChecked);
  });
});
