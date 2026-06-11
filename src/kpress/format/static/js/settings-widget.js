/**
 * The settings widget (registry id `settings`): the default presentation over
 * the theme/font engines — a gear button opening a menu of choosers. It is a
 * built-in chrome widget assembled ONLY from the public layers (dogfood rule):
 * the runtime registries, the menu primitive, the theme engine, the icon
 * sprite, and the `data-kpress-*` state-attr contract.
 *
 * Its chooser catalog is defined here, in the widget's own JS
 * (schema-with-the-code): config is `{ choosers: [...] }` (default
 * `["theme"]`); unknown ids warn and are skipped. The widget client-renders
 * into its server mount (no-JS rule) — there is no server-rendered menu.
 */

import { icon } from "./icons.js";
import { bindMenu, markChecked } from "./menu.js";
import { emit, storage, widgets } from "./runtime.js";
import { bindThemeToggleControls } from "./theme.js";

const PROSE_FONT_KEY = "kpress.proseFont";
const FONT_SET_KEY = "kpress.fontSet";

/**
 * @param {string} value "serif" | "sans"
 */
function applyProseFont(value) {
  document.documentElement.dataset.kpressProseFont = value;
  storage.set(PROSE_FONT_KEY, value);
  emit("widget:change", { id: "settings", key: "reading-font", value });
}

/**
 * @param {string} value "custom" | "system"
 */
function applyFontSet(value) {
  document.documentElement.dataset.kpressFontSet = value;
  // Already-rendered documents stamped data-kpress-fonts at render time;
  // re-sync them so the switch applies without a re-render.
  for (const doc of document.querySelectorAll(".kpress")) {
    doc.setAttribute("data-kpress-fonts", value === "system" ? "system" : "custom");
  }
  storage.set(FONT_SET_KEY, value);
  emit("widget:change", { id: "settings", key: "font-set", value });
}

/**
 * @param {string} choice data attribute name suffix
 * @param {string} value
 * @param {string} label
 * @param {string} glyph icon name in the sprite
 * @returns {string}
 */
function segment(choice, value, label, glyph) {
  return (
    `<button type="button" class="kpress-menu-seg" role="menuitemradio" ` +
    `data-kpress-${choice}="${value}" aria-checked="false" ` +
    `title="${label}" aria-label="${label}">${icon(glyph)}</button>`
  );
}

/**
 * The built-in chooser catalog. Each chooser renders one `.kpress-menu-chooser`
 * group and binds its own handling — adding a chooser is adding an entry here
 * (or registering a custom widget that composes the same primitives).
 *
 * @type {Record<string, { render(): string, bind(el: HTMLElement): void }>}
 */
const CHOOSERS = {
  theme: {
    render: () =>
      `<div class="kpress-menu-chooser" role="group" aria-label="Theme">` +
      segment("theme-choice", "system", "System theme", "monitor") +
      segment("theme-choice", "light", "Light theme", "sun") +
      segment("theme-choice", "dark", "Dark theme", "moon") +
      `</div>`,
    bind(el) {
      bindThemeToggleControls();
      markChecked(
        el,
        "kpressThemeChoice",
        document.documentElement.dataset.kpressTheme || "system",
      );
    },
  },
  "reading-font": {
    render: () =>
      `<div class="kpress-menu-chooser" role="group" aria-label="Reading font">` +
      segment("prose-choice", "serif", "Serif reading font", "serif") +
      segment("prose-choice", "sans", "Sans-serif reading font", "sans") +
      `</div>`,
    bind(el) {
      for (const button of el.querySelectorAll("[data-kpress-prose-choice]")) {
        button.addEventListener("click", () => {
          const value = button.getAttribute("data-kpress-prose-choice") || "serif";
          applyProseFont(value);
          markChecked(el, "kpressProseChoice", value);
        });
      }
      markChecked(
        el,
        "kpressProseChoice",
        document.documentElement.dataset.kpressProseFont || "serif",
      );
    },
  },
  "font-set": {
    render: () =>
      `<select class="kpress-menu-select" aria-label="Fonts">` +
      `<option value="custom">Clean fonts</option>` +
      `<option value="system">System fonts</option>` +
      `</select>`,
    bind(el) {
      const select = /** @type {HTMLSelectElement | null} */ (
        el.querySelector("select.kpress-menu-select")
      );
      if (!select) {
        return;
      }
      select.value = document.documentElement.dataset.kpressFontSet || "custom";
      select.addEventListener("change", () => {
        applyFontSet(select.value);
      });
    },
  },
};

/**
 * Mount (or remount) the settings widget into an element.
 *
 * @param {HTMLElement} el
 * @param {Record<string, unknown>} config
 */
export function mountSettings(el, config) {
  const requested = Array.isArray(config.choosers)
    ? /** @type {string[]} */ (config.choosers)
    : ["theme"];
  const groups = [];
  /** @type {string[]} */
  const active = [];
  for (const chooserId of requested) {
    const chooser = CHOOSERS[chooserId];
    if (!chooser) {
      console.warn(`kpress: unknown settings chooser "${chooserId}" (skipped)`);
      continue;
    }
    groups.push(chooser.render());
    active.push(chooserId);
  }
  el.innerHTML =
    `<button type="button" class="kpress-settings-btn" id="kpress-settings-btn" ` +
    `aria-haspopup="true" title="Settings" aria-label="Settings">${icon("settings")}</button>` +
    `<div class="kpress-settings-menu kpress-menu" role="menu" aria-label="Settings">` +
    groups.join("") +
    `</div>`;
  el.setAttribute("aria-expanded", "false");

  // Remounts replace the button, so rebind the popover cleanly each time.
  const holder = /** @type {{ __kpressMenuDispose?: () => void }} */ (/** @type {unknown} */ (el));
  holder.__kpressMenuDispose?.();
  const button = /** @type {HTMLElement | null} */ (el.querySelector(".kpress-settings-btn"));
  if (button) {
    holder.__kpressMenuDispose = bindMenu(el, button) ?? undefined;
  }
  for (const chooserId of active) {
    CHOOSERS[chooserId]?.bind(el);
  }
}

widgets.register("settings", { mount: mountSettings });
