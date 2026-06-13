/**
 * Menu/popover behavior primitive (`kpress.menu`): the headless engine behind
 * the settings gear and any other segmented-chooser popover. Extracted from
 * the former theme.js `bindSettingsMenu` so widgets (built-in or host) compose
 * it instead of re-implementing open/close/dismiss/marking (see
 * kpress-design.md "Extension and Injection Model", layer B).
 */

/**
 * Wire a popover: toggle on the button, dismiss on outside click or Escape.
 * Visibility is driven by `aria-expanded` on the wrapper. Idempotent — a
 * second bind on the same wrapper returns null.
 *
 * @param {HTMLElement} wrap
 * @param {HTMLElement} button
 * @returns {(() => void) | null} disposer, or null when already bound
 */
export function bindMenu(wrap, button) {
  if (!wrap || !button || wrap.getAttribute("data-kpress-bound") === "true") {
    return null;
  }
  wrap.setAttribute("data-kpress-bound", "true");
  const isOpen = () => wrap.getAttribute("aria-expanded") === "true";
  /** @param {boolean} open */
  const setOpen = (open) => wrap.setAttribute("aria-expanded", open ? "true" : "false");
  /** @param {MouseEvent} event */
  const onButtonClick = (event) => {
    event.stopPropagation();
    setOpen(!isOpen());
  };
  /** @param {MouseEvent} event */
  const onDocumentClick = (event) => {
    if (isOpen() && !wrap.contains(/** @type {Node} */ (event.target))) {
      setOpen(false);
    }
  };
  /** @param {KeyboardEvent} event */
  const onKeydown = (event) => {
    if (event.key === "Escape" && isOpen()) {
      setOpen(false);
    }
  };
  button.addEventListener("click", onButtonClick);
  document.addEventListener("click", onDocumentClick);
  document.addEventListener("keydown", onKeydown);
  return () => {
    button.removeEventListener("click", onButtonClick);
    document.removeEventListener("click", onDocumentClick);
    document.removeEventListener("keydown", onKeydown);
    wrap.removeAttribute("data-kpress-bound");
  };
}

/**
 * Mark the active segment in a chooser group: `aria-checked="true"` on the
 * `[role="menuitemradio"]` child whose `data-*` value matches.
 *
 * @param {HTMLElement | Document} group
 * @param {string} dataKey camelCase dataset key, e.g. "kpressThemeChoice"
 * @param {string} value
 */
export function markChecked(group, dataKey, value) {
  for (const segment of group.querySelectorAll('[role="menuitemradio"]')) {
    const el = /** @type {HTMLElement} */ (segment);
    el.setAttribute("aria-checked", el.dataset[dataKey] === value ? "true" : "false");
  }
}

const kpressGlobal = /** @type {Record<string, unknown>} */ (
  /** @type {Record<string, unknown>} */ (globalThis).kpress ?? {}
);
/** @type {Record<string, unknown>} */ (globalThis).kpress = kpressGlobal;
kpressGlobal.menu = { bindMenu, markChecked };
