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
// Threshold precedence, per table: explicit runtime config
// (`kpress.behaviors.configure("tables", { wideMinColumns, wideMinRowChars })`)
// wins; else the server-resolved values stamped on the enclosing article root
// (data-kpress-table-wide-min-*, see render.py) so a custom
// RenderOptions/kpress.yml cutoff survives this runtime's re-classification;
// else these built-in defaults (markup with no stamps, e.g. hand-authored
// fragments).
export const TABLE_WIDE_MIN_COLUMNS = 6;
export const TABLE_WIDE_MIN_ROW_CHARS = 100;

const TABLE_WIDE_MIN_COLUMNS_ATTR = "data-kpress-table-wide-min-columns";
const TABLE_WIDE_MIN_ROW_CHARS_ATTR = "data-kpress-table-wide-min-row-chars";

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
 * @param {Record<string, unknown>} config
 */
function markTableScale(table, config) {
  const wrap = table.parentElement?.closest(".kpress-table-wrap");
  if (!wrap || table.parentElement?.closest("table")) {
    return;
  }
  const thresholds = resolveThresholds(table, config);
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
 * The server-resolved threshold stamped on the table's nearest carrier (the
 * article root in rendered output), or null when absent or unparsable.
 *
 * @param {Element} table
 * @param {string} name
 * @returns {number | null}
 */
function stampedThreshold(table, name) {
  const carrier = table.closest(`[${name}]`);
  const value = carrier ? Number.parseInt(carrier.getAttribute(name) ?? "", 10) : Number.NaN;
  return Number.isFinite(value) && value >= 0 ? value : null;
}

/**
 * Per-table threshold resolution: explicit runtime config, else the document's
 * stamped server values, else the built-in defaults (see the precedence note
 * on TABLE_WIDE_MIN_COLUMNS).
 *
 * @param {Element} table
 * @param {Record<string, unknown>} [config]
 * @returns {{ wideMinColumns: number, wideMinRowChars: number }}
 */
function resolveThresholds(table, config = {}) {
  return {
    wideMinColumns:
      typeof config.wideMinColumns === "number"
        ? config.wideMinColumns
        : (stampedThreshold(table, TABLE_WIDE_MIN_COLUMNS_ATTR) ?? TABLE_WIDE_MIN_COLUMNS),
    wideMinRowChars:
      typeof config.wideMinRowChars === "number"
        ? config.wideMinRowChars
        : (stampedThreshold(table, TABLE_WIDE_MIN_ROW_CHARS_ATTR) ?? TABLE_WIDE_MIN_ROW_CHARS),
  };
}

/**
 * @param {ParentNode} [root]
 * @param {Record<string, unknown>} [config]
 */
export function initKpressTables(root = document, config = {}) {
  for (const table of root.querySelectorAll(".kpress-prose table:not(.kpress-table)")) {
    const wrapper = document.createElement("div");
    wrapper.className = "kpress-table-wrap";
    table.classList.add("kpress-table");
    markNumericCells(table);
    table.parentNode?.insertBefore(wrapper, table);
    wrapper.append(table);
    markTableScale(table, config);
  }

  for (const table of root.querySelectorAll(".kpress-prose table.kpress-table")) {
    markNumericCells(table);
    markTableScale(table, config);
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
