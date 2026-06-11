import { behaviors } from "./runtime.js";

/**
 * KPress inline video embed.
 *
 * A YouTube reference is rendered server-side as a safe, network-free
 * placeholder (`[data-kpress-video-id]`), so sanitized and sealed output never
 * ship an external `<iframe>`. At runtime this replaces each placeholder with
 * the inline YouTube player — no popup. The player (and its only network
 * request) loads when this script runs, and lazily once it scrolls into view.
 *
 * Embedding host apps inject the document fragment after this
 * module loads, so the behavior's bind also starts a MutationObserver that
 * embeds placeholders added later (and its disposer disconnects it, so an
 * override really turns the built-in off — late placeholders included).
 *
 * NOTE: the filename is historical (this used to be a click-to-open popover);
 * it is now an inline embedder. A rename is tracked as follow-up cleanup.
 */

const EMBED_HOST = "https://www.youtube-nocookie.com";

/**
 * @param {string | null} text
 * @returns {number}
 */
function parseStartSeconds(text) {
  if (!text) {
    return 0;
  }
  const trimmed = String(text).trim();
  const cleaned = trimmed.endsWith("s") ? trimmed.slice(0, -1) : trimmed;
  const seconds = Number.parseFloat(cleaned);
  return Number.isFinite(seconds) && seconds >= 0 ? Math.floor(seconds) : 0;
}

/**
 * @param {string} videoId
 * @param {number} startSeconds
 * @returns {string}
 */
function buildEmbedUrl(videoId, startSeconds) {
  const params = new URLSearchParams({ modestbranding: "1", rel: "0" });
  if (startSeconds > 0) {
    params.set("start", String(startSeconds));
  }
  return `${EMBED_HOST}/embed/${encodeURIComponent(videoId)}?${params.toString()}`;
}

/**
 * Replace one server-rendered placeholder with the inline YouTube player.
 * @param {Element} placeholder
 */
function embedVideo(placeholder) {
  const videoId = placeholder.getAttribute("data-kpress-video-id");
  if (!videoId) {
    return;
  }
  const startSeconds = parseStartSeconds(placeholder.getAttribute("data-kpress-video-start"));
  const title = placeholder.getAttribute("data-kpress-video-title") || "Video";
  const figure = document.createElement("figure");
  figure.className = "kpress-video";
  const iframe = document.createElement("iframe");
  iframe.className = "kpress-video-embed";
  iframe.src = buildEmbedUrl(videoId, startSeconds);
  iframe.title = title;
  iframe.loading = "lazy";
  iframe.referrerPolicy = "strict-origin-when-cross-origin";
  iframe.allow =
    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
  iframe.setAttribute("allowfullscreen", "");
  figure.appendChild(iframe);
  placeholder.replaceWith(figure);
}

/**
 * Embed every video placeholder under `root` (idempotent — embedded
 * placeholders are removed from the DOM, so they are not matched again).
 * @param {ParentNode} [root]
 */
export function initKpressVideoEmbeds(root = document) {
  for (const placeholder of root.querySelectorAll("[data-kpress-video-id]")) {
    embedVideo(placeholder);
  }
}

behaviors.register("video", {
  bind: (root) => {
    initKpressVideoEmbeds(/** @type {ParentNode} */ (root));
    if (
      typeof MutationObserver === "undefined" ||
      typeof document === "undefined" ||
      !document.body
    ) {
      return;
    }
    const observer = new MutationObserver((records) => {
      for (const record of records) {
        for (const node of record.addedNodes) {
          if (!(node instanceof Element)) {
            continue;
          }
          if (node.matches("[data-kpress-video-id]")) {
            embedVideo(node);
          }
          for (const nested of node.querySelectorAll("[data-kpress-video-id]")) {
            embedVideo(nested);
          }
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  },
});
