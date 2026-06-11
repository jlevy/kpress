/**
 * KPress client runtime: the host-facing JS surface and the seam KPress's own
 * built-ins use (the dogfood rule — see kpress-design.md "Extension and
 * Injection Model"). It assembles the `kpress` global from small parts:
 *
 * - `model()` — the parsed #kpress-page-model page model (layer A).
 * - `on`/`off`/`emit` — events (`kpress:ready`, `widget:change`, ...).
 * - `storage` — persistence with a pluggable adapter (localStorage default;
 *   an embedding host can swap in cookies with one call).
 * - `widgets` — client-rendered chrome: register/configure/mount over the
 *   server-emitted `[data-kpress-widget]` mounts (no-JS rule).
 * - `behaviors` — bindings over server-rendered markup: register/override/
 *   configure/rebind.
 *
 * Lifecycle: modules register at import (no DOM work); the runtime applies all
 * registrations once the document is ready and emits `kpress:ready`. Host
 * scripts loaded earlier (head_extra_html) therefore register/override before
 * built-ins are applied; anything registered after ready is applied
 * immediately. Other KPress modules attach their own namespaces (e.g.
 * `kpress.theme`, `kpress.menu`) — assembled, not monolithic.
 */

/** @typedef {{ get(key: string): string | null, set(key: string, value: string): void }} KpressStorageAdapter */
/** @typedef {(detail?: unknown) => void} KpressListener */
/** @typedef {Record<string, unknown>} KpressConfig */
/** @typedef {{ mount(el: HTMLElement, config: KpressConfig, model: KpressConfig): void }} KpressWidget */
/** @typedef {{ selector?: string, bind(root: Document | HTMLElement, config: KpressConfig): void }} KpressBehavior */

/** @type {KpressConfig | null} */
let cachedModel = null;

/**
 * The page model published by the server (#kpress-page-model), parsed once.
 * Fragments have no block; embeds get the same data in the render payload.
 *
 * @returns {KpressConfig}
 */
export function getModel() {
  if (cachedModel === null) {
    /** @type {KpressConfig} */
    let parsed = {};
    const block = document.getElementById("kpress-page-model");
    if (block?.textContent) {
      try {
        parsed = JSON.parse(block.textContent) ?? {};
      } catch {
        parsed = {};
      }
    }
    if (typeof parsed.widgets !== "object" || parsed.widgets === null) {
      parsed.widgets = {};
    }
    cachedModel = parsed;
  }
  return cachedModel;
}

/** @type {Map<string, Set<KpressListener>>} */
const listeners = new Map();

/**
 * @param {string} type
 * @param {KpressListener} listener
 */
export function on(type, listener) {
  let set = listeners.get(type);
  if (!set) {
    set = new Set();
    listeners.set(type, set);
  }
  set.add(listener);
}

/**
 * @param {string} type
 * @param {KpressListener} listener
 */
export function off(type, listener) {
  listeners.get(type)?.delete(listener);
}

/**
 * @param {string} type
 * @param {unknown} [detail]
 */
export function emit(type, detail) {
  for (const listener of [...(listeners.get(type) ?? [])]) {
    listener(detail);
  }
}

/** @type {KpressStorageAdapter} */
const localStorageAdapter = {
  get(key) {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {
      // Storage may be unavailable (private mode, sandboxed embed).
    }
  },
};

/** @type {KpressStorageAdapter} */
let activeAdapter = localStorageAdapter;

export const storage = {
  /** @param {string} key */
  get(key) {
    return activeAdapter.get(key);
  },
  /**
   * @param {string} key
   * @param {string} value
   */
  set(key, value) {
    activeAdapter.set(key, value);
  },
  /**
   * Swap the persistence adapter (e.g. cookies for cross-port sharing).
   * Every primitive and widget persists through it from then on.
   *
   * @param {KpressStorageAdapter} adapter
   */
  use(adapter) {
    activeAdapter = adapter;
  },
};

let applied = false;

/** @type {Map<string, KpressWidget>} */
const widgetRegistry = new Map();
/** @type {Map<string, KpressConfig>} */
const widgetConfigs = new Map();

/**
 * Widget config: the page model's (opaque, verbatim) config under any
 * `configure()` values — the widget's own JS owns the schema.
 *
 * @param {string} id
 * @returns {KpressConfig}
 */
