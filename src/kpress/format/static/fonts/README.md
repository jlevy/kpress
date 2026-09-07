# Vendored Fonts

Every face a KPress document draws from is in this directory.
Nothing is fetched from a CDN at page load, and nothing is borrowed from the reader’s
machine: the rule is that a document resolves every text run to a face KPress ships, on
screen and in print.
The system stacks that trail each family in
[`style-tokens.css`](../css/style-tokens.css) are the fallback for a face that failed to
load, not part of the design.
The exception is `font_mode="system"`, where a page asks for the platform stack on
purpose and downloads none of these files.

All five families are under the
[SIL Open Font License 1.1](https://openfontlicense.org), which permits bundling and
redistribution; the license text for each ships in `src/kpress/licenses/`, and
[`NOTICE.md`](../../../../../NOTICE.md) is the top-level record.

## The Faces

| Family | Role | Files |
| --- | --- | --- |
| PT Serif | prose reading face, and the Latin letters inside mathematics | 4 static, 400/700 x normal/italic |
| Source Sans 3 Variable | sans on screen, at whatever weight a context asks for | 2 variable, `wght` x normal/italic |
| Source Sans 3 | sans in print, one static instance per weight | 12 generated, see below |
| Source Code Pro | mono: code fences, inline code, math error text | 2 static, 400/700 normal |
| KPress Quotes | the quotation marks and the apostrophe inside prose | 1 generated, 6 glyphs of Source Serif 4 |

## Provenance

The vendored bytes come from the [Fontsource](https://fontsource.org) npm packages,
which repackage the Google Fonts releases as per-subset woff2. Only the `latin` subset
is vendored. Each file below is byte-identical to the file of the same name inside the
pinned package, which is how the origin of the four faces that predate this record was
established: the extraction commit that brought PT Serif and Source Sans 3 into the
repository named no source, but their bytes match, so the source is not in doubt.

| File | Package | Version | sha256 |
| --- | --- | --- | --- |
| `pt-serif-latin-400-normal.woff2` | `@fontsource/pt-serif` | 5.3.0 | `4271064a37f3ffc0aac5f3806db8a72acc23e19447d1804e4e80d8796cbf6330` |
| `pt-serif-latin-400-italic.woff2` | `@fontsource/pt-serif` | 5.3.0 | `cb373bde18855c82a0ebf2946ea661ebd0be58a7fbabdf20f7744ecd9c0a9cfd` |
| `pt-serif-latin-700-normal.woff2` | `@fontsource/pt-serif` | 5.3.0 | `bf23a7a4eebedbb87d4084a69496b29815914a18e339a00f5dc73a03c9c9328f` |
| `pt-serif-latin-700-italic.woff2` | `@fontsource/pt-serif` | 5.3.0 | `3cb3cfab3c562cbbb5a53accf433f65ed1cd0403ea3bdd6ceeb73bf87f23521c` |
| `source-sans-3-latin-wght-normal.woff2` | `@fontsource-variable/source-sans-3` | 5.3.0 | `7a19a7027e125257d310c6dbd78ae3a30b5ea1e3794d60b12bb28227a003bfda` |
| `source-sans-3-latin-wght-italic.woff2` | `@fontsource-variable/source-sans-3` | 5.3.0 | `9a15dafc2c2b2414aaa9d6c30830d9aab4361329d8495b1574633603b994b411` |
| `source-code-pro-latin-400-normal.woff2` | `@fontsource/source-code-pro` | 5.3.0 | `75aa8cacfd459d58d7c093f3ff0ab8745cc878dfc93c5d4cda052791aeace878` |
| `source-code-pro-latin-700-normal.woff2` | `@fontsource/source-code-pro` | 5.3.0 | `34faf509fa4130733093f36100f76670ff7d93d4889746de11a62a0fe8d82084` |

Each file is `package/files/<name>` inside the package tarball.
To re-verify one:

```bash
npm pack @fontsource/source-code-pro@5.3.0 --ignore-scripts
tar xzf fontsource-source-code-pro-5.3.0.tgz
shasum -a 256 package/files/source-code-pro-latin-400-normal.woff2
```

All three packages were published on 2026-07-19, so the 14-day cool-off in
[`SUPPLY-CHAIN-SECURITY.md`](../../../../../SUPPLY-CHAIN-SECURITY.md) is satisfied.
None is an installed dependency: the bytes are vendored, and the package name and
version record where they came from.

The twelve `source-sans-3-latin-<weight>-<style>.woff2` files are **generated, not
vendored**. `devtools/instance_sans.py` instances them from the variable faces above,
and `python -m devtools.instance_sans --check` verifies the shipped bytes against a
fresh run, so they carry no hash here.

## The Quote Face

`kpress-quotes.woff2` is also generated, from a source that is **not** vendored.
PT Serif draws its own quotation marks badly, so KPress ships six glyphs of Source Serif
4 in their place and leads the prose stack with them over that `unicode-range`; the
reasoning is in [Quotation Marks](../../../../../docs/kpress-design.md#quotation-marks).
The 20 KB upstream face is a build input, and only the 724-byte subset is committed.

| Field | Value |
| --- | --- |
| Package | `@fontsource/source-serif-4` |
| Version | 5.3.0, published 2026-07-19 (OFL-1.1) |
| Source file | `package/files/source-serif-4-latin-400-normal.woff2`, 20,088 bytes |
| Source sha256 | `02194deb92d3975dd30e11a3824a1f1db32b48c93654e60560cb81ce8e7b5f95` |
| Command | `python -m devtools.subset_quotes` |
| Output | `kpress-quotes.woff2`, 724 bytes, 6 glyphs plus `.notdef` |
| Output sha256 | `c1b4e25238045596fcee7c888f5cc589d5294f59ab8feb2745c57824682df570` |

Fetch the source once, then generate:

```bash
mkdir -p ~/.cache/kpress/fonts && cd ~/.cache/kpress/fonts
npm pack @fontsource/source-serif-4@5.3.0 --ignore-scripts
tar xzOf fontsource-source-serif-4-5.3.0.tgz \
    package/files/source-serif-4-latin-400-normal.woff2 \
    > source-serif-4-latin-400-normal.woff2
```

`python -m devtools.subset_quotes --check` rebuilds the subset and compares it byte for
byte when that file is present, and falls back to checking the shipped file against the
output sha256 above when it is not.
Both hashes are pinned in the tool.

## Two Naming Quirks Worth Knowing

**Source Code Pro’s static files call themselves ExtraLight.** Both files report family
`Source Code Pro ExtraLight` and PostScript names `SourceCodeProExtraLight-Regular` and
`-Bold`, because Google Fonts instanced them from a variable font whose default axis
position is ExtraLight and did not rewrite the name table.
The outlines are the real 400 and 700 (`usWeightClass` 400 and 700; the stems differ),
and `@font-face` names the family, so nothing about rendering is affected.
It matters in one place: Chromium’s `CSS.getPlatformFontsForNode` reports the face’s own
name, so `tests/test_playwright_mono_face.py` asserts a `Source Code Pro` prefix rather
than an exact family name.
The bytes are vendored as published so the sha256 above can be checked against the
package.

**Source Sans 3 has two family names on purpose.** The variable face is
`Source Sans 3 Variable` and the print instances are `Source Sans 3`, which are the
upstream names of the two releases.
Keeping them distinct means the two never share a weight range and font matching never
has to break a tie; see
[Print Sans Faces](../../../../../docs/kpress-design.md#print-sans-faces).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
