// Draw a document's Mermaid diagrams.
//
// The server marks a `mermaid` fence as a figure that holds its source
// (`[data-kpress-diagram="mermaid"]` around `.kpress-diagram-source`; see
// `_render_mermaid_diagram` in format/markdown.py). KPress does not ship Mermaid: a page or
// host supplies it, either as `globalThis.mermaid` (the zero-configuration `diagrams`
// behavior) or through `initKpressDiagrams(root, {mermaid})`, which also accepts an ES
// module namespace or a loader, so a host that imports Mermaid on demand never sets a
// global.
//
// `initKpressDiagrams` draws each figure in document order and returns a binding:
// `ready` settles when every figure has drawn or failed, `rerender()` draws them again (a
// theme change does this by itself), and `dispose()` stops drawing and leaves the figures
// as they are. A figure that fails shows Mermaid's message above its source
// (`.kpress-diagram-error`). The `controls` option attaches a toolbar to each figure;
// `diagram-controls.js` provides one, and is opt-in so a page that only draws diagrams
// does not load it.
//
// Placement `"document"` puts Mermaid's SVG in the page, so it follows the theme, prints,
// and selects with the prose. Placement `"image"` shows it as
// `<img src="data:image/svg+xml…">`, where it can run no script, load nothing, and navigate
// nowhere, whatever Mermaid let through: the choice for content the host does not trust.

import { behaviors, off, on } from "./runtime.js";

/** A Mermaid figure in KPress's markup. */
export const MERMAID_FIGURE_SELECTOR = '[data-kpress-diagram="mermaid"]';

/**
 * Mermaid's own default `maxTextSize`, which GitHub keeps. A longer source is refused with
 * a message rather than drawn as Mermaid's "Maximum text size" placeholder. A host's
 * `config.maxTextSize` replaces it.
 */
export const MAX_DIAGRAM_TEXT = 50_000;

/**
 * The face and size Mermaid's default themes draw labels in (Mermaid 12's
 * `themeVariables.fontFamily` and `fontSize`). Image placement measures labels in a host
 * element that carries these as a `style` attribute; see `measuringHost`.
 */
const MERMAID_DEFAULT_FONT_FAMILY = '"trebuchet ms", verdana, arial, sans-serif';
const MERMAID_DEFAULT_FONT_SIZE = "16px";

/**
 * @typedef {{
 *   initialize?: (config: Record<string, unknown>) => void;
 *   render: (id: string, source: string, container?: Element) => Promise<string | { svg?: string }> | string | { svg?: string };
 * }} MermaidApi
 */

/**
 * What the `mermaid` option accepts: the API object, an ES module namespace whose
 * `default` is the API, or a function that returns either (or a promise of either), called
 * once, and only when the root holds a diagram.
 *
 * @typedef {MermaidApi | { default: MermaidApi } | (() => unknown)} MermaidSource
 */

/**
 * A toolbar attached to each figure. `attach` returns what removes it; `update` runs after
 * every draw, clear, and failure, so the controls can follow the figure's status.
 *
 * @typedef {{
 *   attach(figure: HTMLElement): () => void;
 *   update?(figure: HTMLElement): void;
 * }} DiagramControls
 */

/**
 * @typedef {{
 *   mermaid?: MermaidSource | null;
 *   config?: Record<string, unknown>;
 *   theme?: () => "light" | "dark";
 *   subscribeTheme?: (listener: () => void) => () => void;
 *   placement?: "document" | "image";
 *   controls?: DiagramControls | null;
 *   yieldBetween?: () => Promise<void>;
 * }} DiagramOptions
 */

/**
 * @typedef {{
 *   figures: HTMLElement[];
 *   ready: Promise<void>;
 *   rerender(): void;
 *   dispose(): void;
 * }} DiagramBinding
 */

let diagramSequence = 0;

