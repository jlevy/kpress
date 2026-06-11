/**
 * Theme engine (`kpress.theme`): the headless light/dark machinery — resolve
 * the `system` preference, set the `data-kpress-theme` /
 * `data-kpress-resolved-theme` state attrs, persist the choice, notify
 * listeners, and track OS theme changes. Presentation lives elsewhere (the
 * settings widget is the default face; a host can put its own toggle on this
 * engine). See kpress-design.md "Theme and Fonts".
 */

import { emit, on, storage } from "./runtime.js";

const STORAGE_KEY = "kpress.theme";
const THEME_MODES = new Set(["system", "light", "dark"]);
/** @type {MediaQueryList | null} */
let systemThemeQuery = null;

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
  if (!query || query === systemThemeQuery) {
    return;
  }
  systemThemeQuery = query;
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
}

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

initKpressTheme();
