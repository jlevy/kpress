import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  diagramControls,
  fitView,
  keyAction,
  MAX_FIT_SCALE,
  MAX_SCALE,
  MIN_SCALE,
  PAN_STEP,
  panBy,
  viewAction,
  viewTransform,
  wheelView,
  ZOOM_STEP,
  zoomAbout,
} from "../../src/kpress/format/static/js/diagram-controls.js";
import {
  diagramErrorMessage,
  initKpressDiagrams,
  kpressMermaidConfig,
  MAX_DIAGRAM_TEXT,
  mermaidFigureFor,
} from "../../src/kpress/format/static/js/diagrams.js";
import { emit } from "../../src/kpress/format/static/js/runtime.js";

const FIGURE = (source, attributes = "") => `
  <figure class="kpress-diagram kpress-mermaid" data-kpress-diagram="mermaid"
    data-kpress-diagram-provider="mermaid" data-kpress-diagram-status="source" ${attributes}>
    <pre class="kpress-diagram-source"><code class="language-mermaid">${source}</code></pre>
  </figure>`;

/** A stand-in Mermaid whose `render` draws the source's first line as an SVG label. */
function fakeMermaid(render) {
  return {
    initialize: vi.fn(),
    render: vi.fn(
      render ??
        (async (id, text) => ({
          svg: `<svg id="${id}" viewBox="0 0 120 40" style="max-width: 120px;"><text>${text.split("\n")[0]}</text></svg>`,
        })),
    ),
  };
}

const noYield = () => Promise.resolve();
const figures = () => [...document.querySelectorAll(".kpress-mermaid")];

beforeEach(() => {
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-kpress-resolved-theme");
  delete globalThis.mermaid;
  vi.useRealTimers();
});

afterEach(() => {
  delete globalThis.mermaid;
});

describe("diagram view arithmetic", () => {
  it("fits content centered, never enlarging past MAX_FIT_SCALE", () => {
    expect(fitView({ width: 400, height: 100 }, { width: 800, height: 400 })).toEqual({
      scale: MAX_FIT_SCALE,
      x: 0,
      y: 100,
    });
    expect(fitView({ width: 2000, height: 500 }, { width: 1000, height: 500 })).toEqual({
      scale: 0.5,
      x: 0,
      y: 125,
    });
    expect(fitView({ width: 0, height: 10 }, { width: 10, height: 10 })).toEqual({
      scale: 1,
      x: 0,
      y: 0,
    });
  });

  it("zooms about a point that stays put, within the bounds", () => {
    const view = zoomAbout({ scale: 1, x: 0, y: 0 }, 2, { x: 100, y: 50 });
    expect(view).toEqual({ scale: 2, x: -100, y: -50 });
    // The origin maps to the same content point before and after.
    expect((100 - view.x) / view.scale).toBe(100);
    expect(zoomAbout({ scale: 9, x: 0, y: 0 }, 4, { x: 0, y: 0 }).scale).toBe(MAX_SCALE);
    expect(zoomAbout({ scale: 0.2, x: 0, y: 0 }, 0.1, { x: 0, y: 0 }).scale).toBe(MIN_SCALE);
  });

  it("maps buttons and keys to view actions", () => {
    const sizes = { content: { width: 100, height: 100 }, viewport: { width: 200, height: 200 } };
    const start = { scale: 1, x: 0, y: 0 };
    expect(viewAction(start, "zoom-in", sizes).scale).toBe(ZOOM_STEP);
    expect(viewAction(start, "zoom-out", sizes).scale).toBe(0.8);
    expect(viewAction(start, "pan-up", sizes)).toEqual({ scale: 1, x: 0, y: PAN_STEP });
    expect(viewAction(start, "pan-right", sizes)).toEqual({ scale: 1, x: -PAN_STEP, y: 0 });
    expect(viewAction({ scale: 3, x: 9, y: 9 }, "reset", sizes)).toEqual(
      fitView(sizes.content, sizes.viewport),
    );

    expect(keyAction({ key: "+" })).toBe("zoom-in");
    expect(keyAction({ key: "_" })).toBe("zoom-out");
    expect(keyAction({ key: "0" })).toBe("reset");
    expect(keyAction({ key: "ArrowLeft" })).toBe("pan-left");
    expect(keyAction({ key: "+", metaKey: true })).toBeNull();
    expect(keyAction({ key: "a" })).toBeNull();
  });

  it("pans on a plain wheel and zooms on a pinch", () => {
    const start = { scale: 1, x: 0, y: 0 };
    expect(wheelView(start, { deltaX: 10, deltaY: 20 }, { x: 0, y: 0 })).toEqual(
      panBy(start, -10, -20),
    );
    expect(wheelView(start, { deltaX: 0, deltaY: -200, ctrlKey: true }, { x: 0, y: 0 }).scale).toBe(
      Math.round(Math.E * 1000) / 1000,
    );
    expect(viewTransform({ scale: 2, x: 3, y: 4 })).toBe("translate(3px, 4px) scale(2)");
  });
});

