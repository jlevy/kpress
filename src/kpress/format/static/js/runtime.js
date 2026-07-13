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
 *
 * Fault isolation: one registration (widget mount, behavior bind, event
 * listener, storage adapter) failing must not take down the rest of the page
 * or suppress `kpress:ready` — failures are reported via `console.error` and
 * the pass continues.
 */

/** @typedef {{ get(key: string): string | null, set(key: string, value: string): void }} KpressStorageAdapter */
/** @typedef {(detail?: unknown) => void} KpressListener */
/** @typedef {Record<string, unknown>} KpressConfig */
/** @typedef {{ mount(el: HTMLElement, config: KpressConfig, model: KpressConfig): (() => void) | void }} KpressWidget */
/**
 * A behavior binds handling over server-rendered markup. `bind` MAY return a
 * disposer that tears the binding down (listeners, observers); the runtime
 * stores it per behavior id and calls it before re-binding the id
 * (`override`, `rebind`, or a re-`register`), so replacement is real — no
 * built-in wiring lingers behind a host override.
 *
 * @typedef {{ bind(root: Document | HTMLElement, config: KpressConfig): (() => void) | void }} KpressBehavior
 */

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
    // Match the <script> element specifically: content-authored HTML can carry an
    // id (e.g. <div id="kpress-page-model">) under the sanitizing trust modes, and
    // getElementById would return that clobbering element if it precedes ours. A
    // <script> tag from content is always stripped by the sanitizer, so this selector
    // can only match the server-emitted page model.
    const block = document.querySelector("script#kpress-page-model");
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
    try {
      listener(detail);
    } catch (error) {
      console.error(`kpress: "${type}" listener failed`, error);
    }
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
  /**
   * A throwing custom adapter degrades to "nothing persisted" (null) rather
   * than breaking the caller (theme engine, widgets).
   *
   * @param {string} key
   */
  get(key) {
    try {
      return activeAdapter.get(key);
    } catch (error) {
      console.error("kpress: storage adapter get failed", error);
      return null;
    }
  },
  /**
   * A throwing custom adapter degrades to a no-op set.
   *
   * @param {string} key
   * @param {string} value
   */
  set(key, value) {
    try {
      activeAdapter.set(key, value);
    } catch (error) {
      console.error("kpress: storage adapter set failed", error);
    }
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
/** Mounted elements and their explicit replacement config (null means resolved config). */
/** @type {Map<string, Map<HTMLElement, KpressConfig | null>>} */
const widgetMounts = new Map();
/** @type {Map<HTMLElement, () => void>} */
const widgetDisposers = new Map();

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
    widgets.mount(id, /** @type {HTMLElement} */ (el));
  }
}

/**
 * Run and forget one widget mount's disposer.
 *
 * @param {string} id
 * @param {HTMLElement} el
 */
function disposeWidgetMount(id, el) {
  const dispose = widgetDisposers.get(el);
  widgetDisposers.delete(el);
  if (dispose) {
    try {
      dispose();
    } catch (error) {
      console.error(`kpress: widget "${id}" disposer failed`, error);
    }
  }
}

/**
 * @param {string} id
 * @param {boolean} preserveActive
 */
function remountAllFor(id, preserveActive) {
  const alreadyMounted = [...(widgetMounts.get(id) ?? [])];
  mountAllFor(id);
  for (const [el, config] of alreadyMounted) {
    if (!el.isConnected) {
      disposeWidgetMount(id, el);
      const mounts = widgetMounts.get(id);
      mounts?.delete(el);
      if (mounts?.size === 0) {
        widgetMounts.delete(id);
      }
      el.removeAttribute("data-kpress-widget-bound");
      continue;
    }
    if (preserveActive && (el === document.activeElement || el.contains(document.activeElement))) {
      continue;
    }
    widgets.mount(id, el, config ?? undefined);
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
      remountAllFor(id, false);
    }
  },
  /**
   * Merge host config over the page model's for this widget id. Unknown ids
   * (typos) warn and store nothing.
   *
   * @param {string} id
   * @param {KpressConfig} config
   */
  configure(id, config) {
    if (!widgetRegistry.has(id)) {
      console.warn(
        `kpress: widgets.configure("${id}") ignored — no widget registered with that id`,
      );
      return;
    }
    widgetConfigs.set(id, { ...(widgetConfigs.get(id) ?? {}), ...config });
    if (applied) {
      remountAllFor(id, false);
    }
  },
  /**
   * Mount a registered widget into an element (embeds mount anywhere). The
   * element is marked bound so the ready pass never mounts a server mount a
   * second time after an explicit pre-ready mount. A throwing widget is
   * isolated (console.error) so one bad mount cannot abort the ready pass.
   *
   * @param {string} id
   * @param {HTMLElement} el
   * @param {KpressConfig} [config]
   */
  mount(id, el, config) {
    const widget = widgetRegistry.get(id);
    if (!widget) {
      console.warn(`kpress: widgets.mount("${id}") ignored — no widget registered with that id`);
      return;
    }
    if (!el) {
      return;
    }
    disposeWidgetMount(id, el);
    el.setAttribute("data-kpress-widget-bound", "true");
    let mounts = widgetMounts.get(id);
    if (!mounts) {
      mounts = new Map();
      widgetMounts.set(id, mounts);
    }
    mounts.set(el, config ?? null);
    try {
      const dispose = widget.mount(el, config ?? resolveWidgetConfig(id), getModel());
      if (typeof dispose === "function") {
        widgetDisposers.set(el, dispose);
      }
    } catch (error) {
      console.error(`kpress: widget "${id}" mount failed`, error);
    }
  },
};

