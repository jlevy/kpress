// Controls for drawn Mermaid diagrams, as GitHub gives them: a toolbar on each figure
// (copy source, show source, expand), and an expand dialog with zoom and pan buttons plus
// wheel, pinch, drag, and keys.
//
// Opt-in: pass `diagramControls()` as `initKpressDiagrams`'s `controls` option, or
// configure the `diagrams` behavior with it. A page that only draws diagrams never loads
// this module.
//
// The zoom and pan arithmetic is pure (`fitView`, `zoomAbout`, `panBy`, `viewAction`,
// `keyAction`, `wheelView`), so it is tested without a browser. Glyphs come from the KPress
// icon sprites through `icon()`; the server inlines the diagram glyphs
// (static/icons/diagram-icons.svg) only in a document that holds a Mermaid figure. A
// render that lost them -- a host's sanitizer drops inline SVG -- gets them from
// `ensureDiagramSprites`, which fetches each missing sprite from beside this module. A
// host that passes its own `icon` loads neither.

import { icon as spriteIcon } from "./icons.js";

/** How much one zoom step scales: the dialog's buttons, keys, and one wheel notch. */
export const ZOOM_STEP = 1.25;
/** The dialog's zoom bounds, relative to the diagram's natural size. */
export const MIN_SCALE = 0.1;
export const MAX_SCALE = 10;
/** The most the dialog's first view, and reset, enlarge a small diagram to fit. */
export const MAX_FIT_SCALE = 2;
/** How far one pan button press or arrow key moves the diagram, in CSS pixels. */
export const PAN_STEP = 80;
/** How long the copy button shows its result before it returns to idle; code-copy.js's. */
const COPY_STATE_RESET_DELAY_MS = 1200;

/** @typedef {{ scale: number, x: number, y: number }} DiagramView */
/** @typedef {{ width: number, height: number }} Size */
/**
 * @typedef {"zoom-in" | "zoom-out" | "reset" | "pan-up" | "pan-down" | "pan-left" | "pan-right"} ViewActionName
 */
/**
 * The names `icon` and `decorate` receive: the toolbar's `copy`, `toggle-source`, and
 * `expand`; the dialog's view actions; and `close`.
 *
 * @typedef {"copy" | "toggle-source" | "expand" | ViewActionName | "close"} ControlName
 */
/**
 * @typedef {{
 *   icon?: (name: string) => string;
 *   decorate?: (button: HTMLButtonElement, name: ControlName) => void;
 *   copy?: ((button: HTMLButtonElement, text: string) => void) | null;
 *   expand?: boolean;
 * }} DiagramControlsOptions
 */

/** @param {number} value @param {number} low @param {number} high */
function clamp(value, low, high) {
  return Math.min(high, Math.max(low, value));
}

/** @param {number} value */
function round(value) {
  return Math.round(value * 1000) / 1000;
}

/**
 * The view that fits *content* inside *viewport*, centered, enlarged at most
 * `MAX_FIT_SCALE` times.
 *
 * @param {Size} content
 * @param {Size} viewport
 * @returns {DiagramView}
 */
export function fitView(content, viewport) {
  if (!(content.width > 0 && content.height > 0 && viewport.width > 0 && viewport.height > 0)) {
    return { scale: 1, x: 0, y: 0 };
  }
  const scale = clamp(
    Math.min(viewport.width / content.width, viewport.height / content.height, MAX_FIT_SCALE),
    MIN_SCALE,
    MAX_SCALE,
  );
  return {
    scale: round(scale),
    x: round((viewport.width - content.width * scale) / 2),
    y: round((viewport.height - content.height * scale) / 2),
  };
}

/**
 * *view* scaled by *factor* about *origin*, a point in the viewport, which stays put.
 *
 * @param {DiagramView} view
 * @param {number} factor
 * @param {{ x: number, y: number }} origin
 * @returns {DiagramView}
 */