describe("initKpressDiagrams", () => {
  it("draws with an injected Mermaid module and never needs a global", async () => {
    document.body.innerHTML = FIGURE("graph TD\nA--&gt;B");
    const mermaid = fakeMermaid();

    const binding = initKpressDiagrams(document, {
      mermaid: { default: mermaid },
      yieldBetween: noYield,
    });
    await binding.ready;

    const [figure] = figures();
    expect(globalThis.mermaid).toBeUndefined();
    expect(mermaid.render).toHaveBeenCalledWith(
      expect.stringMatching(/^kpress-mermaid-\d+$/),
      "graph TD\nA-->B",
      undefined,
    );
    expect(figure.dataset.kpressDiagramStatus).toBe("rendered");
    expect(figure.querySelector(".kpress-diagram-rendered svg text")?.textContent).toBe("graph TD");
    expect(figure.querySelector(".kpress-diagram-source").hidden).toBe(true);
    expect(binding.figures).toEqual([figure]);
  });

  it("merges the host's configuration over KPress's for the host's theme", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    const mermaid = fakeMermaid();

    await initKpressDiagrams(document, {
      mermaid,
      theme: () => "dark",
      config: { flowchart: { curve: "basis" }, fontFamily: "serif" },
      yieldBetween: noYield,
    }).ready;

    expect(mermaid.initialize).toHaveBeenCalledWith({
      ...kpressMermaidConfig("dark"),
      flowchart: { diagramPadding: 48, curve: "basis" },
      fontFamily: "serif",
    });
    expect(kpressMermaidConfig("dark").theme).toBe("dark");
    expect(kpressMermaidConfig("light")).toMatchObject({
      theme: "default",
      securityLevel: "strict",
      startOnLoad: false,
    });
  });

  it("calls a loader once, and only when the root holds a diagram", async () => {
    const mermaid = fakeMermaid();
    const loader = vi.fn(async () => ({ default: mermaid }));

    await initKpressDiagrams(document, { mermaid: loader }).ready;
    expect(loader).not.toHaveBeenCalled();

    document.body.innerHTML = FIGURE("graph TD") + FIGURE("graph LR");
    await initKpressDiagrams(document, { mermaid: loader, yieldBetween: noYield }).ready;
    expect(loader).toHaveBeenCalledTimes(1);
    expect(mermaid.render).toHaveBeenCalledTimes(2);
  });

  it("leaves the source in place when no Mermaid is available", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    const binding = initKpressDiagrams();
    await binding.ready;
    expect(figures()[0].dataset.kpressDiagramStatus).toBe("source");
    expect(document.querySelector(".kpress-diagram-error")).toBeNull();
  });

  it("shows Mermaid's message above the source when a diagram fails", async () => {
    document.body.innerHTML = FIGURE("graph TD\nA--");
    const mermaid = fakeMermaid(async (id) => {
      const scratch = document.createElement("div");
      scratch.id = `d${id}`;
      document.body.append(scratch);
      throw new Error("Parse error on line 2: <b>A--</b>\n");
    });

    await initKpressDiagrams(document, { mermaid, yieldBetween: noYield }).ready;

    const [figure] = figures();
    const note = figure.querySelector(":scope > .kpress-diagram-error");
    expect(figure.dataset.kpressDiagramStatus).toBe("error");
    expect(note?.getAttribute("role")).toBe("note");
    expect(note?.querySelector("strong")?.textContent).toBe("Could not draw this diagram.");
    expect(note?.querySelector(".kpress-diagram-error-detail")?.textContent).toBe(
      "Parse error on line 2: <b>A--</b>",
    );
    // Text, never markup: the message can quote the source.
    expect(note?.querySelector("b")).toBeNull();
    expect(note?.nextElementSibling?.classList.contains("kpress-diagram-source")).toBe(true);
    expect(figure.querySelector(".kpress-diagram-source").hidden).toBe(false);
    expect(document.querySelector('[id^="dkpress-mermaid-"]')).toBeNull();
    expect(diagramErrorMessage({ message: "  " })).toBe("Mermaid could not draw this diagram.");
  });

  it("refuses a source longer than Mermaid's limit without calling it", async () => {
    document.body.innerHTML = FIGURE("x".repeat(MAX_DIAGRAM_TEXT + 1));
    const mermaid = fakeMermaid();
    await initKpressDiagrams(document, { mermaid, yieldBetween: noYield }).ready;
    expect(mermaid.render).not.toHaveBeenCalled();
    expect(document.querySelector(".kpress-diagram-error-detail")?.textContent).toBe(
      "This diagram's source is 50,001 characters; Mermaid draws at most 50,000.",
    );
  });

  it("says so on every figure when Mermaid cannot load", async () => {
    document.body.innerHTML = FIGURE("graph TD") + FIGURE("graph LR");
    await initKpressDiagrams(document, {
      mermaid: async () => {
        throw new Error("network down");
      },
    }).ready;
    const details = [...document.querySelectorAll(".kpress-diagram-error-detail")];
    expect(details.map((detail) => detail.textContent)).toEqual([
      "Mermaid could not load: network down",
      "Mermaid could not load: network down",
    ]);
  });

  it("redraws in the new theme when the theme changes, and stops after dispose", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    const mermaid = fakeMermaid();
    let theme = "light";
    /** @type {(() => void) | null} */
    let listener = null;
    const unsubscribe = vi.fn();
    const binding = initKpressDiagrams(document, {
      mermaid,
      theme: () => theme,
      subscribeTheme: (fn) => {
        listener = fn;
        return unsubscribe;
      },
      yieldBetween: noYield,
    });
    await binding.ready;

    theme = "dark";
    listener?.();
    expect(figures()[0].dataset.kpressDiagramStatus).toBe("source");
    await binding.ready;

    expect(mermaid.initialize).toHaveBeenLastCalledWith(expect.objectContaining({ theme: "dark" }));
    expect(document.querySelectorAll(".kpress-diagram-rendered")).toHaveLength(1);

    binding.dispose();
    expect(unsubscribe).toHaveBeenCalledTimes(1);
    binding.rerender();
    expect(figures()[0].dataset.kpressDiagramStatus).toBe("rendered");
  });

  it("follows the runtime's theme:change by default", async () => {
    document.documentElement.dataset.kpressResolvedTheme = "light";
    document.body.innerHTML = FIGURE("graph TD");
    const mermaid = fakeMermaid();
    const binding = initKpressDiagrams(document, { mermaid, yieldBetween: noYield });
    await binding.ready;

    document.documentElement.dataset.kpressResolvedTheme = "dark";
    emit("theme:change", { mode: "dark", resolved: "dark" });
    await binding.ready;
    expect(mermaid.initialize).toHaveBeenLastCalledWith(expect.objectContaining({ theme: "dark" }));
    binding.dispose();
  });

  it("keeps a drawing that matches and redraws one from another theme", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    const mermaid = fakeMermaid();
    await initKpressDiagrams(document, { mermaid, theme: () => "light" }).ready;
    await initKpressDiagrams(document, { mermaid, theme: () => "light" }).ready;
    expect(mermaid.render).toHaveBeenCalledTimes(1);

    await initKpressDiagrams(document, { mermaid, theme: () => "dark" }).ready;
    expect(mermaid.render).toHaveBeenCalledTimes(2);
    expect(document.querySelectorAll(".kpress-diagram-rendered")).toHaveLength(1);
  });

  it("discards a render that finishes after dispose", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    /** @type {(value: { svg: string }) => void} */
    let finish = () => {};
    const mermaid = fakeMermaid(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const binding = initKpressDiagrams(document, { mermaid, yieldBetween: noYield });
    await vi.waitFor(() => expect(mermaid.render).toHaveBeenCalled());
    expect(figures()[0].dataset.kpressDiagramStatus).toBe("rendering");

    binding.dispose();
    finish({ svg: "<svg></svg>" });
    await binding.ready;

    expect(figures()[0].dataset.kpressDiagramStatus).toBe("source");
    expect(document.querySelector(".kpress-diagram-rendered")).toBeNull();
  });

  it("places an image measured in a host with Mermaid's font", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    /** @type {Element | undefined} */
    let measuredIn;
    const mermaid = fakeMermaid(async (id, _text, container) => {
      measuredIn = container;
      expect(container?.isConnected).toBe(true);
      return { svg: `<svg id="${id}" viewBox="0 0 120.5 40"><text>A<br>B</text></svg>` };
    });

    await initKpressDiagrams(document, {
      mermaid,
      placement: "image",
      yieldBetween: noYield,
    }).ready;

    expect(measuredIn?.getAttribute("style")).toContain(
      'font-family:"trebuchet ms", verdana, arial, sans-serif;font-size:16px;',
    );
    expect(measuredIn?.isConnected).toBe(false);
    const image = document.querySelector(".kpress-diagram-rendered > img.kpress-diagram-image");
    expect(image?.getAttribute("alt")).toBe("Mermaid diagram");
    const src = image?.getAttribute("src") ?? "";
    expect(src.startsWith("data:image/svg+xml;charset=utf-8,")).toBe(true);
    const xml = decodeURIComponent(src.slice(src.indexOf(",") + 1));
    expect(xml).toContain('width="120.5"');
    expect(xml).toContain('xmlns="http://www.w3.org/2000/svg"');
    expect(document.querySelector(".kpress-diagram-rendered svg")).toBeNull();
  });

  it("adopts a host's bare Mermaid block as a figure", async () => {
    document.body.innerHTML = '<pre lang="mermaid"><code>graph TD</code></pre>';
    const figure = mermaidFigureFor(document.querySelector("pre"));
    expect(figure.matches('figure.kpress-mermaid[data-kpress-diagram="mermaid"]')).toBe(true);
    expect(figure.querySelector(":scope > pre.kpress-diagram-source")).not.toBeNull();
    expect(mermaidFigureFor(figure)).toBe(figure);

    await initKpressDiagrams(document, { mermaid: fakeMermaid(), yieldBetween: noYield }).ready;
    expect(figure.dataset.kpressDiagramStatus).toBe("rendered");
  });
});

