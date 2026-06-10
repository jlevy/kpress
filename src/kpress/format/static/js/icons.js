// KPress client icon helper. The glyphs live in the SVG sprite
// (static/icons/icons.svg), which the server inlines once per document. This only builds
// a `<use>` reference to a sprite symbol -- there is no SVG markup in JS. Icon-only: the
// visible label belongs in aria-label/title on the control, not here.

/**
 * Reference a sprite symbol by name (e.g. "copy", "check", "triangle-alert").
 * @param {string} name
 * @param {string} [className]
 * @returns {string}
 */
export function icon(name, className = "") {
  const cls = className ? ` class="${className}"` : "";
  return `<svg${cls} aria-hidden="true"><use href="#kpress-icon-${name}"></use></svg>`;
}
