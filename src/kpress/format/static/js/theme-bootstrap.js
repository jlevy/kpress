// KPress theme bootstrap. Inlined render-blocking into <head> by render_page so the
// resolved theme is set before first paint (no flash of the wrong theme). It is a classic
// IIFE (not an ES module) and reads the server-set `data-kpress-theme` attribute, so the
// renderer never interpolates anything into this source -- it lives here, in a real JS file.
(() => {
  const key = "kpress.theme";
  const root = document.documentElement;
  let mode = root.dataset.kpressTheme || "system";
  try {
    mode = localStorage.getItem(key) || mode;
  } catch {
    // localStorage can throw in private/sandboxed contexts; keep the attribute default.
  }
  const resolved =
    mode === "light" || mode === "dark"
      ? mode
      : globalThis.matchMedia?.("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
  root.dataset.kpressTheme = mode;
  root.dataset.kpressResolvedTheme = resolved;
})();
