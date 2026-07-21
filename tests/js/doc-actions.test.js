import { beforeEach, describe, expect, it, vi } from "vitest";
import { markdownTwinUrl, mountDocActions } from "../../src/kpress/format/static/js/doc-actions.js";
// The widget imports "./runtime.js" without cache-busting queries; share that
// instance to drive it.
import { widgets as sharedWidgets } from "../../src/kpress/format/static/js/runtime.js";

function docActionsMount() {
  const el = document.createElement("div");
  el.className = "kpress-widget kpress-doc-actions kpress-no-print";
  el.id = "kpress-doc-actions";
  el.setAttribute("data-kpress-widget", "doc-actions");
  document.body.appendChild(el);
  return el;
}

beforeEach(() => {
  document.body.innerHTML = "";
});

describe("markdownTwinUrl", () => {
  it("replaces an .html or .htm suffix with .md", () => {
    expect(markdownTwinUrl("/blog/report.html")).toBe("/blog/report.md");
    expect(markdownTwinUrl("/blog/report.htm")).toBe("/blog/report.md");
    expect(markdownTwinUrl("/blog/report.xhtml")).toBe("/blog/report.md");
  });

  it("appends .md to an extensionless path", () => {
    expect(markdownTwinUrl("/blog/report")).toBe("/blog/report.md");
  });

  it("maps directory paths to their index twin", () => {
    expect(markdownTwinUrl("/")).toBe("/index.md");
    expect(markdownTwinUrl("/blog/report/")).toBe("/blog/report/index.md");
    expect(markdownTwinUrl("/index.html")).toBe("/index.md");
  });
});

describe("doc-actions widget", () => {
  it("registers and renders both text badges with their labels", () => {
    const el = docActionsMount();
    sharedWidgets.mount("doc-actions", el, {});

    const print = el.querySelector("[data-kpress-doc-print]");
    const markdown = /** @type {HTMLAnchorElement} */ (el.querySelector("a"));
    expect(print?.textContent).toBe("PDF");
    expect(print?.getAttribute("aria-label")).toBe("Export PDF");
    expect(print?.getAttribute("title")).toBe("Export PDF");
    expect(markdown.textContent).toBe("MD");
    expect(markdown.getAttribute("aria-label")).toBe("View as Markdown");
    expect(markdown.getAttribute("title")).toBe("View as Markdown");
  });

  it("derives the markdown href from the page path by default", () => {
    const el = docActionsMount();
    mountDocActions(el, {});
    const markdown = /** @type {HTMLAnchorElement} */ (el.querySelector("a"));
    // jsdom serves at "/": the root twin.
    expect(markdown.getAttribute("href")).toBe("/index.md");
  });

  it("prefers an explicit markdown_url and escapes it", () => {
    const el = docActionsMount();
    mountDocActions(el, { markdown_url: '/raw/doc.md?a=1&b="2"' });
    const markdown = /** @type {HTMLAnchorElement} */ (el.querySelector("a"));
    expect(markdown.getAttribute("href")).toBe('/raw/doc.md?a=1&b="2"');
  });

  it("relocates its mount into the content card when one exists", () => {
    document.body.innerHTML =
      '<article class="kpress" data-kpress-card="on">' +
      '<div class="kpress-long-text"><h1>T</h1></div></article>';
    const el = docActionsMount();
    mountDocActions(el, {});
    expect(el.parentElement?.className).toBe("kpress-long-text");

    // Remount is idempotent: the mount stays in the card.
    mountDocActions(el, {});
    expect(el.parentElement?.className).toBe("kpress-long-text");
    expect(document.querySelectorAll(".kpress-doc-actions")).toHaveLength(1);
  });

  it("stays in place when no content card exists", () => {
    document.body.innerHTML =
      '<article class="kpress" data-kpress-card="off">' +
      '<div class="kpress-long-text"><h1>T</h1></div></article>';
    const el = docActionsMount();
    mountDocActions(el, {});
    expect(el.parentElement).toBe(document.body);
  });

  it("print button calls window.print", () => {
    const el = docActionsMount();
    mountDocActions(el, {});
    const print = vi.fn();
    vi.stubGlobal("print", print);
    const button = /** @type {HTMLElement} */ (el.querySelector("[data-kpress-doc-print]"));
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(print).toHaveBeenCalledTimes(1);
    vi.unstubAllGlobals();
  });

  it("config flags drop either action", () => {
    const el = docActionsMount();
    mountDocActions(el, { print: false });
    expect(el.querySelector("[data-kpress-doc-print]")).toBeNull();
    expect(el.querySelector("a")).toBeTruthy();

    mountDocActions(el, { markdown: false });
    expect(el.querySelector("[data-kpress-doc-print]")).toBeTruthy();
    expect(el.querySelector("a")).toBeNull();
  });
});
