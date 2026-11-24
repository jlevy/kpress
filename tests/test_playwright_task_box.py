"""Real-browser check that a task list draws the same box without KPress's classes.

A host that sanitizes KPress's HTML again can keep the box as `<input type="checkbox"
disabled>`, with `checked` when ticked, and strip every class: Metabrowser's inert
hardener does. The task styling used to hang only on `li.kpress-task`, so there the box
drew as the browser's own grey disabled checkbox and the list bullet stayed. The styles
now key on the box's place as well, the first element of the item or of its first
paragraph, which is safe in `sanitized` output because the box is the only `<input>`
that survives.

This builds a page, copies each task list with every class removed and each box reduced
to those attributes, and compares what Chromium computes for the two, on screen and in
print, item by item. Only a `ul` item drops its marker for the box: an ordered item,
a footnote among them, keeps its number, so a class-free ordered task list shows the
number beside the box, where KPress's classed one shows the box alone.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import pytest

from kpress.publish import build_site

#: Tight and loose task lists, an ordered one, one nested in an ordered item (which
#: print.css restyles), and a list that mixes a plain item, whose bullet stays, with a
#: task item.
_SOURCE = (
    "# Task boxes\n\n"
    "- [ ] Open, tight\n"
    "- [x] Done, tight\n\n"
    "Between.\n\n"
    "- [ ] Open, loose\n\n"
    "- [x] Done, loose\n\n"
    "Between.\n\n"
    "1. [ ] Ordered open\n"
    "2. [x] Ordered done\n"
    "3. An ordered item that carries a nested task list.\n"
    "   - [ ] Nested open\n"
    "   - [x] Nested done\n\n"
    "Between.\n\n"
    "- A plain item, whose bullet stays.\n"
    "- [x] A task item beside it.\n"
)

#: Copy each top-level list, strip every class from the copy, and reduce each box to the
#: attributes a class-stripping host keeps. The copy goes right after its original, in
#: the same `.kpress-prose`, so the same rules reach both.
_STRIP_CLASSES = """
() => {
  const prose = document.querySelector(".kpress-prose");
  const lists = [...prose.querySelectorAll(":scope > ul, :scope > ol")];
  lists.forEach((list, index) => {
    const bare = list.cloneNode(true);
    for (const node of [bare, ...bare.querySelectorAll("*")]) {
      node.removeAttribute("class");
    }
    for (const box of bare.querySelectorAll("input")) {
      for (const name of box.getAttributeNames()) {
        if (!["type", "disabled", "checked"].includes(name)) box.removeAttribute(name);
      }
    }
    list.dataset.probe = `classed-${index}`;
    bare.dataset.probe = `bare-${index}`;
    list.after(bare);
  });
  return lists.length;
}
"""

#: What Chromium computes for each item of a list and its box, with the box's place
#: relative to its item, so that a moved or resized box shows as well as a restyled one.
_DESCRIBE = """
(probe) => {
  const list = document.querySelector(`[data-probe="${probe}"]`);
  return [...list.querySelectorAll("li")].map((item) => {
    const style = getComputedStyle(item);
    const before = getComputedStyle(item, "::before");
    const itemRect = item.getBoundingClientRect();
    const box = item.querySelector(":scope > input, :scope > p:first-child > input");
    let drawn = null;
    if (box) {
      const css = getComputedStyle(box);
      const rect = box.getBoundingClientRect();
      drawn = {
        appearance: css.appearance,
        background: css.backgroundColor,
        mask: css.maskImage,
        maskSize: css.maskSize,
        width: css.width,
        height: css.height,
        marginEnd: css.marginInlineEnd,
        verticalAlign: css.verticalAlign,
        cursor: css.cursor,
        left: rect.left - itemRect.left,
        top: rect.top - itemRect.top,
        checked: box.checked,
      };
    }
    return {
      text: item.textContent.trim().split("\\n")[0],
      ordered: item.parentElement.tagName === "OL",
      listStyle: style.listStyleType,
      bullet: before.content,
      height: itemRect.height,
      box: drawn,
    };
  });
}
"""


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path, source: str) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(source, encoding="utf-8")
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


def _launch_chromium(playwright: Any, sync_api: Any) -> Any:
    """Require the bundled browser in CI; locally try Chrome before skipping."""
    if os.environ.get("KPRESS_REQUIRE_BROWSER") == "1":
        return playwright.chromium.launch(headless=True)
    try:
        return playwright.chromium.launch(headless=True)
    except sync_api.Error:
        try:
            return playwright.chromium.launch(headless=True, channel="chrome")
        except sync_api.Error as exc:
            pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")


@contextmanager
def _task_page(tmp_path: Path, source: str = _SOURCE) -> Generator[Any]:
    """A site of *source*, served locally and open in Chromium with its fonts settled."""
    sync_api = (
        import_module("playwright.sync_api")
        if os.environ.get("KPRESS_REQUIRE_BROWSER") == "1"
        else pytest.importorskip("playwright.sync_api")
    )
    public = _build_fixture_site(tmp_path, source)
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_api.sync_playwright() as playwright:
            browser = _launch_chromium(playwright, sync_api)
            try:
                context = browser.new_context(viewport={"width": 900, "height": 900})
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector(".kpress-prose")
                page.evaluate("document.fonts.ready")
                yield page
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_a_task_list_without_classes_draws_as_the_classed_one(tmp_path: Path) -> None:
    with _task_page(tmp_path) as page:
        count = cast(int, page.evaluate(_STRIP_CLASSES))
        assert count == 4
        described: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for media in ("screen", "print"):
            page.emulate_media(media=media)
            page.evaluate("document.fonts.ready")
            for index in range(count):
                for form in ("classed", "bare"):
                    probe = f"{form}-{index}"
                    described[media, probe] = cast(
                        list[dict[str, Any]], page.evaluate(_DESCRIBE, probe)
                    )

    for media in ("screen", "print"):
        for index in range(count):
            classed = described[media, f"classed-{index}"]
            bare = described[media, f"bare-{index}"]
            for classed_item, bare_item in zip(classed, bare, strict=True):
                if bare_item["ordered"] and bare_item["box"] is not None:
                    # An ordered item keeps its number without `.kpress-task`.
                    if media == "screen":
                        assert (classed_item["listStyle"], bare_item["listStyle"]) == (
                            "none",
                            "decimal",
                        ), bare_item
                    classed_item = {**classed_item, "listStyle": None}
                    bare_item = {**bare_item, "listStyle": None}
                assert bare_item == classed_item, (media, index)

    # And what both draw is KPress's box with no bullet, not the browser's checkbox.
    screen = [item for index in range(count) for item in described["screen", f"bare-{index}"]]
    tasks = [item for item in screen if item["box"] is not None]
    assert len(tasks) == 9
    for item in tasks:
        assert item["box"]["appearance"] == "none", item
        assert item["box"]["mask"].startswith('url("data:image/svg+xml'), item
        assert item["bullet"] in ("none", "normal"), item
        assert item["listStyle"] == ("decimal" if item["ordered"] else "none"), item
    assert [item["box"]["checked"] for item in tasks] == [
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        True,
    ]
    # A plain item keeps its bullet, beside a task item as anywhere else.
    plain = [item for item in screen if item["text"].startswith("A plain item")]
    assert [item["bullet"] for item in plain] == ['""']


#: An ordered item and a footnote whose first element is a box, each beside one that
#: is not. `sanitized` output, which a site build writes, keeps the raw box disabled.
_NUMBERED_SOURCE = (
    "# Numbered boxes\n\n"
    '1. <input type="checkbox" disabled> first\n'
    "2. second\n\n"
    "Note[^1] and another[^2].\n\n"
    '[^1]: <input type="checkbox" disabled> pending\n'
    "[^2]: plain\n"
)

#: Each ordered item's marker, on its own and through `::before`, which print draws.
_MARKERS = """
() => [...document.querySelectorAll(".kpress-prose ol > li")].map((item) => ({
  text: item.textContent.trim(),
  listStyle: getComputedStyle(item).listStyleType,
  before: getComputedStyle(item, "::before").content,
}))
"""


def test_an_ordered_item_or_footnote_that_starts_with_a_box_keeps_its_number(
    tmp_path: Path,
) -> None:
    with _task_page(tmp_path, _NUMBERED_SOURCE) as page:
        markers: dict[str, list[dict[str, str]]] = {}
        for media in ("screen", "print"):
            page.emulate_media(media=media)
            markers[media] = cast(list[dict[str, str]], page.evaluate(_MARKERS))

    for media, items in markers.items():
        assert [item["text"].split()[0] for item in items] == [
            "first",
            "second",
            "pending",
            "plain",
        ], media
        boxed = [items[0], items[2]]
        plain = [items[1], items[3]]
        for box_item, plain_item in zip(boxed, plain, strict=True):
            assert {**box_item, "text": ""} == {**plain_item, "text": ""}, media
    assert markers["screen"][0]["listStyle"] == "decimal"
