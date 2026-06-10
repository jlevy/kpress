// KaTeX progressive enhancement. Vendored KaTeX (katex.min.js) and its
// auto-render extension (auto-render.min.js) load before this script. The
// server emits each expression as a TeX source node (.kpress-math-render)
// plus a semantic MathML node (.kpress-math-semantic). KaTeX renders the TeX
// in place; the MathML stays in the accessibility tree as the no-JS fallback.
//
// This loads as a classic deferred <script> (after the UMD KaTeX globals), so it
// is a self-invoking IIFE-style script -- no ESM `export` (that would throw
// "Unexpected token 'export'" in a classic script and skip math enhancement).

const OPTIONS = {
  delimiters: [
    { left: "\\[", right: "\\]", display: true },
    { left: "\\(", right: "\\)", display: false },
  ],
  throwOnError: false,
  ignoredClasses: ["kpress-math-semantic"],
};

function enhanceMath() {
  const render = globalThis.renderMathInElement;
  if (typeof render !== "function") {
    return;
  }
  const nodes = document.querySelectorAll(".kpress-math-render");
  for (const node of nodes) {
    const host = node.closest("[data-kpress-math]");
    if (!host || host.dataset.kpressMathRendered === "true") {
      continue;
    }
    try {
      render(node, OPTIONS);
      host.dataset.kpressMathRendered = "true";
    } catch {
      // Leave the semantic MathML fallback in place on failure.
    }
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", enhanceMath, { once: true });
} else {
  enhanceMath();
}
