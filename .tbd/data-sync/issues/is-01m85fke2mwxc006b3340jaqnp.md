---
type: is
id: is-01m85fke2mwxc006b3340jaqnp
title: "Text after a stray <td> or <th> is dropped: the postprocessor never flushes its buffered cell"
kind: bug
status: open
priority: 2
version: 1
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-11-24T00:34:27.533Z
updated_at: 2026-11-24T00:34:27.533Z
---
`_postprocess_html` drops everything after a `<td>` or `<th>` that no table holds and
no end tag closes, so the Document view shows none of the text that follows.

Found by review A of Metabrowser PR #766 (finding A12,
https://github.com/jlevy/metabrowser/pull/766#pullrequestreview-6030955099), where the
rendered diff of such a file shows nothing of what it added and flags the file
source-only. Metabrowser tracks its side as mb-5b1w.

## Reproduction (KPress 0.3.9)

```python
from kpress.format import parse_markdown
from kpress.format.markdown import _postprocess_html
from kpress.format.sanitize import sanitize_raw_html

source = "# Title\n\n<td>\n\nA paragraph after.\n\nAnother one.\n"
parse_markdown(source, title="", trust_mode="sanitized").html
# '<h1 id="title">Title</h1>'
html = '<h1>Title</h1>\n<td>\n<p>A paragraph after.</p>\n<p>Another one.</p>\n'
_postprocess_html(html)               # '<h1>Title</h1>\n'
sanitize_raw_html(html, "sanitized")[0]  # keeps both paragraphs
```

`<th>` behaves the same.

## What others do

- CommonMark (markdown-it-py's `commonmark` preset, and `gfm-like`): `<td>` is an
  HTML block (type 6) that ends at the blank line, and the paragraphs render:
  `<h1>Title</h1>\n<td>\n<p>A paragraph after.</p>\n<p>Another one.</p>\n`.
- A browser's HTML parser ignores a `td` or `th` start tag in body (HTML's "in body"
  insertion mode: a parse error, the token ignored), so it shows both paragraphs.
- GitHub (`gh api markdown -f mode=gfm`, 2026-11-23) drops the stray tag and keeps the
  text: `<h1>Title</h1>\n\n<p>A paragraph after.</p>\n<p>Another one.</p>`.

## Cause

The postprocessor's parser buffers a cell on its start tag (`src/kpress/format/markdown.py`,
`if not self._cell and normalized_tag in {"td", "th"}: self._cell = _BufferedCell(...)`)
and writes it only in `_flush_cell`, on the cell's end tag or a table boundary.
`_postprocess_html` calls `parser.close()` and joins `parser.parts` without flushing a
cell still open, so the buffered cell and every part appended to it after are lost.

## Fix

Buffer a cell only inside a table (`self._table_depth > 0`), or flush an open cell at
`close()` and at any end of the buffered region, so text after a stray cell tag is kept
as the browser and GitHub keep it. Add the reproduction as a test.
