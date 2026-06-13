/**
 * KPress extension-model demo (see ../extensions.md and kpress-design.md
 * "Extension and Injection Model"). Everything here is HOST code: it ships
 * with the site, not with KPress, and changes no KPress source — that is the
 * point. It exercises, in ~80 lines:
 *
 *  1. a NEW widget (`minimap`) computed from the published page model,
 *  2. a different face on a built-in engine (`theme-toggle` over kpress.theme),
 *  3. a one-aspect tweak of a built-in behavior (TOC toggle: custom icon +
 *     always-visible policy, via callback config),
 *  4. a behavior override over unchanged markup (footnote-preview), and
 *  5. injected HTML made interactive (a glossary behavior over [data-gloss]).
 *
 * The `kpress` global is assembled by the page's own assets (runtime.js loads
 * first); this module runs after the built-ins register and before the runtime
 * applies, so overrides take effect cleanly.
 */

const kpress = /** @type {any} */ (globalThis).kpress;

// 1. A new widget: a minimap built from the page model's headings.
//    Enabled per page via `format.widgets: {minimap: on}` (the mount comes
//    from the server; this code only ever sees its own mount element).
//    Model strings are data, not markup — build DOM nodes, never interpolate
//    them into innerHTML. Static styling lives in demo/extensions.css.
kpress.widgets.register("minimap", {
  mount(el, _config, model) {
    const headings = Array.isArray(model.headings) ? model.headings : [];
    const nav = document.createElement("nav");
    nav.setAttribute("aria-label", "Minimap");
    for (const h of headings) {
      const link = document.createElement("a");
      link.href = h.href;
      link.textContent = h.title;
      link.style.paddingInlineStart = `${(h.level - 1) * 8}px`;
      nav.append(link);
    }
    el.replaceChildren(nav);
  },
});

// 2. A bare dark/light toggle over the built-in theme engine — the gear menu
//    is only the engine's default face. (A site wanting ONLY this control
//    sets `widgets: {settings: off, theme-toggle: on}`.)
kpress.widgets.register("theme-toggle", {
  mount(el) {
    el.innerHTML = `<button type="button" aria-label="Toggle theme">◐</button>`;
    el.querySelector("button")?.addEventListener("click", () => {
      kpress.theme.set(kpress.theme.resolved() === "dark" ? "light" : "dark");
    });
  },
});

// 3. Tweak ONE aspect of the built-in TOC behavior: a custom toggle icon and
//    an always-visible policy — callback config, no binary KPress setting.
//    (`defaultTocToggleVisible` stays importable from the toc module for
//    hosts that want to wrap rather than replace the policy.)
kpress.behaviors.configure("toc", {
  icon: `<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/></svg>`,
  visible: () => true,
});

// 4. Override footnote hover handling over the SAME markup: jump-on-click
//    instead of hover previews (a deliberately different reading style).
kpress.behaviors.override("footnote-preview", (root) => {
  for (const anchor of root.querySelectorAll('sup a[href^="#fn-"]')) {
    anchor.addEventListener("click", (event) => {
      event.preventDefault();
      const id = (anchor.getAttribute("href") || "").slice(1);
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    });
  }
});

// 5. Injected HTML made interactive: the page's Markdown carries
//    <span data-gloss="..."> spans; this registered behavior binds them the
//    same way KPress binds its own document markup.
kpress.behaviors.register("glossary", {
  bind(root) {
    for (const term of root.querySelectorAll("[data-gloss]")) {
      term.setAttribute("title", term.getAttribute("data-gloss") || "");
    }
  },
});
