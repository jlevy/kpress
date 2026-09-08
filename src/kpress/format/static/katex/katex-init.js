// Native progressive enhancement. Hosts with their own math nodes use the
// shared katex-math-runtime.js directly and supply their own render loop.
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
    globalThis.kpressMathText.complete();
    return;
  }
  const nodes = document.querySelectorAll(".kpress-math-render");
  applyTextMetrics(nodes);
  const pending = [];
  for (const node of nodes) {
    const host = node.closest("[data-kpress-math]");
    if (!host || host.dataset.kpressMathRendered === "true") {
      continue;
    }
    pending.push(
      renderMathNode(node, () => {
        render(node, OPTIONS);
        host.dataset.kpressMathRendered = "true";
      }).catch(() => {
        // The semantic MathML remains readable if enhancement fails.
        delete host.dataset.kpressMathRendered;
      }),
    );
  }
  restore();
  return Promise.all(pending).then(() => globalThis.kpressMathText.complete());
}

function startMath() {
  const nodes = document.querySelectorAll(".kpress-math-render");
  const loads = mathFaceLoads(nodes);
  if (loads === null) {
    enhanceMath();
  } else {
    // Warm both profiles together. The render boundary reuses these requests
    // and their original deadline, then checks the individual expression.
    waitForLoads(loads).then(enhanceMath, enhanceMath);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", startMath, { once: true });
} else {
  startMath();
}
