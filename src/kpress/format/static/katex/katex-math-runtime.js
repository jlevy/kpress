// Shared by the native initializer and hosts that render their own mathematics.
// Load after katex.min.js and katex-text-metrics.js. This classic script exposes
// kpressMathText; it does not scan or render the document by itself.
const TEXT_FACE_OPT_OUT =
  '[data-kpress-math-text="katex"], [data-kpress-fonts="system"], [data-kpress-font-set="system"]';
const SANS_CONTEXT =
  '.kpress-figcaption, .kpress-footnotes, .kpress-table, .sans-text, .description, .key-claims, .summary, .concepts, .claim, .para-caption, .tab-button, .kpress-tab-button, details, [data-kpress-prose-font="sans"]';
const SERIF_SET = "prose";
const SANS_SET = "sans";
const KATEX_SET = "katex";
const SANS_FACE_ATTR = "kpressMathFace";
const SCALE_KEY = "scale";
const FACE_WAIT_MS = 3000;
const FACE_SAMPLE = "a1αΩ";
const KATEX_FAMILIES = ["KaTeX_Main", "KaTeX_Math"];
const COMPOSITE_FAMILIES = {
  [SERIF_SET]: "KPress Math Text",
  [SANS_SET]: "KPress Math Text Sans",
};
const COMPOSITE_FONTS = {
  [SERIF_SET]: [
    "400 1em 'KPress Math Text'",
    "italic 400 1em 'KPress Math Text'",
    "700 1em 'KPress Math Text'",
    "italic 700 1em 'KPress Math Text'",
  ],
  [SANS_SET]: [
    "400 1em 'KPress Math Text Sans'",
    "italic 400 1em 'KPress Math Text Sans'",
    "650 1em 'KPress Math Text Sans'",
    "italic 650 1em 'KPress Math Text Sans'",
  ],
};
let metricsApplied = false;
let installedSet = null;
const faceLoads = new WeakMap();
const descriptionLoads = new Map();
const loadEntries = new WeakMap();
const renderVersions = new WeakMap();
const hiddenNodes = new WeakMap();
const waitRecord = [];

function tablesFor(set) {
  const metrics = globalThis.kpressKatexTextMetrics;
  const tables = set === SERIF_SET ? metrics : metrics?.[set];
  return tables && typeof tables === "object" ? tables : null;
}

function installTables(set) {
  if (installedSet === set) {
    return true;
  }
  const tables = tablesFor(set);
  const katex = globalThis.katex;
  if (!tables || typeof katex?.__setFontMetrics !== "function") {
    return false;
  }
  for (const [face, table] of Object.entries(tables)) {
    if (face === SANS_SET || face === KATEX_SET || face === SCALE_KEY) {
      continue;
    }
    katex.__setFontMetrics(face, table);
  }
  installedSet = set;
  return true;
}

function applyTextMetrics(nodes) {
  if (metricsApplied || ![...nodes].some((node) => !node.closest(TEXT_FACE_OPT_OUT))) {
    return;
  }
  metricsApplied = true;
  if (!tablesFor(SANS_SET) || !installTables(SERIF_SET)) {
    installedSet = null;
    document.documentElement.dataset.kpressMathText = "katex";
    console.warn(
      "kpress: the math text face metrics are unavailable; KaTeX's own faces are restored",
    );
  }
}

function textMetricsSet(node, options = {}) {
  if (node.closest(TEXT_FACE_OPT_OUT)) {
    return KATEX_SET;
  }
  return node.closest(SANS_CONTEXT) || options.isSansContext?.(node) ? SANS_SET : SERIF_SET;
}

