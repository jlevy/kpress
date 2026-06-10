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

document.addEventListener("kpress:tabchange", () => {
  initKpressTables();
});

initKpressTables();