/** @type {Map<string, KpressBehavior>} */
const behaviorRegistry = new Map();
/** @type {Map<string, KpressConfig>} */
const behaviorConfigs = new Map();
/** Disposers returned by behavior binds, keyed by behavior id. @type {Map<string, () => void>} */
const behaviorDisposers = new Map();

/**
 * Run a behavior id's stored disposer (if any). Disposal failures are
 * isolated: re-binding proceeds regardless.
 *
 * @param {string} id
 */
function disposeBehavior(id) {
  const dispose = behaviorDisposers.get(id);
  if (!dispose) {
    return;
  }
  behaviorDisposers.delete(id);
  try {
    dispose();
  } catch (error) {
    console.error(`kpress: behavior "${id}" disposer failed`, error);
  }
}

/**
 * Dispose the id's previous binding, then bind. A throwing bind is isolated
 * (console.error) so one bad behavior cannot leave later behaviors unbound or
 * suppress `kpress:ready`.
 *
 * @param {string} id
 */
function runBehavior(id) {
  const behavior = behaviorRegistry.get(id);
  if (!behavior?.bind) {
    return;
  }
  disposeBehavior(id);
  try {
    const dispose = behavior.bind(document, behaviorConfigs.get(id) ?? {});
    if (typeof dispose === "function") {
      behaviorDisposers.set(id, dispose);
    }
  } catch (error) {
    console.error(`kpress: behavior "${id}" bind failed`, error);
  }
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
   * (an object) — the same markup, different handling. Replacement is real:
   * the previous binding's disposer runs before the override binds. Unknown
   * ids warn and no-op — `register` is the path that creates behaviors.
   *
   * @param {string} id
   * @param {KpressBehavior["bind"] | Partial<KpressBehavior>} binding
   */
  override(id, binding) {
    const current = behaviorRegistry.get(id);
    if (!current) {
      console.warn(
        `kpress: behaviors.override("${id}") ignored — no behavior registered with that id ` +
          `(behaviors.register is the path that creates new behaviors)`,
      );
      return;
    }
    const next =
      typeof binding === "function" ? { ...current, bind: binding } : { ...current, ...binding };
    behaviorRegistry.set(id, /** @type {KpressBehavior} */ (next));
    if (applied) {
      runBehavior(id);
    }
  },
  /**
   * Merge config passed to this behavior's bind. JS config may carry
   * callbacks/policies — the channel YAML cannot express. Unknown ids
   * (typos) warn and store nothing.
   *
   * @param {string} id
   * @param {KpressConfig} config
   */
  configure(id, config) {
    if (!behaviorRegistry.has(id)) {
      console.warn(
        `kpress: behaviors.configure("${id}") ignored — no behavior registered with that id`,
      );
      return;
    }
    behaviorConfigs.set(id, { ...(behaviorConfigs.get(id) ?? {}), ...config });
    if (applied) {
      runBehavior(id);
    }
  },
  /**
   * Re-run one behavior's binding (after an override post-ready, or after
   * injecting markup it should pick up). The previous binding's disposer runs
   * first. Unknown ids warn and no-op.
   *
   * @param {string} id
   */
  rebind(id) {
    if (!behaviorRegistry.has(id)) {
      console.warn(
        `kpress: behaviors.rebind("${id}") ignored — no behavior registered with that id`,
      );
      return;
    }
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

let presentationReapplyActive = false;

function reapplyPresentationRegistrations() {
  if (kpressGlobal.isReady !== true || presentationReapplyActive) {
    return;
  }
  presentationReapplyActive = true;
  try {
    for (const id of widgetRegistry.keys()) {
      remountAllFor(id, true);
    }
    for (const id of behaviorRegistry.keys()) {
      // Theme emits theme:change from its own bind; rebinding it here would recurse.
      if (id !== "theme") {
        runBehavior(id);
      }
    }
  } finally {
    presentationReapplyActive = false;
  }
}

on("theme:change", reapplyPresentationRegistrations);
on("palette:change", reapplyPresentationRegistrations);

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