describe("diagram controls", () => {
  const icon = (name) => `<i data-glyph="${name}"></i>`;

  it("adds a toolbar whose source toggle follows the figure", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    const decorate = vi.fn();
    const binding = initKpressDiagrams(document, {
      mermaid: fakeMermaid(),
      controls: diagramControls({ icon, decorate }),
      yieldBetween: noYield,
    });
    await binding.ready;

    const [figure] = figures();
    const toolbar = figure.querySelector(":scope > .kpress-diagram-toolbar");
    expect(toolbar?.classList.contains("kpress-no-print")).toBe(true);
    const buttons = [...(toolbar?.querySelectorAll("button") ?? [])];
    expect(buttons.map((button) => button.getAttribute("aria-label"))).toEqual([
      "Copy diagram source",
      "Show source",
      "Expand diagram",
    ]);
    expect(buttons.map((button) => button.querySelector("i")?.dataset.glyph)).toEqual([
      "copy",
      "code",
      "maximize",
    ]);
    expect(decorate).toHaveBeenCalledWith(buttons[0], "copy");

    const toggle = /** @type {HTMLButtonElement} */ (buttons[1]);
    toggle.click();
    expect(figure.dataset.kpressDiagramShowSource).toBe("true");
    expect(figure.querySelector(".kpress-diagram-rendered").hidden).toBe(true);
    expect(figure.querySelector(".kpress-diagram-source").hidden).toBe(false);
    expect(toggle.getAttribute("aria-label")).toBe("Show diagram");
    expect(decorate).toHaveBeenLastCalledWith(toggle, "toggle-source");

    // The choice survives a redraw.
    binding.rerender();
    await binding.ready;
    expect(figure.querySelector(".kpress-diagram-rendered").hidden).toBe(true);
    toggle.click();
    expect(figure.querySelector(".kpress-diagram-rendered").hidden).toBe(false);
    expect(figure.querySelector(".kpress-diagram-source").hidden).toBe(true);

    binding.dispose();
    toggle.click();
    expect(figure.dataset.kpressDiagramShowSource).toBe("false");
  });

  it("copies the source, or hands the button to the host", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const writeText = vi.fn(async () => {});
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    document.body.innerHTML = FIGURE("graph TD\nA--&gt;B");
    await initKpressDiagrams(document, {
      mermaid: fakeMermaid(),
      controls: diagramControls({ icon }),
      yieldBetween: noYield,
    }).ready;
    const copy = /** @type {HTMLButtonElement} */ (document.querySelector(".kpress-diagram-copy"));
    copy.click();
    await vi.waitFor(() => expect(copy.dataset.kpressCopyState).toBe("copied"));
    expect(writeText).toHaveBeenCalledWith("graph TD\nA-->B");
    expect(copy.querySelector("i")?.dataset.glyph).toBe("check");
    vi.advanceTimersByTime(1200);
    expect(copy.dataset.kpressCopyState).toBe("idle");

    document.body.innerHTML = FIGURE("graph LR");
    const own = vi.fn((button, text) => {
      button.dataset.hostCopy = text;
    });
    await initKpressDiagrams(document, {
      mermaid: fakeMermaid(),
      controls: diagramControls({ icon, copy: own }),
      yieldBetween: noYield,
    }).ready;
    const owned = /** @type {HTMLButtonElement} */ (document.querySelector(".kpress-diagram-copy"));
    expect(own).toHaveBeenCalledWith(owned, "graph LR");
    expect(owned.dataset.hostCopy).toBe("graph LR");
    writeText.mockClear();
    owned.click();
    await Promise.resolve();
    expect(writeText).not.toHaveBeenCalled();
    expect(owned.dataset.kpressCopyState).toBe("idle");

    document.body.innerHTML = FIGURE("graph LR");
    initKpressDiagrams(document, { controls: diagramControls({ copy: null, expand: false }) });
    expect(
      [...document.querySelectorAll(".kpress-diagram-toolbar button")].map((b) => b.className),
    ).toEqual(["kpress-diagram-button kpress-diagram-toggle-source"]);
  });

  it("opens a zoom and pan dialog that closes with the binding", async () => {
    document.body.innerHTML = FIGURE("graph TD");
    const binding = initKpressDiagrams(document, {
      mermaid: fakeMermaid(),
      controls: diagramControls({ icon }),
      yieldBetween: noYield,
    });
    await binding.ready;
    const [figure] = figures();
    /** @type {HTMLButtonElement} */ (figure.querySelector(".kpress-diagram-expand")).click();

    const found = figure.querySelector(":scope > dialog.kpress-diagram-dialog");
    expect(found).not.toBeNull();
    const dialog = /** @type {HTMLDialogElement} */ (found);
    expect(dialog.hasAttribute("open")).toBe(true);
    const actions = [...(dialog.querySelectorAll("[data-kpress-diagram-action]") ?? [])].map(
      (button) => /** @type {HTMLElement} */ (button).dataset.kpressDiagramAction,
    );
    expect(actions).toEqual([
      "zoom-in",
      "zoom-out",
      "reset",
      "pan-up",
      "pan-down",
      "pan-left",
      "pan-right",
    ]);
    const stage = /** @type {HTMLElement} */ (dialog.querySelector(".kpress-diagram-stage"));
    const drawing = stage.querySelector("svg");
    expect(drawing?.style.width).toBe("120px");
    expect(drawing?.style.maxWidth).toBe("none");

    const start = stage.style.transform;
    /** @type {HTMLButtonElement} */ (
      dialog.querySelector('[data-kpress-diagram-action="pan-up"]')
    ).click();
    expect(stage.style.transform).not.toBe(start);
    dialog.dispatchEvent(new KeyboardEvent("keydown", { key: "0", bubbles: true }));
    expect(stage.style.transform).toBe(start);

    /** @type {HTMLButtonElement} */ (dialog.querySelector(".kpress-diagram-dialog-close")).click();
    expect(figure.querySelector("dialog")).toBeNull();

    /** @type {HTMLButtonElement} */ (figure.querySelector(".kpress-diagram-expand")).click();
    expect(figure.querySelector("dialog")).not.toBeNull();
    binding.dispose();
    expect(figure.querySelector("dialog")).toBeNull();
  });
});
