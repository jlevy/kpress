import { behaviors } from "./runtime.js";

// Mirrors _NUMERIC_CELL_RE in format/markdown.py: optional leading sign (ASCII
// or typographic minus U+2212), optional major currency symbol, grouped or
// plain digits, optional decimals, optional trailing percent. Whitespace is
// stripped before matching, so "$ 12.45" matches as "$12.45".
const NUMERIC_CELL_PATTERN = /^[-+−]?[$€¥£₹₩¢₽]?((\d{1,3}(,\d{3})+|\d+)(\.\d+)?|\.\d+)%?$/;

/**
 * Column-scoped numeric marking, mirroring the server-side renderer: a column
 * is numeric when at least one non-empty body (td) cell matches the numeric
 * pattern and no non-empty body cell mismatches (empty cells neither qualify
 * nor disqualify). Every cell of a numeric column — header included — gets
 * data-kpress-numeric; mixed columns get no marks and keep the default start
 * alignment. Tables using rowspan/colspan are left unmarked (spans shift cell
 * positions, so positional column identity is unreliable). Marks are also
 * cleared where the decision says no, so re-running converges.
 *
 * @param {Element} table
 */
function markNumericCells(table) {
  /** @type {{cell: Element, column: number}[]} */
  const cells = [];
  const numericColumns = new Set();
  const disqualifiedColumns = new Set();
  let hasSpan = false;
  for (const row of /** @type {HTMLTableElement} */ (table).rows) {
    let column = 0;
    for (const cell of row.cells) {
      const colspan = cell.getAttribute("colspan");
      const rowspan = cell.getAttribute("rowspan");
      if ((colspan && colspan !== "1") || (rowspan && rowspan !== "1")) {
        hasSpan = true;
      }
      cells.push({ cell, column });
      const text = (cell.textContent || "").replace(/\s+/g, "");
      if (cell.tagName === "TD" && text) {
        if (NUMERIC_CELL_PATTERN.test(text)) {
          numericColumns.add(column);
        } else {
          disqualifiedColumns.add(column);
        }
      }
      column += 1;
    }
  }
  for (const { cell, column } of cells) {
    const numeric = !hasSpan && numericColumns.has(column) && !disqualifiedColumns.has(column);
    if (numeric) {
      cell.setAttribute("data-kpress-numeric", "true");
    } else {
      cell.removeAttribute("data-kpress-numeric");
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
