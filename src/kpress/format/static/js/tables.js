import { behaviors } from "./runtime.js";

// Mirrors _NUMERIC_CELL_RE in format/markdown.py: optional leading sign (ASCII
// or typographic minus U+2212), optional major currency symbol, grouped or
// plain digits, optional decimals, optional trailing percent. Whitespace is
// stripped before matching, so "$ 12.45" matches as "$12.45".
const NUMERIC_CELL_PATTERN = /^[-+−]?[$€¥£₹₩¢₽]?((\d{1,3}(,\d{3})+|\d+)(\.\d+)?|\.\d+)%?$/;

// Wide-table cutoff, mirroring TABLE_WIDE_MIN_* in format/markdown.py: a table
// earns the wide presentation (data-kpress-table-scale="wide" on its wrap,
// which the CSS turns into a bleed past the reading column on wide panes and
// an edge-bleed scroll region on phones) only when it is large on BOTH axes.
// Host-tunable via `kpress.behaviors.configure("tables", { wideMinColumns,
// wideMinRowChars })`.
export const TABLE_WIDE_MIN_COLUMNS = 6;
export const TABLE_WIDE_MIN_ROW_CHARS = 100;

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

/**
 * Wide-table marking, mirroring `_finalize_table_scale` in format/markdown.py:
 * the table's wrap gets `data-kpress-table-scale="wide"` only when the widest
 * row has at least `wideMinColumns` cells AND the average row carries at least
 * `wideMinRowChars` visible characters. The mark is also cleared where the
 * decision says no, so re-running converges (matching the numeric marking).
 * Nested tables are skipped, matching the server, which sizes only top-level
 * tables.
 *
 * @param {Element} table
 * @param {{ wideMinColumns: number, wideMinRowChars: number }} thresholds
 */
function markTableScale(table, thresholds) {
  const wrap = table.parentElement?.closest(".kpress-table-wrap");
  if (!wrap || table.parentElement?.closest("table")) {
    return;
  }
  let maxColumns = 0;
  let totalChars = 0;
  let rowCount = 0;
  for (const row of /** @type {HTMLTableElement} */ (table).rows) {
    maxColumns = Math.max(maxColumns, row.cells.length);
    let rowChars = 0;
    for (const cell of row.cells) {
      rowChars += (cell.textContent || "").replace(/\s+/g, " ").trim().length;
    }
    totalChars += rowChars;
    rowCount += 1;
  }
  const averageRowChars = rowCount ? totalChars / rowCount : 0;
  const wide =
    maxColumns >= thresholds.wideMinColumns && averageRowChars >= thresholds.wideMinRowChars;
  if (wide) {
    wrap.setAttribute("data-kpress-table-scale", "wide");
  } else {
    wrap.removeAttribute("data-kpress-table-scale");
  }
}

/**
 * @param {Record<string, unknown>} [config]
 * @returns {{ wideMinColumns: number, wideMinRowChars: number }}
 */
function scaleThresholds(config = {}) {
  return {
    wideMinColumns:
      typeof config.wideMinColumns === "number" ? config.wideMinColumns : TABLE_WIDE_MIN_COLUMNS,
    wideMinRowChars:
      typeof config.wideMinRowChars === "number"
        ? config.wideMinRowChars
        : TABLE_WIDE_MIN_ROW_CHARS,
  };
}

/**
 * @param {ParentNode} [root]
 * @param {Record<string, unknown>} [config]
 */
export function initKpressTables(root = document, config = {}) {
  const thresholds = scaleThresholds(config);
  for (const table of root.querySelectorAll(".kpress-prose table:not(.kpress-table)")) {
    const wrapper = document.createElement("div");
    wrapper.className = "kpress-table-wrap";
    table.classList.add("kpress-table");
    markNumericCells(table);
    table.parentNode?.insertBefore(wrapper, table);
    wrapper.append(table);
    markTableScale(table, thresholds);
  }

  for (const table of root.querySelectorAll(".kpress-prose table.kpress-table")) {
    markNumericCells(table);
    markTableScale(table, thresholds);
  }
}

behaviors.register("tables", {
  bind: (root, config) => {
    initKpressTables(/** @type {ParentNode} */ (root), config);
    // Tab panels reveal their tables lazily; re-wrap on every tab change. The
    // listener lives in bind (not at import) so an override really replaces
    // the built-in handling, and the disposer removes it.
    const onTabChange = () => {
      initKpressTables(document, config);
    };
    document.addEventListener("kpress:tabchange", onTabChange);
    return () => document.removeEventListener("kpress:tabchange", onTabChange);
  },
});
