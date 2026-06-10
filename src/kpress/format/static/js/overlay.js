/**
 * Shared overlay/positioning primitive for KPress.
 *
 * Provides viewport-aware placement, dismiss handlers (Escape, resize,
 * outside-click), and backdrop management used by tooltips, video popovers,
 * and the table-of-contents drawer.
 *
 * Floating-UI reconsider tripwire: adopt Floating UI if and only if the
 * overlay system requires multi-axis collision detection with simultaneous
 * flip + shift, OR virtual element anchoring for non-DOM triggers. Until
 * then, the cost of a JS runtime dependency is not justified.
 */

import { addViewportResizeListener, resolveKpressViewport } from "./viewport.js";

export const OVERLAY_VIEWPORT_MARGIN_PX = 10;
export const OVERLAY_DEFAULT_GAP_PX = 10;

/**
 * @typedef {{ top: number; bottom: number; left: number; right: number; width: number; height: number }} TriggerRect
 * @typedef {{ width: number; height: number }} OverlaySize
 * @typedef {{
 *   viewportWidth: number;
 *   viewportHeight: number;
 *   preferred?: "top" | "bottom" | "left" | "right";
 *   gap?: number;
 *   margin?: number;
 * }} PositionOptions
 * @typedef {{ side: "top" | "bottom" | "left" | "right"; top: number; left: number }} PositionResult
 */

/**
 * Compute viewport-aware position for an overlay element relative to a trigger.
 *
 * Attempts the preferred side, flipping to the opposite if there is not enough
 * room. Clamps the cross-axis so the overlay stays within viewport margins.
 *
 * @param {TriggerRect} trigger - bounding rect of the trigger element
 * @param {OverlaySize} overlay - measured width/height of the overlay
 * @param {PositionOptions} options
 * @returns {PositionResult}
 */
export function computePosition(trigger, overlay, options) {
  const preferred = options.preferred ?? "bottom";
  const gap = options.gap ?? OVERLAY_DEFAULT_GAP_PX;
  const margin = options.margin ?? OVERLAY_VIEWPORT_MARGIN_PX;
  const vw = options.viewportWidth;
  const vh = options.viewportHeight;

  /** @param {number} value @param {number} min @param {number} max */
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  if (preferred === "right" || preferred === "left") {
    const fitsRight = trigger.right + gap + overlay.width + margin <= vw;
    const fitsLeft = trigger.left - gap - overlay.width >= margin;
    const side =
      preferred === "right"
        ? fitsRight
          ? "right"
          : fitsLeft
            ? "left"
            : "right"
        : fitsLeft
          ? "left"
          : fitsRight
            ? "right"
            : "left";

    const left =
      side === "right"
        ? Math.min(trigger.right + gap, vw - overlay.width - margin)
        : Math.max(margin, trigger.left - gap - overlay.width);

    const centerY = trigger.top + trigger.height / 2 - overlay.height / 2;
    const top = clamp(centerY, margin, vh - overlay.height - margin);

    return { side, top, left };
  }

  const fitsBottom = trigger.bottom + gap + overlay.height + margin <= vh;
  const fitsTop = trigger.top - gap - overlay.height >= margin;
  const side =
    preferred === "bottom"
      ? fitsBottom
        ? "bottom"
        : fitsTop
          ? "top"
          : "bottom"
      : fitsTop
        ? "top"
        : fitsBottom
          ? "bottom"
          : "top";

  const top =
    side === "bottom" ? trigger.bottom + gap : Math.max(margin, trigger.top - gap - overlay.height);

  const centerX = trigger.left + trigger.width / 2 - overlay.width / 2;
  const left = clamp(centerX, margin, vw - overlay.width - margin);

  return { side, top, left };
}

/**
 * Register an Escape-key dismiss handler on the document.
 *
 * @param {() => void} callback
 * @returns {() => void} cleanup function to remove the listener
 */
export function dismissOnEscape(callback) {
  /** @param {KeyboardEvent} event */
  const handler = (event) => {
    if (event.key === "Escape") {
      callback();
    }
  };
  document.addEventListener("keydown", handler);
  return () => document.removeEventListener("keydown", handler);
}

/**
 * Register a viewport resize dismiss handler.
 *
 * @param {() => void} callback
 * @param {Document | Element | null | undefined} [viewport]
 * @returns {() => void} cleanup function to remove the listener
 */
export function dismissOnResize(callback, viewport = document) {
  return addViewportResizeListener(resolveKpressViewport(viewport), callback);
}

/**
 * Register a click-outside dismiss handler for an overlay element.
 *
 * @param {Element | null} overlay
 * @param {() => void} callback
 * @returns {() => void} cleanup function to remove the listener
 */
export function dismissOnOutsideClick(overlay, callback) {
  /** @param {MouseEvent} event */
  const handler = (event) => {
    if (!overlay || !(event.target instanceof Node)) {
      return;
    }
    if (!overlay.contains(event.target)) {
      callback();
    }
  };
  document.addEventListener("click", handler);
  return () => document.removeEventListener("click", handler);
}

/**
 * Toggle a backdrop element's visibility.
 *
 * @param {Element | null} backdrop
 * @param {boolean} visible
 */
export function toggleBackdrop(backdrop, visible) {
  if (!backdrop) {
    return;
  }
  backdrop.classList.toggle("kpress-visible", visible);
  backdrop.setAttribute("aria-hidden", String(!visible));
}
