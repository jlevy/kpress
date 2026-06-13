import { behaviors } from "./runtime.js";

const NUMERIC_CELL_PATTERN = /^[-+]?((\d{1,3}(,\d{3})+)|\d+)(\.\d+)?%?$/;

/**
 * @param {Element} table
 */
function markNumericCells(table) {
  for (const cell of table.querySelectorAll("th, td")) {
    const text = cell.textContent?.trim() || "";
    if (NUMERIC_CELL_PATTERN.test(text)) {
      cell.setAttribute("data-kpress-numeric", "true");
    }
  }
}

/** @param {ParentNode} [root] */
export function initKpressTables(root = document) {
  for (const table of root.querySelectorAll(".kpress-prose table:not(.kpress-table)")) {
    const wrapper = document.createElement("div");
    wrapper.className = "kpress-table-wrap";
    table.classList.add("kpress-table");
    markNumericCells(table);
    table.parentNode?.insertBefore(wrapper, table);
    wrapper.append(table);
  }

  for (const table of root.querySelectorAll(".kpress-prose table.kpress-table")) {
    markNumericCells(table);
  }
}

behaviors.register("tables", {
  bind: (root) => {
    initKpressTables(/** @type {ParentNode} */ (root));
    // Tab panels reveal their tables lazily; re-wrap on every tab change. The
    // listener lives in bind (not at import) so an override really replaces
    // the built-in handling, and the disposer removes it.
    const onTabChange = () => {
      initKpressTables();
    };
    document.addEventListener("kpress:tabchange", onTabChange);
    return () => document.removeEventListener("kpress:tabchange", onTabChange);
  },
});
