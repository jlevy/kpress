let generatedMermaidCounter = 0;

/**
 * @typedef {{
 *   initialize?: (config: Record<string, unknown>) => void;
 *   render: (id: string, source: string) => Promise<string | { svg?: string }> | string | { svg?: string };
 * }} MermaidApi
 */

/**
 * @param {unknown} candidate
 * @returns {candidate is MermaidApi}
 */
function isMermaidApi(candidate) {
  return (
    typeof candidate === "object" &&
    candidate !== null &&
    "render" in candidate &&
    typeof candidate.render === "function"
  );
}

/**
 * @returns {MermaidApi | null}
 */
function hostMermaid() {
  const candidate = /** @type {{ mermaid?: unknown }} */ (globalThis).mermaid;
  return isMermaidApi(candidate) ? candidate : null;
}

/**
 * @param {string | { svg?: string }} result
 * @returns {string}
 */
function renderedSvg(result) {
  return typeof result === "string" ? result : result.svg || "";
}

/**
 * @param {HTMLElement} figure
 * @returns {string}
 */
function mermaidId(figure) {
  if (!figure.id) {
    generatedMermaidCounter += 1;
    figure.id = `kpress-mermaid-${generatedMermaidCounter}`;
  }
  return `${figure.id}-svg`;
}

/**
 * @param {HTMLElement} figure
 * @param {MermaidApi} mermaid
 */
async function renderMermaidFigure(figure, mermaid) {
  if (["rendered", "rendering"].includes(figure.dataset.kpressDiagramStatus || "")) {
    return;
  }
  const source = figure.querySelector(".kpress-diagram-source");
  const code = source?.querySelector("code") ?? source;
  const text = code?.textContent?.trim() || "";
  if (!text) {
    return;
  }
  figure.dataset.kpressDiagramStatus = "rendering";

  try {
    const svg = renderedSvg(await mermaid.render(mermaidId(figure), text));
    if (!svg) {
      throw new Error("Mermaid renderer did not return SVG.");
    }
    const rendered = document.createElement("div");
    rendered.className = "kpress-diagram-rendered";
    rendered.innerHTML = svg;
    figure.insertBefore(rendered, source ?? null);
    if (source instanceof HTMLElement) {
      source.hidden = true;
    }
    figure.dataset.kpressDiagramStatus = "rendered";
  } catch {
    figure.dataset.kpressDiagramStatus = "error";
    if (source instanceof HTMLElement) {
      source.hidden = false;
    }
  }
}

export async function initKpressDiagrams(root = document) {
  const mermaid = hostMermaid();
  if (!mermaid) {
    return;
  }
  mermaid.initialize?.({ startOnLoad: false, securityLevel: "strict" });
  for (const figure of root.querySelectorAll('[data-kpress-diagram="mermaid"]')) {
    if (!(figure instanceof HTMLElement)) {
      continue;
    }
    await renderMermaidFigure(figure, mermaid);
  }
}

globalThis.setTimeout(() => {
  void initKpressDiagrams();
}, 0);
