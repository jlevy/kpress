// KPress pre-paint bootstrap. Inlined render-blocking into <head> by render_page so
// persisted reader preferences are applied before first paint (no flash of the wrong
// theme or fonts). It is a classic IIFE (not an ES module) and reads the server-set
// `data-kpress-theme` attribute, so the renderer never interpolates anything into this
// source -- it lives here, in a real JS file.
//
// It runs before the module runtime exists, so it reads raw localStorage: hosts that
// swap the kpress.storage adapter (e.g. cookies) re-sync at runtime init; embedded
// hosts never load this bootstrap at all (fragment path).
(() => {
  const root = document.documentElement;
  /** @param {string} key */
  const stored = (key) => {
    try {
      return localStorage.getItem(key);
    } catch {
      // localStorage can throw in private/sandboxed contexts; keep defaults.
      return null;
    }
  };

  // Theme: resolve `system` via the OS preference; always stamped.
  const mode = stored("kpress.theme") || root.dataset.kpressTheme || "system";
  const resolved =
    mode === "light" || mode === "dark"
      ? mode
      : globalThis.matchMedia?.("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
  root.dataset.kpressTheme = mode;
  root.dataset.kpressResolvedTheme = resolved;

  // Other persisted reader preferences: stamped only when a choice exists
  // (CSS defaults apply otherwise).
  const proseFont = stored("kpress.proseFont");
  if (proseFont) {
    root.dataset.kpressProseFont = proseFont;
  }
  const fontSet = stored("kpress.fontSet");
  if (fontSet) {
    root.dataset.kpressFontSet = fontSet;
  }
})();
