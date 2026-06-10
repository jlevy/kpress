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
  try {
    localStorage.setItem(STORAGE_KEY, normalized);
  } catch {
    // Storage may be unavailable in embedded views.
  }
}

function bindThemeToggleControls() {
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

/**
 * Wire the gear settings popover: toggle on the button, dismiss on outside
 * click or Escape. Visibility is driven by `aria-expanded` on the wrapper.
 */
function bindSettingsMenu() {
  const wrap = document.querySelector(".kpress-settings");
  const button = wrap?.querySelector(".kpress-settings-btn");
  if (!wrap || !button || wrap.getAttribute("data-kpress-bound") === "true") {
    return;
  }
  wrap.setAttribute("data-kpress-bound", "true");
  const isOpen = () => wrap.getAttribute("aria-expanded") === "true";
  /** @param {boolean} open */
  const setOpen = (open) => wrap.setAttribute("aria-expanded", open ? "true" : "false");
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    setOpen(!isOpen());
  });
  document.addEventListener("click", (event) => {
    if (isOpen() && !wrap.contains(/** @type {Node} */ (event.target))) {
      setOpen(false);
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isOpen()) {
      setOpen(false);
    }
  });
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
  try {
    mode = localStorage.getItem(STORAGE_KEY) || mode;
  } catch {
    // Keep the document-provided mode.
  }
  bindThemeToggleControls();
  bindSettingsMenu();
  bindSystemThemeListener();
  setKpressTheme(mode);
}

initKpressTheme();
