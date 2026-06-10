/**
 * Host embedding protocol for KPress documents rendered inside another shell.
 *
 * KPress stays host-neutral: it emits postMessage events, while the embedding
 * parent frame decides how resize, expand, and close requests affect shell chrome.
 */

const MESSAGE_SOURCE = "kpress";
const MESSAGE_VERSION = 1;
const DEFAULT_TARGET_ORIGIN = "*";

/**
 * @typedef {"kpress:ready" | "kpress:resize" | "kpress:expand" | "kpress:close"} KpressHostMessageType
 * @typedef {{
 *   source: "kpress";
 *   version: 1;
 *   type: KpressHostMessageType;
 *   documentId: string;
 *   height: number;
 *   width: number;
 *   expanded?: boolean;
 *   reason?: string;
 * }} KpressHostMessage
 * @typedef {{ postMessage(message: KpressHostMessage, targetOrigin: string): void }} KpressHostTarget
 * @typedef {{
 *   embedded?: boolean;
 *   targetWindow?: KpressHostTarget;
 *   targetOrigin?: string;
 *   documentId?: string;
 *   escapeClose?: boolean;
 * }} KpressHostOptions
 * @typedef {{ postResize(): void; destroy(): void }} KpressHostController
 */

/**
 * @param {Document | Element} root
 * @returns {Element | null}
 */
function queryDocumentElement(root) {
  if ("documentElement" in root) {
    return root.querySelector("[data-kpress-document-id], .kpress, [data-kpress-host-document]");
  }
  return root.matches("[data-kpress-document-id], .kpress, [data-kpress-host-document]")
    ? root
    : root.querySelector("[data-kpress-document-id], .kpress, [data-kpress-host-document]");
}

/**
 * @param {Document | Element} root
 * @param {KpressHostOptions} options
 * @returns {string}
 */
function documentId(root, options) {
  if (options.documentId) {
    return options.documentId;
  }
  const element = queryDocumentElement(root);
  const explicit = element?.getAttribute("data-kpress-document-id");
  if (explicit) {
    return explicit;
  }
  if (root instanceof Document && root.title) {
    return root.title;
  }
  return window.location.pathname || "kpress-document";
}

/**
 * @returns {{ height: number; width: number }}
 */
function measureDocument() {
  const body = document.body;
  const html = document.documentElement;
  const height = Math.ceil(
    Math.max(
      body?.scrollHeight ?? 0,
      body?.offsetHeight ?? 0,
      html.scrollHeight,
      html.offsetHeight,
      html.clientHeight,
    ),
  );
  const width = Math.ceil(Math.max(html.scrollWidth, html.offsetWidth, html.clientWidth));
  return { height, width };
}

/**
 * @param {Document | Element} root
 * @param {KpressHostOptions} options
 * @returns {boolean}
 */
function shouldUseEscapeClose(root, options) {
  if (typeof options.escapeClose === "boolean") {
    return options.escapeClose;
  }
  const element = queryDocumentElement(root);
  return element?.getAttribute("data-kpress-host-escape-close") === "true";
}

/**
 * @param {KpressHostMessageType} type
 * @param {KpressHostTarget} targetWindow
 * @param {string} targetOrigin
 * @param {string} id
 * @param {Partial<Pick<KpressHostMessage, "expanded" | "reason">>} [detail]
 */
function postKpressHostMessage(type, targetWindow, targetOrigin, id, detail = {}) {
  targetWindow.postMessage(
    {
      source: MESSAGE_SOURCE,
      version: MESSAGE_VERSION,
      type,
      documentId: id,
      ...measureDocument(),
      ...detail,
    },
    targetOrigin,
  );
}

/**
 * @param {Document | Element} [root]
 * @param {KpressHostOptions} [options]
 * @returns {KpressHostController}
 */
export function initKpressHost(root = document, options = {}) {
  const embedded = options.embedded ?? window.parent !== window;
  const targetWindow = options.targetWindow ?? (embedded ? window.parent : null);
  /** @type {Array<() => void>} */
  const cleanups = [];
  let lastSize = "";
  let resizeQueued = false;

  if (!embedded || !targetWindow) {
    return { postResize() {}, destroy() {} };
  }

  const id = documentId(root, options);
  const targetOrigin = options.targetOrigin ?? DEFAULT_TARGET_ORIGIN;
  const escapeClose = shouldUseEscapeClose(root, options);

  const post = (
    /** @type {KpressHostMessageType} */ type,
    /** @type {Partial<Pick<KpressHostMessage, "expanded" | "reason">>} */ detail = {},
  ) => postKpressHostMessage(type, targetWindow, targetOrigin, id, detail);

  const postResize = (force = false) => {
    const size = measureDocument();
    const key = `${size.width}x${size.height}`;
    if (!force && key === lastSize) {
      return;
    }
    lastSize = key;
    post("kpress:resize");
  };

  const scheduleResize = () => {
    if (resizeQueued) {
      return;
    }
    resizeQueued = true;
    requestAnimationFrame(() => {
      resizeQueued = false;
      postResize();
    });
  };

  const onExpand = (/** @type {Event} */ event) => {
    event.preventDefault();
    const target = event.currentTarget;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const expanded = target.getAttribute("aria-pressed") !== "true";
    target.setAttribute("aria-pressed", String(expanded));
    post("kpress:expand", { expanded });
    scheduleResize();
  };

  const onClose = (/** @type {Event} */ event) => {
    event.preventDefault();
    post("kpress:close", { reason: "control" });
  };

  const onKeydown = (/** @type {KeyboardEvent} */ event) => {
    if (!escapeClose || event.defaultPrevented || event.key !== "Escape") {
      return;
    }
    post("kpress:close", { reason: "escape" });
  };

  for (const trigger of root.querySelectorAll(
    '[data-kpress-host-action="expand"], [data-kpress-host-expand]',
  )) {
    trigger.addEventListener("click", onExpand);
    cleanups.push(() => trigger.removeEventListener("click", onExpand));
  }
  for (const trigger of root.querySelectorAll(
    '[data-kpress-host-action="close"], [data-kpress-host-close]',
  )) {
    trigger.addEventListener("click", onClose);
    cleanups.push(() => trigger.removeEventListener("click", onClose));
  }

  document.addEventListener("keydown", onKeydown);
  document.addEventListener("kpress:tabchange", scheduleResize);
  window.addEventListener("load", scheduleResize);
  window.addEventListener("resize", scheduleResize);
  cleanups.push(() => document.removeEventListener("keydown", onKeydown));
  cleanups.push(() => document.removeEventListener("kpress:tabchange", scheduleResize));
  cleanups.push(() => window.removeEventListener("load", scheduleResize));
  cleanups.push(() => window.removeEventListener("resize", scheduleResize));

  /** @type {ResizeObserver | null} */
  const observer =
    typeof ResizeObserver === "undefined" ? null : new ResizeObserver(scheduleResize);
  observer?.observe(document.documentElement);
  if (document.body) {
    observer?.observe(document.body);
  }
  cleanups.push(() => observer?.disconnect());

  post("kpress:ready");
  postResize(true);

  return {
    postResize() {
      postResize(true);
    },
    destroy() {
      for (const cleanup of cleanups.splice(0)) {
        cleanup();
      }
    },
  };
}

initKpressHost();