export function zoomAbout(view, factor, origin) {
  const scale = clamp(view.scale * factor, MIN_SCALE, MAX_SCALE);
  const ratio = scale / view.scale;
  return {
    scale: round(scale),
    x: round(origin.x - (origin.x - view.x) * ratio),
    y: round(origin.y - (origin.y - view.y) * ratio),
  };
}

/**
 * *view* moved by (*dx*, *dy*) viewport pixels.
 *
 * @param {DiagramView} view
 * @param {number} dx
 * @param {number} dy
 * @returns {DiagramView}
 */
export function panBy(view, dx, dy) {
  return { scale: view.scale, x: round(view.x + dx), y: round(view.y + dy) };
}

/**
 * The view after one of the dialog's buttons or keys. A zoom keeps the viewport's center
 * still; a pan button moves the view the way its arrow points, as GitHub's do; reset fits.
 *
 * @param {DiagramView} view
 * @param {ViewActionName} action
 * @param {{ content: Size, viewport: Size }} sizes
 * @returns {DiagramView}
 */
export function viewAction(view, action, sizes) {
  const center = { x: sizes.viewport.width / 2, y: sizes.viewport.height / 2 };
  switch (action) {
    case "zoom-in":
      return zoomAbout(view, ZOOM_STEP, center);
    case "zoom-out":
      return zoomAbout(view, 1 / ZOOM_STEP, center);
    case "reset":
      return fitView(sizes.content, sizes.viewport);
    case "pan-up":
      return panBy(view, 0, PAN_STEP);
    case "pan-down":
      return panBy(view, 0, -PAN_STEP);
    case "pan-left":
      return panBy(view, PAN_STEP, 0);
    case "pan-right":
      return panBy(view, -PAN_STEP, 0);
    default:
      return view;
  }
}

/**
 * The dialog action a key names, or null.
 *
 * @param {{ key: string, ctrlKey?: boolean, metaKey?: boolean, altKey?: boolean }} event
 * @returns {ViewActionName | null}
 */
export function keyAction(event) {
  if (event.ctrlKey || event.metaKey || event.altKey) {
    return null;
  }
  /** @type {Record<string, ViewActionName>} */
  const keys = {
    "+": "zoom-in",
    "=": "zoom-in",
    "-": "zoom-out",
    _: "zoom-out",
    0: "reset",
    ArrowUp: "pan-up",
    ArrowDown: "pan-down",
    ArrowLeft: "pan-left",
    ArrowRight: "pan-right",
  };
  return keys[event.key] ?? null;
}

/**
 * The view after a wheel event at *origin*. A pinch, which browsers report as a wheel with
 * the control key, and a wheel with the control or command key held zoom about the
 * pointer; a plain wheel or two-finger scroll pans.
 *
 * @param {DiagramView} view
 * @param {{ deltaX: number, deltaY: number, ctrlKey?: boolean, metaKey?: boolean }} wheel
 * @param {{ x: number, y: number }} origin
 * @returns {DiagramView}
 */
export function wheelView(view, wheel, origin) {
  if (wheel.ctrlKey || wheel.metaKey) {
    return zoomAbout(view, Math.exp(-wheel.deltaY / 200), origin);
  }
  return panBy(view, -wheel.deltaX, -wheel.deltaY);
}

/** @param {DiagramView} view */
export function viewTransform(view) {
  return `translate(${view.x}px, ${view.y}px) scale(${view.scale})`;
}

/**
 * The sprites the controls draw from, relative to this module, each with a symbol that
 * shows it is already in the document.
 */
const SPRITES = /** @type {const} */ ([
  ["../icons/icons.svg", "kpress-icon-copy"],
  ["../icons/diagram-icons.svg", "kpress-icon-zoom-in"],
]);
/** Each document's sprite fetches, by path, so one is fetched at most once. */
/** @type {WeakMap<Document, Map<string, Promise<void>>>} */
const spriteLoads = new WeakMap();