function compositeDeclared(set) {
  if (typeof document.fonts?.forEach !== "function") {
    return true;
  }
  const family = COMPOSITE_FAMILIES[set].toLowerCase();
  let declared = false;
  document.fonts.forEach((face) => {
    if (face.family.replace(/^["']|["']$/g, "").toLowerCase() === family) {
      declared = true;
    }
  });
  // Check declarations, not load status: a failed unused weight must not discard
  // the profile. The rendered glyph requests validate its required faces later.
  return declared;
}

// Initialization is independent of the native loop. A host can use this API on
// its first dynamically created formula, including a page with no native math.
function installTablesFor(node, options = {}) {
  applyTextMetrics([node]);
  let set = textMetricsSet(node, options);
  if (set !== KATEX_SET && !compositeDeclared(set)) {
    // FontFaceSet.check accepts a missing CSS family when fallback is available.
    // Select matching stock metrics and families before laying out that fallback.
    set = KATEX_SET;
  }
  if (node.dataset) {
    delete node.dataset[SANS_FACE_ATTR];
    if (set === KATEX_SET && tablesFor(KATEX_SET)) {
      node.dataset[SANS_FACE_ATTR] = KATEX_SET;
    }
  }
  if (!installedSet) {
    return null;
  }
  if (!installTables(set)) {
    throw new Error("kpress: the selected mathematics font metrics are unavailable");
  }
  if (set === SANS_SET && node.dataset) {
    node.dataset[SANS_FACE_ATTR] = SANS_SET;
  }
  return set;
}

function restore() {
  if (installedSet) {
    installTables(SERIF_SET);
  }
}

function faceKey(face) {
  return [face.family, face.style, face.weight, face.unicodeRange].join("|");
}

// Failed and empty requests settle independently, so a broken font does not
// release the formulas while another, successful font is still arriving.
function trackLoad(request, start, cache, key) {
  if (cache.has(key)) {
    return cache.get(key);
  }
  globalThis.kpressMathFaceWait = waitRecord;
  const entry = { request, outcome: "pending", faces: [] };
  waitRecord.push(entry);
  let matched;
  try {
    matched = start();
  } catch (error) {
    matched = Promise.reject(error);
  }
  const promise = Promise.resolve(matched).then(
    (faces) => {
      entry.faces = faces.map(faceKey);
      entry.outcome = faces.length ? "loaded" : "empty";
      return entry;
    },
    (error) => {
      entry.outcome = "error";
      entry.detail = String(error);
      return entry;
    },
  );
  loadEntries.set(promise, { entry, deadline: performance.now() + FACE_WAIT_MS });
  cache.set(key, promise);
  return promise;
}

function loadDescription(spec, text) {
  // A screen face and its print override share the description but are separate
  // faces. Do not reuse the screen's resolved promise after a media switch.
  const medium = globalThis.matchMedia?.("print").matches ? "print" : "screen";
  const key = `${medium}|${spec}|${text}`;
  return trackLoad(spec, () => document.fonts.load(spec, text), descriptionLoads, key);
}

function mathFaceLoads(nodes = document.querySelectorAll(".kpress-math-render"), options = {}) {
  const fonts = document.fonts;
  if (
    !nodes.length ||
    !fonts ||
    typeof fonts.load !== "function" ||
    typeof fonts.forEach !== "function"
  ) {
    return null;
  }
  const loads = [];
  fonts.forEach((face) => {
    if (
      (!options.allEmbeddedFonts && !KATEX_FAMILIES.includes(face.family)) ||
      typeof face.load !== "function"
    ) {
      return;
    }
    loads.push(
      trackLoad(faceKey(face), () => face.load().then((loaded) => [loaded]), faceLoads, face),
    );
  });
  const wanted = new Set([...nodes].map((node) => textMetricsSet(node, options)));
  for (const set of [SERIF_SET, SANS_SET]) {
    if (!wanted.has(set)) {
      continue;
    }
    for (const spec of COMPOSITE_FONTS[set]) {
      loads.push(loadDescription(spec, FACE_SAMPLE));
    }
  }
  return loads;
}

function waitForLoads(loads, timeout = FACE_WAIT_MS) {
  if (loads === null) {
    return Promise.resolve({ status: "unavailable" });
  }
  if (!loads.length) {
    return Promise.resolve({ status: "ready" });
  }
  // Reusing a pending preparation must not start another three-second wait.
  // New glyph requests still receive their own allowance at a later render.
  for (const load of loads) {
    const state = loadEntries.get(load);
    if (state?.entry.outcome === "pending") {
      timeout = Math.min(timeout, Math.max(0, state.deadline - performance.now()));
    }
  }
  if (timeout <= 0) {
    return Promise.resolve({ status: "timeout" });
  }
  let timer;
  const deadline = new Promise((resolve) => {
    timer = setTimeout(() => resolve({ status: "timeout" }), timeout);
  });
  return Promise.race([
    Promise.all(loads).then((entries) => ({
      status: entries.some((entry) => entry.outcome === "error")
        ? "error"
        : entries.some((entry) => entry.outcome === "empty")
          ? "empty"
          : "ready",
    })),
    deadline,
  ]).finally(() => clearTimeout(timer));
}

function ready(nodes = document.querySelectorAll(".kpress-math-render"), options = {}) {
  const list = [...nodes];
  applyTextMetrics(list);
  return waitForLoads(mathFaceLoads(list, options));
}

function hideNode(node) {
  if (!hiddenNodes.has(node)) {
    hiddenNodes.set(node, {
      visibility: node.style.getPropertyValue("visibility"),
      priority: node.style.getPropertyPriority("visibility"),
    });
  }
  node.style.setProperty("visibility", "hidden", "important");
  node.dataset.kpressMathPending = "true";
}

function showNode(node) {
  const previous = hiddenNodes.get(node);
  if (previous) {
    if (previous.visibility) {
      node.style.setProperty("visibility", previous.visibility, previous.priority);
    } else {
      node.style.removeProperty("visibility");
    }
    hiddenNodes.delete(node);
  }
  delete node.dataset.kpressMathPending;
}

// Render under the real cascade while hidden, then ask CSS font matching for
// exactly the glyphs in the rendered HTML. This catches AMS, large operators,
// delimiters and other construct fonts without downloading every KaTeX family.
// The semantic MathML subtree is excluded: it is not the painted result.
function renderedFaceLoads(node) {
  const fonts = document.fonts;
  if (!fonts || typeof fonts.load !== "function") {
    return null;
  }
  const requests = new Map();
  for (const html of node.querySelectorAll(".katex-html")) {
    const walker = document.createTreeWalker(html, NodeFilter.SHOW_TEXT);
    for (let text = walker.nextNode(); text; text = walker.nextNode()) {
      if (!text.textContent || !text.parentElement) {
        continue;
      }
      const style = getComputedStyle(text.parentElement);
      if (!style.fontFamily) {
        continue;
      }
      const spec = `${style.fontStyle || "normal"} ${style.fontWeight || "400"} ${style.fontSize || "16px"} ${style.fontFamily}`;
      if (!requests.has(spec)) {
        requests.set(spec, new Set());
      }
      for (const character of text.textContent) {
        requests.get(spec).add(character);
      }
    }
  }
  const loads = [];
  for (const [spec, characters] of requests) {
    const text = [...characters].join("");
    if (typeof fonts.check === "function" && fonts.check(spec, text)) {
      continue;
    }
    loads.push(loadDescription(spec, text));
  }
  return loads;
}

// The version is assigned before any await. A slow earlier slider or resize
// callback can therefore never overwrite a newer request for the same node.
function renderMathNode(node, renderer, options = {}) {
  const version = (renderVersions.get(node) ?? 0) + 1;
  renderVersions.set(node, version);
  const expires = performance.now() + FACE_WAIT_MS;
  hideNode(node);
  const run = () => {
    if (renderVersions.get(node) !== version) {
      return Promise.resolve({ status: "superseded" });
    }
    try {
      installTablesFor(node, options);
      renderer();
    } catch (error) {
      showNode(node);
      return Promise.reject(error);
    } finally {
      restore();
    }
    let loads;
    try {
      loads = renderedFaceLoads(node);
    } catch (error) {
      showNode(node);
      return Promise.reject(error);
    }
    if (loads === null || !loads.length) {
      showNode(node);
      return Promise.resolve({ status: loads === null ? "unavailable" : "ready" });
    }
    return waitForLoads(loads, Math.max(0, expires - performance.now())).then((result) => {
      if (renderVersions.get(node) !== version) {
        return { status: "superseded" };
      }
      showNode(node);
      if (result.status !== "ready") {
        // Keep native MathML (or the host's text fallback) instead of showing
        // fallback glyphs positioned with the unavailable face's metrics.
        throw new Error(`kpress: required mathematics fonts are unavailable (${result.status})`);
      }
      return result;
    });
  };
  // Preserve synchronous enhancement on browsers without font loading support.
  // With fonts, readiness belongs to every render, including observer callbacks.
  if (!document.fonts || typeof document.fonts.load !== "function") {
    return run();
  }
  try {
    return ready([node], options).then(run);
  } catch (error) {
    showNode(node);
    return Promise.reject(error);
  }
}

function renderMath(tex, node, katexOptions = {}, options = {}) {
  return renderMathNode(node, () => globalThis.katex.render(tex, node, katexOptions), options);
}

function complete() {
  clearTimeout(globalThis.kpressMathPendingTimer);
  delete document.documentElement.dataset.kpressMathPending;
}

globalThis.kpressMathText = {
  ready,
  render: renderMath,
  installTablesFor,
  restore,
  complete,
};
