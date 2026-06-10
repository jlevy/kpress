import { beforeEach, describe, expect, it, vi } from "vitest";

let importCounter = 0;

async function importFresh(relativePath) {
  importCounter += 1;
  const moduleUrl = new URL(`../../src/kpress/format/static/js/${relativePath}`, import.meta.url);
  return import(`${moduleUrl.href}?test=${importCounter}`);
}

beforeEach(() => {
  document.body.innerHTML = "";
  document.body.className = "";
  document.body.removeAttribute("style");
  Reflect.deleteProperty(globalThis, "ResizeObserver");
  vi.useRealTimers();
});

describe("overlay.js shared overlay primitive", () => {
  describe("computePosition", () => {
    it("places overlay below trigger when space is available", async () => {
      const { computePosition } = await importFresh("overlay.js");
      const result = computePosition(
        { top: 100, bottom: 120, left: 200, right: 260, width: 60, height: 20 },
        { width: 300, height: 150 },
        { viewportWidth: 1024, viewportHeight: 768, preferred: "bottom" },
      );
      expect(result.side).toBe("bottom");
      expect(result.top).toBeGreaterThanOrEqual(120);
      expect(result.left).toBeGreaterThanOrEqual(0);
    });

    it("flips to top when bottom overflows viewport", async () => {
      const { computePosition } = await importFresh("overlay.js");
      const result = computePosition(
        { top: 700, bottom: 720, left: 200, right: 260, width: 60, height: 20 },
        { width: 300, height: 150 },
        { viewportWidth: 1024, viewportHeight: 768, preferred: "bottom" },
      );
      expect(result.side).toBe("top");
      expect(result.top).toBeLessThan(700);
    });

    it("clamps left to viewport margin when trigger is near left edge", async () => {
      const { computePosition } = await importFresh("overlay.js");
      const result = computePosition(
        { top: 100, bottom: 120, left: 2, right: 62, width: 60, height: 20 },
        { width: 300, height: 150 },
        { viewportWidth: 1024, viewportHeight: 768, preferred: "bottom" },
      );
      expect(result.left).toBeGreaterThanOrEqual(10);
    });

    it("clamps right to viewport margin when trigger is near right edge", async () => {
      const { computePosition } = await importFresh("overlay.js");
      const result = computePosition(
        { top: 100, bottom: 120, left: 900, right: 960, width: 60, height: 20 },
        { width: 300, height: 150 },
        { viewportWidth: 1024, viewportHeight: 768, preferred: "bottom" },
      );
      expect(result.left + 300).toBeLessThanOrEqual(1024 - 10);
    });

    it("places overlay to the right when preferred is right", async () => {
      const { computePosition } = await importFresh("overlay.js");
      const result = computePosition(
        { top: 100, bottom: 120, left: 200, right: 260, width: 60, height: 20 },
        { width: 300, height: 150 },
        { viewportWidth: 1024, viewportHeight: 768, preferred: "right" },
      );
      expect(result.side).toBe("right");
      expect(result.left).toBeGreaterThanOrEqual(260);
    });

    it("respects custom gap between trigger and overlay", async () => {
      const { computePosition } = await importFresh("overlay.js");
      const result = computePosition(
        { top: 100, bottom: 120, left: 200, right: 260, width: 60, height: 20 },
        { width: 300, height: 150 },
        { viewportWidth: 1024, viewportHeight: 768, preferred: "bottom", gap: 20 },
      );
      expect(result.top).toBeGreaterThanOrEqual(140);
    });

    it("uses default gap of 10px when not specified", async () => {
      const { computePosition } = await importFresh("overlay.js");
      const result = computePosition(
        { top: 100, bottom: 120, left: 200, right: 260, width: 60, height: 20 },
        { width: 300, height: 150 },
        { viewportWidth: 1024, viewportHeight: 768, preferred: "bottom" },
      );
      expect(result.top).toBe(130);
    });
  });

  describe("dismissOnEscape", () => {
    it("calls dismiss callback when Escape is pressed", async () => {
      const { dismissOnEscape } = await importFresh("overlay.js");
      const dismiss = vi.fn();
      const cleanup = dismissOnEscape(dismiss);

      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
      expect(dismiss).toHaveBeenCalledTimes(1);

      cleanup();
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
      expect(dismiss).toHaveBeenCalledTimes(1);
    });

    it("ignores non-Escape keys", async () => {
      const { dismissOnEscape } = await importFresh("overlay.js");
      const dismiss = vi.fn();
      const cleanup = dismissOnEscape(dismiss);

      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
      expect(dismiss).not.toHaveBeenCalled();

      cleanup();
    });
  });

  describe("dismissOnResize", () => {
    it("calls dismiss callback on window resize", async () => {
      const { dismissOnResize } = await importFresh("overlay.js");
      const dismiss = vi.fn();
      const cleanup = dismissOnResize(dismiss);

      window.dispatchEvent(new Event("resize"));
      expect(dismiss).toHaveBeenCalledTimes(1);

      cleanup();
      window.dispatchEvent(new Event("resize"));
      expect(dismiss).toHaveBeenCalledTimes(1);
    });

    it("observes embedded viewport resize events", async () => {
      const resizeCallbacks = [];
      class TestResizeObserver {
        constructor(callback) {
          resizeCallbacks.push(callback);
        }

        observe = vi.fn();
        disconnect = vi.fn();
      }
      Object.defineProperty(globalThis, "ResizeObserver", {
        configurable: true,
        value: TestResizeObserver,
      });
      document.body.innerHTML = `<main data-kpress-viewport></main>`;
      const viewport = document.querySelector("[data-kpress-viewport]");
      const { dismissOnResize } = await importFresh("overlay.js");
      const dismiss = vi.fn();

      const cleanup = dismissOnResize(dismiss, viewport);
      resizeCallbacks[0]?.();

      expect(dismiss).toHaveBeenCalledTimes(1);
      cleanup();
    });
  });

  describe("viewport.js shared viewport context", () => {
    it("warns once when falling back to the document viewport", async () => {
      const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
      const { resolveKpressViewport } = await importFresh("viewport.js");

      resolveKpressViewport(document.body);
      resolveKpressViewport(document.body);

      expect(warn).toHaveBeenCalledTimes(1);
      expect(warn.mock.calls[0]?.[0]).toContain("data-kpress-viewport");
      warn.mockRestore();
    });

    it("resolves and measures embedded document viewport bounds", async () => {
      document.body.innerHTML = `
        <main data-kpress-viewport>
          <p><a id="inside" href="#target">Target</a></p>
        </main>
      `;
      const viewport = document.querySelector("[data-kpress-viewport]");
      const inside = document.getElementById("inside");
      viewport.getBoundingClientRect = () => ({
        left: 120,
        right: 520,
        top: 40,
        bottom: 340,
        width: 400,
        height: 300,
        x: 120,
        y: 40,
        toJSON() {},
      });
      inside.getBoundingClientRect = () => ({
        left: 160,
        right: 220,
        top: 90,
        bottom: 110,
        width: 60,
        height: 20,
        x: 160,
        y: 90,
        toJSON() {},
      });

      const { rectRelativeToViewport, resolveKpressViewport, viewportBounds } =
        await importFresh("viewport.js");

      expect(resolveKpressViewport(inside)).toBe(viewport);
      expect(viewportBounds(viewport)).toMatchObject({
        left: 120,
        top: 40,
        width: 400,
        height: 300,
      });
      expect(rectRelativeToViewport(inside.getBoundingClientRect(), viewport)).toMatchObject({
        left: 40,
        right: 100,
        top: 50,
        bottom: 70,
      });
    });
  });

  describe("dismissOnOutsideClick", () => {
    it("calls dismiss callback when clicking outside the overlay", async () => {
      const { dismissOnOutsideClick } = await importFresh("overlay.js");
      document.body.innerHTML = `
        <div id="overlay">Overlay</div>
        <div id="outside">Outside</div>
      `;
      const overlay = document.getElementById("overlay");
      const dismiss = vi.fn();
      const cleanup = dismissOnOutsideClick(overlay, dismiss);

      document.getElementById("outside")?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      expect(dismiss).toHaveBeenCalledTimes(1);

      cleanup();
    });

    it("does not call dismiss when clicking inside the overlay", async () => {
      const { dismissOnOutsideClick } = await importFresh("overlay.js");
      document.body.innerHTML = `
        <div id="overlay">Overlay</div>
      `;
      const overlay = document.getElementById("overlay");
      const dismiss = vi.fn();
      const cleanup = dismissOnOutsideClick(overlay, dismiss);

      overlay?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      expect(dismiss).not.toHaveBeenCalled();

      cleanup();
    });
  });

  describe("toggleBackdrop", () => {
    it("adds kpress-visible class when showing", async () => {
      const { toggleBackdrop } = await importFresh("overlay.js");
      document.body.innerHTML = `<div class="kpress-overlay-backdrop"></div>`;
      const backdrop = document.querySelector(".kpress-overlay-backdrop");

      toggleBackdrop(backdrop, true);
      expect(backdrop?.classList.contains("kpress-visible")).toBe(true);

      toggleBackdrop(backdrop, false);
      expect(backdrop?.classList.contains("kpress-visible")).toBe(false);
    });

    it("sets aria-hidden attribute", async () => {
      const { toggleBackdrop } = await importFresh("overlay.js");
      document.body.innerHTML = `<div class="kpress-overlay-backdrop"></div>`;
      const backdrop = document.querySelector(".kpress-overlay-backdrop");

      toggleBackdrop(backdrop, true);
      expect(backdrop?.getAttribute("aria-hidden")).toBe("false");

      toggleBackdrop(backdrop, false);
      expect(backdrop?.getAttribute("aria-hidden")).toBe("true");
    });

    it("is a no-op when backdrop is null", async () => {
      const { toggleBackdrop } = await importFresh("overlay.js");
      expect(() => toggleBackdrop(null, true)).not.toThrow();
    });
  });

  describe("OVERLAY_VIEWPORT_MARGIN_PX", () => {
    it("exports the default viewport margin", async () => {
      const { OVERLAY_VIEWPORT_MARGIN_PX } = await importFresh("overlay.js");
      expect(OVERLAY_VIEWPORT_MARGIN_PX).toBe(10);
    });
  });

  describe("OVERLAY_DEFAULT_GAP_PX", () => {
    it("exports the default gap", async () => {
      const { OVERLAY_DEFAULT_GAP_PX } = await importFresh("overlay.js");
      expect(OVERLAY_DEFAULT_GAP_PX).toBe(10);
    });
  });
});