function resolveWidgetConfig(id) {
  const widgetsModel = /** @type {Record<string, unknown>} */ (getModel().widgets);
  const fromModel = widgetsModel?.[id];
  const base =
    fromModel && typeof fromModel === "object" ? /** @type {KpressConfig} */ (fromModel) : {};
  return { ...base, ...(widgetConfigs.get(id) ?? {}) };
}

/** @param {string} id */
function mountAllFor(id) {
  for (const el of document.querySelectorAll(`[data-kpress-widget="${id}"]`)) {
    if (el.getAttribute("data-kpress-widget-bound") === "true") {
      continue;
    }
    el.setAttribute("data-kpress-widget-bound", "true");
    widgets.mount(id, /** @type {HTMLElement} */ (el));
  }
}

export const widgets = {
  /**
   * @param {string} id
   * @param {KpressWidget} widget
   */
  register(id, widget) {
    widgetRegistry.set(id, widget);
    if (applied) {
      mountAllFor(id);
    }
  },
  /**
   * Merge host config over the page model's for this widget id.
   *
   * @param {string} id
   * @param {KpressConfig} config
   */
  configure(id, config) {
    widgetConfigs.set(id, { ...(widgetConfigs.get(id) ?? {}), ...config });
  },
  /**
   * Mount a registered widget into an element (embeds mount anywhere).
   *
   * @param {string} id
   * @param {HTMLElement} el
   * @param {KpressConfig} [config]
   */
  mount(id, el, config) {
    const widget = widgetRegistry.get(id);
    if (!widget || !el) {
      return;
    }
    widget.mount(el, config ?? resolveWidgetConfig(id), getModel());
  },
};

/** @type {Map<string, KpressBehavior>} */
const behaviorRegistry = new Map();
/** @type {Map<string, KpressConfig>} */
const behaviorConfigs = new Map();

/** @param {string} id */
function runBehavior(id) {
  const behavior = behaviorRegistry.get(id);
  if (!behavior?.bind) {
    return;
  }
  behavior.bind(document, behaviorConfigs.get(id) ?? {});
}

export const behaviors = {
  /**
   * @param {string} id
   * @param {KpressBehavior} behavior
   */
  register(id, behavior) {
    behaviorRegistry.set(id, behavior);
    if (applied) {
      runBehavior(id);
    }
  },
  /**
   * Replace a behavior's binding (a function) or merge registration fields
   * (an object) — the same markup, different handling.
   *
   * @param {string} id
   * @param {KpressBehavior["bind"] | Partial<KpressBehavior>} binding
   */
  override(id, binding) {
    const current = behaviorRegistry.get(id);
    const next =
      typeof binding === "function"
        ? { ...(current ?? {}), bind: binding }
        : { ...(current ?? {}), ...binding };
    behaviorRegistry.set(id, /** @type {KpressBehavior} */ (next));
    if (applied) {
      runBehavior(id);
    }
  },
  /**
   * Merge config passed to this behavior's bind. JS config may carry
   * callbacks/policies — the channel YAML cannot express.
   *
   * @param {string} id
   * @param {KpressConfig} config
   */
  configure(id, config) {
    behaviorConfigs.set(id, { ...(behaviorConfigs.get(id) ?? {}), ...config });
  },
  /**
   * Re-run one behavior's binding (after an override post-ready, or after
   * injecting markup it should pick up).
   *
   * @param {string} id
   */
  rebind(id) {
    runBehavior(id);
  },
};

/** @type {Record<string, unknown>} */
const kpressGlobal = /** @type {Record<string, unknown>} */ (
  /** @type {Record<string, unknown>} */ (globalThis).kpress ?? {}
);
/** @type {Record<string, unknown>} */ (globalThis).kpress = kpressGlobal;
Object.assign(kpressGlobal, {
  model: getModel,
  on,
  off,
  emit,
  storage,
  widgets,
  behaviors,
  isReady: false,
});

function applyAll() {
  if (applied) {
    return;
  }
  applied = true;
  for (const id of widgetRegistry.keys()) {
    mountAllFor(id);
  }
  for (const id of behaviorRegistry.keys()) {
    runBehavior(id);
  }
  kpressGlobal.isReady = true;
  emit("kpress:ready", {});
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", applyAll, { once: true });
} else {
  applyAll();
}