/**
 * Add to *doc* the KPress sprites the controls draw from that it does not hold. A server
 * render inlines them, but a host that sanitizes the render (an untrusted document's
 * allowlist) removes them, and `<use href="#kpress-icon-*">` then draws nothing. Each
 * missing sprite is fetched from beside this module at most once per document and
 * appended to its body, where it outlives the render. The sprite's `style` attribute is
 * replaced through the CSSOM, which a policy without `'unsafe-inline'` styles allows. A
 * failure leaves the buttons labelled but blank, and is reported once.
 *
 * @param {Document} [doc]
 * @returns {Promise<void>}
 */
export function ensureDiagramSprites(doc = document) {
  let loads = spriteLoads.get(doc);
  if (!loads) {
    loads = new Map();
    spriteLoads.set(doc, loads);
  }
  const pending = [];
  for (const [path, marker] of SPRITES) {
    if (doc.getElementById(marker)) {
      continue;
    }
    let load = loads.get(path);
    if (!load) {
      load = fetchSprite(doc, path, marker).catch((error) => {
        console.warn("kpress diagrams: the control glyphs could not be loaded", error);
      });
      loads.set(path, load);
    }
    pending.push(load);
  }
  return Promise.all(pending).then(() => {});
}

/**
 * @param {Document} doc
 * @param {string} path
 * @param {string} marker
 */
async function fetchSprite(doc, path, marker) {
  const response = await fetch(new URL(path, import.meta.url));
  if (!response.ok) {
    throw new Error(`${path}: HTTP ${response.status}`);
  }
  const parsed = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
  const sprite = parsed.documentElement;
  if (sprite.localName !== "svg" || doc.getElementById(marker)) {
    return;
  }
  sprite.removeAttribute("style");
  const adopted = /** @type {SVGSVGElement} */ (
    /** @type {unknown} */ (doc.importNode(sprite, true))
  );
  adopted.style.display = "none";
  adopted.setAttribute("aria-hidden", "true");
  doc.body.append(adopted);
}

/** The sprite glyph each control draws. */
const GLYPHS = Object.freeze({
  copy: "copy",
  "toggle-source": "code",
  expand: "maximize",
  "zoom-in": "zoom-in",
  "zoom-out": "zoom-out",
  reset: "rotate-ccw",
  "pan-up": "chevron-up",
  "pan-down": "chevron-down",
  "pan-left": "chevron-left",
  "pan-right": "chevron-right",
  close: "x",
});

/** The dialog's view actions, in GitHub's order, with their labels. */
const VIEW_ACTIONS = /** @type {const} */ ([
  ["zoom-in", "Zoom in"],
  ["zoom-out", "Zoom out"],
  ["reset", "Reset view"],
  ["pan-up", "Pan up"],
  ["pan-down", "Pan down"],
  ["pan-left", "Pan left"],
  ["pan-right", "Pan right"],
]);

/**
 * @param {HTMLElement} figure
 * @returns {{ source: HTMLElement | null, text: string }}
 */
function figureSource(figure) {
  const source = /** @type {HTMLElement | null} */ (
    figure.querySelector(":scope > .kpress-diagram-source")
  );
  const code = source?.querySelector("code") ?? source;
  return { source, text: (code?.textContent ?? "").trim() };
}

/**
 * Controls for `initKpressDiagrams`.
 *
 * - `icon(name)` returns a button's glyph markup; it defaults to the KPress sprite, which
 *   `ensureDiagramSprites` adds to a document that lacks it.
 * - `decorate(button, name)` runs when a button is made and whenever its label changes, so
 *   a host can add its own classes or tooltip attributes.
 * - `copy(button, text)` takes the copy button over: KPress then attaches no click handler
 *   to it, and the host copies *text* however it copies. `copy: null` omits the button.
 * - `expand: false` omits the expand button and the dialog.
 *
 * @param {DiagramControlsOptions} [options]
 * @returns {import("./diagrams.js").DiagramControls}
 */