/**
 * The theme and placement each drawn figure was drawn in. A new binding over the same
 * figures keeps a drawing that still matches and redraws one that does not: the runtime
 * rebinds every behavior on `theme:change`, so this is how a rebind follows the theme.
 *
 * @type {WeakMap<HTMLElement, string>}
 */
const drawnAs = new WeakMap();

/** @param {unknown} value @returns {value is Record<string, unknown>} */
function isPlainObject(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

/**
 * *base* with *overrides* merged in, recursively for nested plain objects, so a host can
 * set one `flowchart` key without dropping KPress's others.
 *
 * @param {Record<string, unknown>} base
 * @param {Record<string, unknown>} [overrides]
 * @returns {Record<string, unknown>}
 */
function mergeConfig(base, overrides) {
  /** @type {Record<string, unknown>} */
  const merged = { ...base };
  for (const [key, value] of Object.entries(overrides ?? {})) {
    const current = merged[key];
    merged[key] =
      isPlainObject(current) && isPlainObject(value) ? mergeConfig(current, value) : value;
  }
  return merged;
}

/**
 * Mermaid's site configuration for a resolved theme: GitHub's observable settings, with
 * `securityLevel: "strict"`, which sanitizes labels as GitHub's `antiscript` does and also
 * disables `click` navigation. A diagram's own `%%{init}%%` or front-matter theme wins.
 *
 * @param {"light" | "dark"} theme
 * @returns {Record<string, unknown>}
 */
export function kpressMermaidConfig(theme) {
  return {
    startOnLoad: false,
    securityLevel: "strict",
    suppressErrorRendering: true,
    theme: theme === "dark" ? "dark" : "default",
    flowchart: { diagramPadding: 48 },
    sequence: { diagramMarginY: 40 },
  };
}

/** @param {unknown} candidate @returns {candidate is MermaidApi} */
function isMermaidApi(candidate) {
  return (
    typeof candidate === "object" &&
    candidate !== null &&
    "render" in candidate &&
    typeof candidate.render === "function"
  );
}

/**
 * The Mermaid API in *value*: the API itself, or an ES module namespace's `default`.
 *
 * @param {unknown} value
 * @returns {MermaidApi}
 */
function mermaidApiFrom(value) {
  if (isMermaidApi(value)) {
    return value;
  }
  const fallback =
    value && typeof value === "object" && "default" in value
      ? /** @type {{ default: unknown }} */ (value).default
      : null;
  if (isMermaidApi(fallback)) {
    return fallback;
  }
  throw new TypeError("The Mermaid module has no render function");
}

/**
 * A message for *error*, Mermaid's own when it gave one.
 *
 * @param {unknown} error
 * @returns {string}
 */
export function diagramErrorMessage(error) {
  const message =
    error instanceof Error
      ? error.message
      : error && typeof error === "object" && "message" in error
        ? String(/** @type {{ message: unknown }} */ (error).message)
        : String(error ?? "");
  return message.trim() || "Mermaid could not draw this diagram.";
}

/** @param {number} value */
function round(value) {
  return Math.round(value * 1000) / 1000;
}

/**
 * *svg*, Mermaid's markup, as a standalone SVG document an `<img>` can load: serialized as
 * XML (Mermaid's HTML labels hold `<br>`) and sized to its view box.
 *
 * @param {string} svg
 * @returns {string}
 */
export function svgImageSource(svg) {
  const template = document.createElement("template");
  template.innerHTML = svg;
  const element = template.content.querySelector("svg");
  if (!element) {
    throw new Error("Mermaid returned no SVG");
  }
  const box = (element.getAttribute("viewBox") || "").split(/[\s,]+/).map(Number);
  if (box.length === 4 && box[2] > 0 && box[3] > 0) {
    element.setAttribute("width", String(round(box[2])));
    element.setAttribute("height", String(round(box[3])));
  }
  element.removeAttribute("style");
  element.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  const text = new XMLSerializer().serializeToString(element);
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(text)}`;
}

/**
 * Wrap a bare Mermaid source block (a host's `<pre>`, such as GitHub's
 * `<pre lang="mermaid">`) in KPress's figure markup, so `initKpressDiagrams` draws it like
 * a figure the server rendered. A figure is returned as it is.
 *
 * @param {Element} element
 * @returns {HTMLElement}
 */
export function mermaidFigureFor(element) {
  if (element.matches(MERMAID_FIGURE_SELECTOR)) {
    return /** @type {HTMLElement} */ (element);
  }
  const figure = document.createElement("figure");
  figure.className = "kpress-diagram kpress-mermaid";
  figure.dataset.kpressDiagram = "mermaid";
  figure.dataset.kpressDiagramProvider = "mermaid";
  figure.dataset.kpressDiagramStatus = "source";
  element.replaceWith(figure);
  element.classList.add("kpress-diagram-source");
  figure.append(element);
  return figure;
}

/**
 * The figure's source block and the diagram text it holds.
 *
 * @param {HTMLElement} figure
 * @returns {{ source: HTMLElement | null, text: string }}
 */
export function diagramSource(figure) {
  const source = /** @type {HTMLElement | null} */ (
    figure.querySelector(":scope > .kpress-diagram-source")
  );
  const code = source?.querySelector("code") ?? source;
  return { source, text: (code?.textContent ?? "").trim() };
}

/**
 * The resolved theme around *element*: the nearest `data-kpress-resolved-theme`, which
 * the theme engine stamps on the root and an embedding host may stamp on its scope.
 *
 * @param {Element | null} element
 * @returns {"light" | "dark"}
 */
function resolvedThemeAround(element) {
  const scope =
    element?.closest("[data-kpress-resolved-theme]") ??
    document.documentElement.closest("[data-kpress-resolved-theme]");
  return scope?.getAttribute("data-kpress-resolved-theme") === "dark" ? "dark" : "light";
}

/** @param {() => void} listener */
function subscribeRuntimeTheme(listener) {
  on("theme:change", listener);
  return () => off("theme:change", listener);
}

/**
 * Where image placement measures a diagram. Mermaid lays a diagram out in the page,
 * reading each label's box, and sets the labels' face and size with a `<style>` inside its
 * SVG. A strict content security policy admits no `<style>` element, only `style`
 * attributes, so the labels would be measured in the page's face and drawn, inside the
 * image, in Mermaid's: wider text clipped. This host carries Mermaid's face and size as an
 * attribute, so both agree.
 *
 * @param {Record<string, unknown>} config
 * @returns {HTMLElement}
 */
function measuringHost(config) {
  const variables = isPlainObject(config.themeVariables) ? config.themeVariables : {};
  const family = String(variables.fontFamily ?? config.fontFamily ?? MERMAID_DEFAULT_FONT_FAMILY);
  const size = String(variables.fontSize ?? MERMAID_DEFAULT_FONT_SIZE);
  const host = document.createElement("div");
  host.setAttribute(
    "style",
    `position:fixed;left:-100000px;top:0;width:1200px;visibility:hidden;font-family:${family};font-size:${size};line-height:normal;`,
  );
  host.setAttribute("aria-hidden", "true");
  document.body.append(host);
  return host;
}

/**
 * Remove a figure's drawing and error note, and show its source.
 *
 * @param {HTMLElement} figure
 */
function clearDrawing(figure) {
  figure.querySelector(":scope > .kpress-diagram-rendered")?.remove();
  figure.querySelector(":scope > .kpress-diagram-error")?.remove();
  figure.dataset.kpressDiagramStatus = "source";
  const { source } = diagramSource(figure);
  if (source) {
    source.hidden = false;
  }
}

/**
 * Show *message* above the figure's source, and the source itself.
 *
 * @param {HTMLElement} figure
 * @param {string} message
 */
export function showDiagramError(figure, message) {
  figure.querySelector(":scope > .kpress-diagram-rendered")?.remove();
  figure.querySelector(":scope > .kpress-diagram-error")?.remove();
  figure.dataset.kpressDiagramStatus = "error";
  const note = document.createElement("div");
  note.className = "kpress-diagram-error";
  note.setAttribute("role", "note");
  const title = document.createElement("strong");
  title.textContent = "Could not draw this diagram.";
  const detail = document.createElement("pre");
  detail.className = "kpress-diagram-error-detail";
  // Text only: the message can quote the diagram's source.
  detail.textContent = message;
  note.append(title, detail);
  const { source } = diagramSource(figure);
  figure.insertBefore(note, source);
  if (source) {
    source.hidden = false;
  }
}

/**
 * @param {string} svg
 * @param {"document" | "image"} placement
 * @returns {HTMLElement}
 */
function renderedElement(svg, placement) {
  const rendered = document.createElement("div");
  rendered.className = "kpress-diagram-rendered";
  if (placement === "image") {
    const image = document.createElement("img");
    image.className = "kpress-diagram-image";
    image.alt = "Mermaid diagram";
    image.src = svgImageSource(svg);
    rendered.append(image);
  } else {
    rendered.innerHTML = svg;
  }
  return rendered;
}

/**
 * Draw every Mermaid figure under *root*.
 *
 * Mermaid comes from `options.mermaid`, else `globalThis.mermaid`; with neither, the
 * figures keep their source and `ready` resolves at once. Mermaid is configured before each
 * figure with `kpressMermaidConfig(theme)` merged with `options.config`, so another
 * binding's configuration never leaks into this one's diagrams.
 *
 * @param {ParentNode} [root]
 * @param {DiagramOptions} [options]
 * @returns {DiagramBinding}
 */
export function initKpressDiagrams(root = document, options = {}) {
  const placement = options.placement === "image" ? "image" : "document";
  const controls = options.controls ?? null;
  const yieldBetween =
    options.yieldBetween ?? (() => new Promise((resolve) => setTimeout(resolve, 0)));
  /** @type {HTMLElement[]} */
  const figures = [];
  for (const figure of root.querySelectorAll(MERMAID_FIGURE_SELECTOR)) {
    if (figure instanceof HTMLElement) {
      figures.push(figure);
    }
  }
  const theme =
    options.theme ??
    (() => resolvedThemeAround(figures[0] ?? (root instanceof Element ? root : null)));
  const mermaidSource =
    options.mermaid ?? /** @type {{ mermaid?: unknown }} */ (globalThis).mermaid ?? null;

  let disposed = false;
  let generation = 0;
  /** @type {Array<() => void>} */
  const cleanups = [];
  /** @type {Promise<MermaidApi> | null} */
  let loading = null;

  const loadMermaid = () => {
    loading ??= Promise.resolve(
      typeof mermaidSource === "function" ? mermaidSource() : mermaidSource,
    ).then(mermaidApiFrom);
    return loading;
  };

  /** @param {HTMLElement} figure */
  const updateControls = (figure) => {
    try {
      controls?.update?.(figure);
    } catch (error) {
      console.error("kpress: diagram controls update failed", error);
    }
  };

  /**
   * @param {HTMLElement} figure
   * @param {MermaidApi} mermaid
   * @param {number} pass
   */
  async function drawFigure(figure, mermaid, pass) {
    const { source, text } = diagramSource(figure);
    if (!text) {
      return;
    }
    const currentTheme = theme();
    const look = `${currentTheme} ${placement}`;
    const config = mergeConfig(kpressMermaidConfig(currentTheme), options.config);
    const limit = typeof config.maxTextSize === "number" ? config.maxTextSize : MAX_DIAGRAM_TEXT;
    if (text.length > limit) {
      showDiagramError(
        figure,
        `This diagram's source is ${text.length.toLocaleString("en-US")} characters; Mermaid draws at most ${limit.toLocaleString("en-US")}.`,
      );
      updateControls(figure);
      return;
    }
    figure.dataset.kpressDiagramStatus = "rendering";
    diagramSequence += 1;
    const id = `kpress-mermaid-${diagramSequence}`;
    const host = placement === "image" ? measuringHost(config) : null;
    try {
      mermaid.initialize?.(config);
      const result = await mermaid.render(id, text, host ?? undefined);
      if (disposed || pass !== generation) {
        if (figure.dataset.kpressDiagramStatus === "rendering") {
          figure.dataset.kpressDiagramStatus = "source";
        }
        return;
      }
      const svg = typeof result === "string" ? result : result?.svg || "";
      if (!svg) {
        throw new Error("Mermaid returned no SVG");
      }
      figure.querySelector(":scope > .kpress-diagram-error")?.remove();
      figure.insertBefore(renderedElement(svg, placement), source);
      if (source) {
        source.hidden = true;
      }
      figure.dataset.kpressDiagramStatus = "rendered";
      drawnAs.set(figure, look);
    } catch (error) {
      // Mermaid leaves its scratch element in the page when a render throws.
      document.getElementById(`d${id}`)?.remove();
      if (disposed || pass !== generation) {
        return;
      }
      showDiagramError(figure, diagramErrorMessage(error));
    } finally {
      host?.remove();
    }
    updateControls(figure);
  }

  /** @param {number} pass */
  async function drawAll(pass) {
    const look = `${theme()} ${placement}`;
    const pending = figures.filter(
      (figure) => figure.dataset.kpressDiagramStatus !== "rendered" || drawnAs.get(figure) !== look,
    );
    if (!pending.length || !mermaidSource) {
      return;
    }
    for (const figure of pending) {
      if (figure.dataset.kpressDiagramStatus === "rendered") {
        clearDrawing(figure);
        updateControls(figure);
      }
    }
    let mermaid;
    try {
      mermaid = await loadMermaid();
    } catch (error) {
      if (disposed || pass !== generation) {
        return;
      }
      for (const figure of pending) {
        showDiagramError(figure, `Mermaid could not load: ${diagramErrorMessage(error)}`);
        updateControls(figure);
      }
      return;
    }
    for (const figure of pending) {
      if (disposed || pass !== generation) {
        return;
      }
      await drawFigure(figure, mermaid, pass);
      await yieldBetween();
    }
  }

  if (controls) {
    for (const figure of figures) {
      try {
        cleanups.push(controls.attach(figure));
      } catch (error) {
        console.error("kpress: diagram controls attach failed", error);
      }
      updateControls(figure);
    }
  }

  generation += 1;
  let drawing = drawAll(generation);

  if (figures.length && mermaidSource) {
    const subscribe = options.subscribeTheme ?? subscribeRuntimeTheme;
    cleanups.push(subscribe(() => binding.rerender()));
  }

  /** @type {DiagramBinding} */
  const binding = {
    figures,
    get ready() {
      return drawing;
    },
    rerender() {
      if (disposed) {
        return;
      }
      generation += 1;
      const pass = generation;
      for (const figure of figures) {
        clearDrawing(figure);
        updateControls(figure);
      }
      drawing = drawing.then(() => drawAll(pass));
    },
    dispose() {
      if (disposed) {
        return;
      }
      disposed = true;
      for (const cleanup of cleanups.splice(0)) {
        try {
          cleanup();
        } catch (error) {
          console.error("kpress: diagram cleanup failed", error);
        }
      }
    },
  };
  return binding;
}

// The zero-configuration path: a page that defines `globalThis.mermaid` gets its diagrams
// drawn. A host passes options with `kpress.behaviors.configure("diagrams", {...})`, or
// calls `initKpressDiagrams` itself.
behaviors.register("diagrams", {
  bind: (root, config) => {
    const binding = initKpressDiagrams(
      /** @type {ParentNode} */ (root),
      /** @type {DiagramOptions} */ (config),
    );
    return () => binding.dispose();
  },
});
