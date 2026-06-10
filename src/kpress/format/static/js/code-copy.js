import { icon } from "./icons.js";

const COPY_STATE_RESET_DELAY_MS = 1200;

// Icons reference the inlined SVG sprite via ./icons.js. Icon-only: the visible label
// lives in aria-label/title, never as button text.

/**
 * @param {HTMLButtonElement} button
 * @param {string} state
 * @param {string} icon
 * @param {string} label
 */
function setCopyState(button, state, icon, label) {
  button.innerHTML = icon;
  button.setAttribute("aria-label", label);
  button.setAttribute("title", label);
  button.dataset.kpressCopyState = state;
}

/**
 * @param {HTMLButtonElement} button
 */
function resetCopyButton(button) {
  setCopyState(button, "idle", icon("copy"), "Copy code");
}

export function initKpressCodeCopy(root = document) {
  for (const pre of root.querySelectorAll("pre.kpress-code")) {
    if (pre.querySelector(".kpress-code-copy")) {
      continue;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = "kpress-code-copy kpress-no-print";
    button.setAttribute("aria-live", "polite");
    resetCopyButton(button);
    button.addEventListener("click", async () => {
      const code = pre.querySelector("code")?.textContent || pre.textContent || "";
      try {
        await navigator.clipboard?.writeText(code);
        setCopyState(button, "copied", icon("check"), "Code copied");
      } catch {
        setCopyState(button, "error", icon("triangle-alert"), "Copy failed");
      }
      setTimeout(() => {
        resetCopyButton(button);
      }, COPY_STATE_RESET_DELAY_MS);
    });
    pre.prepend(button);
  }
}

initKpressCodeCopy();
