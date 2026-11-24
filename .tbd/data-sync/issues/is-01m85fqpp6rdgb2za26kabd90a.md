---
type: is
id: is-01m85fqpp6rdgb2za26kabd90a
title: "Raw HTML's sanitizer cost is n*m: html5ever rebuilds every formatting element left open at each later block"
kind: bug
status: open
priority: 2
version: 1
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-11-24T00:36:47.428Z
updated_at: 2026-11-24T00:36:47.428Z
---
`sanitize_raw_html` (through `nh3.clean`, ammonia on html5ever) costs the product of
two counts in its input, not its size: HTML5's tree builder rebuilds every formatting
element still open at each later block that holds text ("reconstruct the active
formatting elements"). One line of raw HTML, `n` distinct `<b a=i>` and then `m`
`<div>x</div>`, renders `n * m` elements.

Found by review A of Metabrowser PR #766 (finding A1,
https://github.com/jlevy/metabrowser/pull/766#pullrequestreview-6030955099).
Metabrowser tracks its side as mb-zrng: its Markdown child, which renders untrusted
documents with KPress, is bounded only by a deadline, so its memory is bounded by how
much of this a deadline admits.

## Reproduction (KPress 0.3.9, nh3)

```python
from kpress.format.sanitize import sanitize_raw_html

n, m = 2_511, 1_998
html = "<div>" + "".join(f"<b a={i}>" for i in range(n)) + "</div>" + "<div>x</div>" * m
sanitize_raw_html(html, "sanitized")  # 47,988 bytes in
```

Measured 2026-11-23 on an Apple M1 Pro, Python 3.14.7, at a load average of 220 to 340:
`nh3.clean` alone took 40 s and 1,281 MB on those 47,988 bytes (5 million `<b>` out).
Smaller sizes, on the whole Markdown render:

| Bytes | `n * m` | Time | Peak RSS |
| --- | --- | --- | --- |
| 7,987 | 151,267 | 3.9 s | 128 MB |
| 11,989 | 338,142 | 10.5 s | 189 MB |
| 15,988 | 598,928 | 20.4 s | 280 MB |
| 23,988 | 1,308,378 | 59.5 s | 459 MB |

## Why a caller cannot bound it from outside

No count over the input is a sound bound. Markdown's own elements can be stranded by
raw HTML: a raw `<table>` inside `**bold**` leaves the `strong` on the list of active
formatting elements, and `</strong>` inside the table is not in scope and removes
nothing. A sound estimate needs the tree builder's markers, scopes, Noah's Ark clause
and adoption agency algorithm, so it is the parser's to make.

## Possible fixes

- Refuse, or render as text, input whose rebuilt-element count passes a limit, counted
  by the parser as it builds.
- Close formatting elements at block boundaries before sanitizing, as a Markdown
  renderer's own output always does, so raw HTML cannot leave them open.
- Cap the output size of `sanitize_raw_html` and say so to the caller.
