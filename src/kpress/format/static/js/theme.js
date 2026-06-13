/**
 * Theme engine (`kpress.theme`): the headless light/dark machinery — resolve
 * the `system` preference, set the `data-kpress-theme` /
 * `data-kpress-resolved-theme` state attrs, persist the choice, notify
 * listeners, and track OS theme changes. Presentation lives elsewhere (the
 * settings widget is the default face; a host can put its own toggle on this
 * engine). See kpress-design.md "Theme and Fonts".
 *
 * Import attaches ONLY the headless namespace — no storage I/O, no DOM
 * mutation, no matchMedia binding. Initialization is the registered `theme`
 * BEHAVIOR's bind, which the runtime applies at ready: a host head script can
 * therefore swap the storage adapter before the engine's first read, and an
 * embed host that owns theme resolution can `override("theme", ...)` so
 * KPress never touches the root theme attrs.
 */

import { behaviors, emit, on, storage } from "./runtime.js";

const STORAGE_KEY = "kpress.theme";
const THEME_MODES = new Set(["system", "light", "dark"]);
/** @type {{ query: MediaQueryList, handler: () => void } | null} */
let systemThemeBinding = null;

/**
 * @param {string} mode
 * @returns {"light" | "dark"}
 */
function resolveTheme(mode) {
  if (mode === "light" || mode === "dark") {
    return mode;
  }
  return globalThis.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light";
}

/**
 * @param {string | null | undefined} mode
 * @returns {"system" | "light" | "dark"}
 */
function normalizeThemeMode(mode) {
  return mode && THEME_MODES.has(mode)
    ? /** @type {"system" | "light" | "dark"} */ (mode)
    : "system";
}

/**
 * @param {"system" | "light" | "dark"} mode
 */
function syncThemeControls(mode) {
  for (const button of document.querySelectorAll("[data-kpress-theme-choice]")) {
    const active = button.getAttribute("data-kpress-theme-choice") === mode;
    button.setAttribute("aria-checked", active ? "true" : "false");
  }
}

export function setKpressTheme(mode = "system") {
  const normalized = normalizeThemeMode(mode);
  const resolved = resolveTheme(normalized);
  document.documentElement.dataset.kpressTheme = normalized;
  document.documentElement.dataset.kpressResolvedTheme = resolved;
  syncThemeControls(normalized);
  storage.set(STORAGE_KEY, normalized);
  emit("theme:change", { mode: normalized, resolved });
}

export function bindThemeToggleControls() {
  for (const button of document.querySelectorAll("[data-kpress-theme-choice]")) {
    if (button.getAttribute("data-kpress-bound") === "true") {
      continue;
    }
    button.setAttribute("data-kpress-bound", "true");
    button.addEventListener("click", () => {
      setKpressTheme(button.getAttribute("data-kpress-theme-choice") || "system");
    });
  }
}

function bindSystemThemeListener() {
  const query = globalThis.matchMedia?.("(prefers-color-scheme: dark)") || null;
  if (!query || systemThemeBinding?.query === query) {
    return;
  }
  unbindSystemThemeListener();
  const updateSystemTheme = () => {
    if (document.documentElement.dataset.kpressTheme === "system") {
      setKpressTheme("system");
    }
  };
  if (query.addEventListener) {
    query.addEventListener("change", updateSystemTheme);
  } else if (query.addListener) {
    query.addListener(updateSystemTheme);
  }
  systemThemeBinding = { query, handler: updateSystemTheme };
}

function unbindSystemThemeListener() {
  if (!systemThemeBinding) {
    return;
  }
  const { query, handler } = systemThemeBinding;
  systemThemeBinding = null;
  if (query.removeEventListener) {
    query.removeEventListener("change", handler);
  } else if (query.removeListener) {
    query.removeListener(handler);
  }
}

/**
 * Initialize the engine: read the persisted mode through the CURRENT storage
 * adapter, stamp the root theme attrs, wire toggle controls, and track OS
 * theme changes. Runs as the `theme` behavior's bind (not at import).
 */
export function initKpressTheme() {
  let mode = document.documentElement.dataset.kpressTheme || "system";
  mode = storage.get(STORAGE_KEY) || mode;
  bindThemeToggleControls();
  bindSystemThemeListener();
  setKpressTheme(mode);
}

const kpressGlobal = /** @type {Record<string, unknown>} */ (
  /** @type {Record<string, unknown>} */ (globalThis).kpress ?? {}
);
/** @type {Record<string, unknown>} */ (globalThis).kpress = kpressGlobal;
kpressGlobal.theme = {
  set: setKpressTheme,
  /** @returns {string} */
  mode: () => document.documentElement.dataset.kpressTheme || "system",
  /** @returns {string} */
  resolved: () =>
    document.documentElement.dataset.kpressResolvedTheme ||
    resolveTheme(document.documentElement.dataset.kpressTheme || "system"),
  /** @param {(detail: unknown) => void} listener */
  onChange: (listener) => on("theme:change", listener),
};

// Initialization is a behavior like any other built-in (dogfood rule): the
// pre-paint bootstrap stamps attrs from raw localStorage before first paint;
// this bind re-reads through the live storage adapter at ready and re-applies,
// so an adapter swapped in by a host head script owns persistence from the
// first read. The disposer unbinds the OS theme listener.
behaviors.register("theme", {
  bind: () => {
    initKpressTheme();
    return unbindSystemThemeListener;
  },
});