export function diagramControls(options = {}) {
  const glyph = options.icon ?? ((/** @type {string} */ name) => spriteIcon(name));
  const decorate = options.decorate ?? (() => {});
  const ownCopy = options.copy;
  const ownIcons = options.icon !== undefined;
  const expandable = options.expand !== false;

  /**
   * @param {ControlName} name
   * @param {string} label
   * @param {string} className
   */
  const button = (name, label, className) => {
    const element = document.createElement("button");
    element.type = "button";
    element.className = `kpress-diagram-button ${className}`;
    element.innerHTML = glyph(GLYPHS[name]);
    setLabel(element, name, label);
    return element;
  };

  /**
   * @param {HTMLButtonElement} element
   * @param {ControlName} name
   * @param {string} label
   */
  const setLabel = (element, name, label) => {
    element.setAttribute("aria-label", label);
    element.setAttribute("title", label);
    decorate(element, name);
  };

  return {
    attach(figure) {
      if (!ownIcons) {
        void ensureDiagramSprites(figure.ownerDocument);
      }
      figure.querySelector(":scope > .kpress-diagram-toolbar")?.remove();
      const toolbar = document.createElement("div");
      toolbar.className = "kpress-diagram-toolbar kpress-no-print";
      /** @type {ReturnType<typeof setTimeout> | null} */
      let copyReset = null;
      /** @type {(() => void) | null} */
      let closeDialog = null;

      /** @type {HTMLButtonElement | null} */
      let copy = null;
      if (ownCopy !== null) {
        copy = button("copy", "Copy diagram source", "kpress-diagram-copy");
        copy.dataset.kpressCopyState = "idle";
        if (ownCopy) {
          ownCopy(copy, figureSource(figure).text);
        }
        toolbar.append(copy);
      }
      const toggle = button("toggle-source", "Show source", "kpress-diagram-toggle-source");
      toolbar.append(toggle);
      const expand = expandable
        ? button("expand", "Expand diagram", "kpress-diagram-expand")
        : null;
      if (expand) {
        toolbar.append(expand);
      }
      figure.prepend(toolbar);

      /**
       * @param {HTMLButtonElement} target
       * @param {"idle" | "copied" | "error"} state
       */
      const setCopyState = (target, state) => {
        const [name, label] =
          state === "copied"
            ? ["check", "Diagram source copied"]
            : state === "error"
              ? ["triangle-alert", "Copy failed"]
              : ["copy", "Copy diagram source"];
        target.innerHTML = glyph(name);
        target.dataset.kpressCopyState = state;
        setLabel(target, "copy", label);
      };

      /** @param {Event} event */
      const onClick = async (event) => {
        const target = /** @type {Element | null} */ (event.target)?.closest?.("button");
        if (!target) {
          return;
        }
        if (target === toggle) {
          figure.dataset.kpressDiagramShowSource =
            figure.dataset.kpressDiagramShowSource === "true" ? "false" : "true";
          applySourceToggle(figure);
        } else if (target === expand) {
          closeDialog?.();
          closeDialog = openDiagramDialog(figure, {
            glyph,
            decorate,
            onClosed: () => {
              closeDialog = null;
            },
          });
        } else if (target === copy && copy && ownCopy === undefined) {
          const text = figureSource(figure).text;
          try {
            await navigator.clipboard.writeText(text);
            setCopyState(copy, "copied");
          } catch {
            setCopyState(copy, "error");
          }
          if (copyReset) {
            clearTimeout(copyReset);
          }
          const reset = copy;
          copyReset = setTimeout(() => {
            copyReset = null;
            setCopyState(reset, "idle");
          }, COPY_STATE_RESET_DELAY_MS);
        }
      };

      /** @param {HTMLElement} figureToUpdate */
      const applySourceToggle = (figureToUpdate) => {
        const rendered = /** @type {HTMLElement | null} */ (
          figureToUpdate.querySelector(":scope > .kpress-diagram-rendered")
        );
        const showSource = !!rendered && figureToUpdate.dataset.kpressDiagramShowSource === "true";
        const { source } = figureSource(figureToUpdate);
        if (rendered) {
          rendered.hidden = showSource;
        }
        if (source) {
          source.hidden = !!rendered && !showSource;
        }
        // An action button whose name says what it does next, not a pressed toggle: the
        // figure's own content says which side is shown.
        setLabel(toggle, "toggle-source", showSource ? "Show diagram" : "Show source");
      };
      toggleUpdates.set(figure, applySourceToggle);

      toolbar.addEventListener("click", onClick);
      return () => {
        toolbar.removeEventListener("click", onClick);
        if (copyReset) {
          clearTimeout(copyReset);
        }
        closeDialog?.();
        closeDialog = null;
        toggleUpdates.delete(figure);
      };
    },
    update(figure) {
      toggleUpdates.get(figure)?.(figure);
    },
  };
}

