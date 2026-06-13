import { behaviors } from "./runtime.js";

let generatedTabGroupCounter = 0;

/**
 * @param {HTMLElement} group
 * @param {HTMLElement[]} tabs
 * @param {HTMLElement} tab
 */
function selectKpressTab(group, tabs, tab) {
  const panelId = tab.getAttribute("aria-controls");

  for (const other of tabs) {
    other.setAttribute("aria-selected", String(other === tab));
    other.setAttribute("tabindex", other === tab ? "0" : "-1");
  }

  for (const panel of group.querySelectorAll(".kpress-tab-panel")) {
    if (panel instanceof HTMLElement) {
      panel.hidden = panel.id !== panelId;
    }
  }

  group.dispatchEvent(new CustomEvent("kpress:tabchange", { bubbles: true, detail: { panelId } }));
}

/**
 * @param {HTMLElement[]} tabs
 * @param {HTMLElement} tab
 * @param {string} key
 * @returns {HTMLElement | null}
 */
function nextTabForKey(tabs, tab, key) {
  const currentIndex = tabs.indexOf(tab);
  if (key === "Home") {
    return tabs[0];
  }
  if (key === "End") {
    return tabs[tabs.length - 1];
  }
  if (key === "ArrowRight" || key === "ArrowDown") {
    return tabs[(currentIndex + 1) % tabs.length];
  }
  if (key === "ArrowLeft" || key === "ArrowUp") {
    return tabs[(currentIndex - 1 + tabs.length) % tabs.length];
  }
  return null;
}

/**
 * @param {Element} element
 * @returns {element is HTMLElement}
 */
function isHTMLElement(element) {
  return element instanceof HTMLElement;
}

/**
 * @param {string} value
 * @returns {string}
 */
function slugPart(value) {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "tab"
  );
}

/**
 * @param {HTMLElement} group
 * @returns {string}
 */
function ensureTabGroupId(group) {
  if (!group.id) {
    generatedTabGroupCounter += 1;
    group.id = `kpress-tabs-${generatedTabGroupCounter}`;
  }
  return group.id;
}

/**
 * @param {HTMLElement} group
 * @returns {HTMLElement[]}
 */
function authoredPanels(group) {
  return [...group.querySelectorAll(".kpress-tab-panel")].filter(isHTMLElement);
}

/**
 * @param {HTMLElement} group
 * @returns {HTMLElement[]}
 */
function hydrateAuthoredTabs(group) {
  const existingTabs = [...group.querySelectorAll("[role='tab']")].filter(isHTMLElement);
  if (existingTabs.length > 0) {
    return existingTabs;
  }

  const panels = authoredPanels(group);
  if (panels.length === 0) {
    return [];
  }

  const groupId = ensureTabGroupId(group);
  const tabList = document.createElement("div");
  tabList.className = "kpress-tab-list";
  tabList.setAttribute("role", "tablist");
  group.insertBefore(tabList, panels[0]);

  for (const [index, panel] of panels.entries()) {
    const selected = index === 0;
    const title = panel.dataset.kpressTabTitle?.trim() || `Tab ${index + 1}`;
    const slug = slugPart(title);
    const panelId = panel.id || `${groupId}-panel-${index + 1}-${slug}`;
    const tabId = `${groupId}-tab-${index + 1}-${slug}`;
    const tab = document.createElement("button");

    panel.id = panelId;
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", tabId);
    panel.hidden = !selected;

    tab.type = "button";
    tab.className = "kpress-tab-button";
    tab.id = tabId;
    tab.textContent = title;
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-controls", panelId);
    tab.setAttribute("aria-selected", String(selected));
    tab.setAttribute("tabindex", selected ? "0" : "-1");
    tabList.append(tab);
  }

  return [...tabList.querySelectorAll("[role='tab']")].filter(isHTMLElement);
}

/** @param {ParentNode} [root] */
export function initKpressTabs(root = document) {
  for (const group of root.querySelectorAll("[data-kpress-tabs]")) {
    if (!(group instanceof HTMLElement)) {
      continue;
    }
    const tabs = hydrateAuthoredTabs(group);
    for (const tab of tabs) {
      tab.classList.add("kpress-tab-button");
      if (tab.dataset.kpressTabBound === "true") {
        continue;
      }
      tab.dataset.kpressTabBound = "true";
      tab.addEventListener("click", () => {
        selectKpressTab(group, tabs, tab);
      });
      tab.addEventListener("keydown", (event) => {
        if (!(event instanceof KeyboardEvent)) {
          return;
        }
        const nextTab = nextTabForKey(tabs, tab, event.key);
        if (!nextTab) {
          return;
        }
        event.preventDefault();
        selectKpressTab(group, tabs, nextTab);
        nextTab.focus();
      });
    }
  }
}

behaviors.register("tabs", {
  bind: (root) => {
    initKpressTabs(/** @type {ParentNode} */ (root));
  },
});
