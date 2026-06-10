---
title: Markdown Features
---
# Markdown features

[Home](/) · [Getting started](/guides/getting-started.html) ·
**[Markdown features](/guides/markdown-features.html)** ·
[API reference](/reference/api/)

KPress renders GitHub-flavored Markdown plus a few extras.
This page exercises the common ones so you can see them styled.

## Text and Lists

Regular paragraphs support **bold**, *italic*, `inline code`, and
[links](https://example.com).
Lists nest cleanly:

1. First step
2. Second step
   - a sub-point
   - another sub-point
3. Third step

## Code with Syntax Highlighting

```python
def fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

## Tables

| Feature | Supported | Notes |
| --- | :---: | --- |
| Tables | ✅ | with alignment |
| Footnotes | ✅ | see below[^note] |
| Math | ✅ | inline $a^2 + b^2 = c^2$ |
| Blockquote | ✅ | styled with theme accents |

## Blockquote

> A static site generator should make the simple case trivial and the advanced case
> possible. KPress aims for both.

[^note]: Footnotes render at the bottom of the document with back-references.