/** Each attached figure's source-toggle refresh, for `update`. */
const toggleUpdates = new WeakMap();

/**
 * Open *figure*'s drawing in a modal dialog with zoom and pan; returns what closes it. The
 * dialog is placed inside the figure, so it inherits the document's theme tokens, and
 * shows in the top layer.
 *
 * @param {HTMLElement} figure
 * @param {{
 *   glyph?: (name: string) => string;
 *   decorate?: (button: HTMLButtonElement, name: ControlName) => void;
 *   onClosed?: () => void;
 * }} [options]
 * @returns {() => void}
 */
export function openDiagramDialog(figure, options = {}) {
  if (!options.glyph) {
    void ensureDiagramSprites(figure.ownerDocument);
  }
  const glyph = options.glyph ?? ((/** @type {string} */ name) => spriteIcon(name));
  const decorate = options.decorate ?? (() => {});
  const drawing = figure.querySelector(
    ":scope > .kpress-diagram-rendered > svg, :scope > .kpress-diagram-rendered > img",
  );
  const dialog = document.createElement("dialog");
  dialog.className = "kpress-diagram-dialog kpress-no-print";
  dialog.setAttribute("aria-label", "Diagram");
  const controls = document.createElement("div");
  controls.className = "kpress-diagram-dialog-controls";

  /**
   * @param {ControlName} name
   * @param {string} label
   * @param {string} className
   */
  const button = (name, label, className) => {
    const element = document.createElement("button");
    element.type = "button";
    element.className = `kpress-diagram-button ${className}`;
    element.innerHTML = glyph(GLYPHS[name]);
    element.setAttribute("aria-label", label);
    element.setAttribute("title", label);
    decorate(element, name);
    return element;
  };
  for (const [action, label] of VIEW_ACTIONS) {
    const element = button(action, label, "kpress-diagram-view-action");
    element.dataset.kpressDiagramAction = action;
    controls.append(element);
  }
  const close = button("close", "Close", "kpress-diagram-dialog-close");
  controls.append(close);

  const viewport = document.createElement("div");
  viewport.className = "kpress-diagram-viewport";
  viewport.tabIndex = 0;
  const stage = document.createElement("div");
  stage.className = "kpress-diagram-stage";
  if (drawing) {
    const copy = /** @type {HTMLElement} */ (drawing.cloneNode(true));
    // Mermaid sizes its SVG as `width: 100%` up to a `max-width` of its natural width; on
    // the stage it takes that natural width, which the view then scales.
    if (copy.tagName.toLowerCase() === "svg" && copy.style.maxWidth) {
      copy.style.width = copy.style.maxWidth;
      copy.style.maxWidth = "none";
      copy.removeAttribute("width");
    }
    stage.append(copy);
  } else {
    const pre = document.createElement("pre");
    pre.textContent = figureSource(figure).text;
    stage.append(pre);
  }
  viewport.append(stage);
  dialog.append(controls, viewport);
  figure.append(dialog);

  /** @type {DiagramView} */
  let view = { scale: 1, x: 0, y: 0 };
  const sizes = () => {
    const box = viewport.getBoundingClientRect();
    return {
      content: { width: stage.scrollWidth || 1, height: stage.scrollHeight || 1 },
      viewport: { width: box.width, height: box.height },
    };
  };
  /** @param {DiagramView} next */
  const apply = (next) => {
    view = next;
    stage.style.transform = viewTransform(view);
  };
  /** @param {{ clientX: number, clientY: number }} point */
  const local = (point) => {
    const box = viewport.getBoundingClientRect();
    return { x: point.clientX - box.left, y: point.clientY - box.top };
  };

  /** @param {Event} event */
  const onClick = (event) => {
    const target = /** @type {Element | null} */ (event.target)?.closest?.("button");
    if (!target) {
      return;
    }
    if (target === close) {
      closeNow();
      return;
    }
    const action = /** @type {ViewActionName | undefined} */ (
      /** @type {HTMLElement} */ (target).dataset.kpressDiagramAction
    );
    if (action) {
      apply(viewAction(view, action, sizes()));
    }
  };
  /** @param {KeyboardEvent} event */
  const onKey = (event) => {
    const action = keyAction(event);
    if (action) {
      event.preventDefault();
      apply(viewAction(view, action, sizes()));
    }
  };
  /** @param {WheelEvent} event */
  const onWheel = (event) => {
    event.preventDefault();
    apply(wheelView(view, event, local(event)));
  };
  /** @type {{ id: number, x: number, y: number } | null} */
  let drag = null;
  /** @param {PointerEvent} event */
  const onPointerDown = (event) => {
    if (event.button !== 0) {
      return;
    }
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY };
    viewport.setPointerCapture?.(event.pointerId);
    viewport.classList.add("kpress-diagram-dragging");
  };
  /** @param {PointerEvent} event */
  const onPointerMove = (event) => {
    if (!drag || drag.id !== event.pointerId) {
      return;
    }
    apply(panBy(view, event.clientX - drag.x, event.clientY - drag.y));
    drag = { id: drag.id, x: event.clientX, y: event.clientY };
  };
  const onPointerUp = () => {
    drag = null;
    viewport.classList.remove("kpress-diagram-dragging");
  };
  const onClose = () => closeNow();

  dialog.addEventListener("click", onClick);
  dialog.addEventListener("keydown", onKey);
  dialog.addEventListener("close", onClose);
  viewport.addEventListener("wheel", onWheel, { passive: false });
  viewport.addEventListener("pointerdown", onPointerDown);
  viewport.addEventListener("pointermove", onPointerMove);
  viewport.addEventListener("pointerup", onPointerUp);
  viewport.addEventListener("pointercancel", onPointerUp);

  let closed = false;
  function closeNow() {
    if (closed) {
      return;
    }
    closed = true;
    dialog.removeEventListener("click", onClick);
    dialog.removeEventListener("keydown", onKey);
    dialog.removeEventListener("close", onClose);
    viewport.removeEventListener("wheel", onWheel);
    viewport.removeEventListener("pointerdown", onPointerDown);
    viewport.removeEventListener("pointermove", onPointerMove);
    viewport.removeEventListener("pointerup", onPointerUp);
    viewport.removeEventListener("pointercancel", onPointerUp);
    if (dialog.open) {
      dialog.close();
    }
    dialog.remove();
    options.onClosed?.();
  }

  if (typeof dialog.showModal === "function") {
    dialog.showModal();
  } else {
    dialog.setAttribute("open", "");
  }
  apply(fitView(sizes().content, sizes().viewport));
  viewport.focus?.({ preventScroll: true });
  return closeNow;
}
