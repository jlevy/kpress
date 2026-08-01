/**
 * Behavior-neutral theme controls. Buttons emit a theme request; whichever
 * layer owns theme resolution handles it and later announces the resolved
 * state through `theme:change`.
 */

import { emit, on } from "./runtime.js";

const THEME_MODES = new Set(["system", "light", "dark"]);

/**
 * @param {string | null | undefined} mode
 * @returns {"system" | "light" | "dark"}
 */
export function normalizeThemeMode(mode) {
  return mode && THEME_MODES.has(mode)
    ? /** @type {"system" | "light" | "dark"} */ (mode)
    : "system";
}

/** @param {"system" | "light" | "dark"} mode */
export function syncThemeControls(mode) {
  for (const button of document.querySelectorAll("[data-kpress-theme-choice]")) {
    const active = button.getAttribute("data-kpress-theme-choice") === mode;
    button.setAttribute("aria-checked", active ? "true" : "false");
  }
}

/** Bind theme buttons without choosing who owns theme resolution. */
export function bindThemeToggleControls() {
  for (const button of document.querySelectorAll("[data-kpress-theme-choice]")) {
    if (button.getAttribute("data-kpress-bound") === "true") {
      continue;
    }
    button.setAttribute("data-kpress-bound", "true");
    button.addEventListener("click", () => {
      const mode = normalizeThemeMode(button.getAttribute("data-kpress-theme-choice"));
      emit("theme:request", { mode });
    });
  }
}

// The event bus and native ESM module are page singletons, so this listener
// intentionally lives for the module lifetime.
on("theme:change", (detail) => {
  const change =
    detail && typeof detail === "object" ? /** @type {{ mode?: unknown }} */ (detail) : {};
  const mode =
    typeof change.mode === "string"
      ? normalizeThemeMode(change.mode)
      : normalizeThemeMode(document.documentElement.dataset.kpressTheme);
  syncThemeControls(mode);
});
