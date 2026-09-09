# Vendored Fonts

Every face a KPress document ships is in this directory.
Nothing is fetched from a CDN at page load: the rule is that a document resolves its
text to a face KPress ships, on screen and in print.
The system stacks that trail each family in
[`style-tokens.css`](../css/style-tokens.css) are the fallback for a face that failed to
load, not part of the design.
Two settings stand outside the rule and ask for the platform on purpose:
`font_mode="system"` swaps every reader face for a system stack, and
`mono_font="system"` does the same for code and additionally drops the mono faces from
the asset manifest, so a page under it downloads none of them.

Every face here is under the [SIL Open Font License 1.1](https://openfontlicense.org),
which permits bundling and redistribution; the license text for each ships in
`src/kpress/licenses/`, and [`NOTICE.md`](../../../../../NOTICE.md) is the top-level
record.
Where that license reserves the upstream name for the original, the family KPress
generates carries a name of its own; where it does not, the vendored subset keeps the
upstream name.

## The Faces

| Family | Role | Files |
| --- | --- | --- |
| PT Serif | prose reading face, and the Latin letters inside mathematics | 4 static, 400/700 x normal/italic |
| Source Sans 3 Variable | sans on screen, at whatever weight a context asks for | 2 variable, `wght` x normal/italic |
| KPress Print Sans | sans in print, one static instance per weight | 10 generated from Source Sans 3, see below |
| KPress Quotes | the quotation marks and the apostrophe inside prose | 1 generated from Source Serif 4, 6 glyphs |
| Planetaire Mono Text | code, inline and fenced | 7 latin subsets, see below; 2 declared by default |

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

Each file is `package/files/<name>` inside the package tarball.
To re-verify one:

```bash
npm pack @fontsource/pt-serif@5.3.0 --ignore-scripts
tar xzf fontsource-pt-serif-5.3.0.tgz
shasum -a 256 package/files/pt-serif-latin-400-normal.woff2
```

All three packages, counting the Source Serif 4 one below, were published on 2026-07-19,
so the 14-day cool-off in
[`SUPPLY-CHAIN-SECURITY.md`](../../../../../SUPPLY-CHAIN-SECURITY.md) is satisfied.
None is an installed dependency: the bytes are vendored, and the package name and
version record where they came from.

The ten `kpress-print-sans-latin-<weight>-<style>.woff2` files are **generated, not
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

## The Mono Face

The seven `planetaire-mono-text-latin-<weight>-<style>.woff2` files are **latin subsets
of a vendored face**, not instances or a rename: `devtools/subset_mono.py` reduces each
upstream style to the same `unicode-range` above and keeps its family, style and
PostScript names, its copyright and its OFL notice exactly as upstream wrote them.
Planetaire declares no Reserved Font Name — contrast the first line of
`src/kpress/licenses/source-sans-3.txt` — so unlike the two generated families below
there is no OFL name to step around and the subsets keep the upstream one.
A separate condition arrives through Hack: the Bitstream Vera license asks that a
modified font be renamed to a name containing neither “Bitstream” nor “Vera”, and no
family, style, full or PostScript name in any of the seven files contains either.
Both words do stand in the copyright and license-description records, which is the
attribution that license asks be kept.

The copyright record names four holders: Joshua Levy for Planetaire, The B612 Project
Authors for the letterforms, Source Foundry Authors and Bitstream for Hack, and Ryan L
McIntyre for the Nerd Fonts glyph patches.
The last is attribution the upstream face carries rather than glyphs KPress ships: the
latin subsets map no Private Use Area code point at all, so no Nerd Fonts glyph reaches
a page. Its license text ships regardless, because the faces’ own license record cites
it.

Each subset ships beside a stylesheet of its own,
`../css/mono-planetaire-<weight>-<style>.css`, because `RenderOptions.mono_weights`
decides which styles a document declares and a single-file page carries every face it
declares.

| Field | Value |
| --- | --- |
| Package | [`jlevy/planetaire`](https://github.com/jlevy/planetaire) |
| Version | `v0.2.0`, published 2026-09-08 (OFL-1.1) |
| Version records inside the files | `Version 0.1.5`, see below |
| Source files | `fonts/web/PlanetaireMonoText-<style>.woff2`, 51 to 66 KB each |
| Command | `python -m devtools.subset_mono` |
| Output | 7 subsets of 13 to 17 KB, plus 7 stylesheets |

The upstream repository is one we publish ourselves, so the 14-day cool-off in
[`SUPPLY-CHAIN-SECURITY.md`](../../../../../SUPPLY-CHAIN-SECURITY.md) does not apply;
the tag and the per-file sha256 below are the pin, and nothing here is an installed
dependency.

The bytes are v0.2.0 and their version records say 0.1.5. Upstream’s release script
built the fonts before it created the tag, and the version resolves from
`git describe --tags --abbrev=0`, so the release commit stamped the preceding tag.
The published v0.2.0 archives and the jsDelivr `@v0.2.0` pin above serve those bytes
permanently, and re-fetching does not change them.
Only name IDs 3 and 5 and `head.fontRevision` carry the older number; the outlines,
metrics and glyph order are v0.2.0’s, and the source hashes below are the hashes of
`@v0.2.0`. A PDF font list or a browser font panel will say 0.1.5.

| Style | Subset | Bytes | Source sha256 | Subset sha256 |
| --- | --- | --- | --- | --- |
| `Regular` | `planetaire-mono-text-latin-400-normal.woff2` | 13,424 | `f412b36c96e0b92dcb0d9d476e572375706d449616d341c7429af02eac7b408f` | `0ecd530d8bdc55cc58ace248b570949c17043a16638b93c19a8c1a16591a23ed` |
| `Bold` | `planetaire-mono-text-latin-700-normal.woff2` | 13,960 | `3c56f2c14f843426a868cbd0730cdeff061eddb2614a7d9481ab885a4cf84820` | `5b01f48d9a28b2657a74cc1f36043544eb19800726a08775088d1478be2edb7b` |
| `Italic` | `planetaire-mono-text-latin-400-italic.woff2` | 14,840 | `348c6582e8ec6822a3d5d3fda89196f04320b5ed0b873ab1fb7404ede0ac7d7b` | `079d54b75f6d5822224ccb27d9d62e9fac0f12b6f6ee467b215ed8022ad87954` |
| `BoldItalic` | `planetaire-mono-text-latin-700-italic.woff2` | 15,036 | `a477f92124203bb20fc02c31ff6817584d879caa568ae3d88cc89e432fbba133` | `4665ca22f8e645185e6137e53a535a021f1d0e1a8b68f7a20c1c7f31f948b71b` |
| `Medium` | `planetaire-mono-text-latin-500-normal.woff2` | 16,232 | `fcfc30f97d941c24058aab40f9f1d3744dde4c19194df85327f2837227eaaf7f` | `ad5b7520c3a8c54c1752a14800cc1791590c17e8321637b2c74b7f963dae53ff` |
| `SemiBold` | `planetaire-mono-text-latin-600-normal.woff2` | 16,564 | `16d6807dc7157e4a2e9d86a7087ea2ebddf58d95b5909aca1305131d12b17bdc` | `d480c09ee43ab1f749ce1637555acd09e6f3674faae365ed2604e7314b6cc804` |
| `ExtraBold` | `planetaire-mono-text-latin-800-normal.woff2` | 16,524 | `51da9327a03ca057ccf156636086929d784ebd7037ce02f9d3763841802b7bdc` | `18e5a3f5eb67ade69a4ae21a64ab94a46e7064190f0f4468fceaec2fce622f9f` |

The subset hashes are the ones `devtools/subset_mono.py` pins in `SUBSET_SHA256` and
falls back to when the sources are absent.

Only regular and bold are declared by default: `code` at 400 and the syntax
highlighter’s keywords at 700. The other five opt in through `format.mono_weights`.
`syntax.css` also sets comments and docstrings italic, so under the default pair a
browser synthesizes the oblique; naming `italic` and `bold-italic` buys the drawn ones
for about 15 KB apiece.
The three heavier italics upstream offers are not vendored at all, since no rule reaches
an italic above 700.

Fetch the sources once, then generate:

```bash
mkdir -p ~/.cache/kpress/fonts && cd ~/.cache/kpress/fonts
for f in Regular Bold Italic BoldItalic Medium SemiBold ExtraBold; do
  curl -fLO "https://cdn.jsdelivr.net/gh/jlevy/planetaire@v0.2.0/fonts/web/PlanetaireMonoText-$f.woff2"
done
```

`python -m devtools.subset_mono --check` rebuilds every subset and compares it byte for
byte when the sources are present, and falls back to checking the shipped files against
the output hashes pinned in the tool when they are not.
The stylesheets are checked either way, since they are generated from the tool alone.

Five licence texts travel with these files, all under `src/kpress/licenses/`:
**Planetaire Mono** (`planetaire-mono.txt`, the OFL text plus the upstream notices) and
its three constituents — **B612 Mono** (`b612-mono.txt`, OFL-1.1, and
`b612-mono-epl-2.0.txt`, the Eclipse Public License 2.0 it is also offered under),
**Hack** (`hack.txt`, MIT plus the Bitstream Vera license), and **Nerd Fonts**
(`nerd-fonts.txt`, MIT for the tooling and OFL-1.1 for the glyph fonts).
That is the set the faces’ own license record names, which is what makes its closing
sentence — that the full texts ship with the distribution — true inside the wheel.

`planetaire-mono.txt` points at `fonts/source/licenses/B612-OFL.txt`, `Hack-LICENSE.md`
and `NerdFonts-LICENSE`. Those are paths in the Planetaire repository; here the same
texts are `b612-mono.txt`, `hack.txt` and `nerd-fonts.txt`, byte for byte.

## A Naming Quirk Worth Knowing

**The two generated families are named for KPress, not for their source.** The print
instances are `KPress Print Sans` and the quote subset is `KPress Quotes`, not
`Source Sans 3` and `Source Serif 4`. Both are modified versions of an OFL face whose
license reserves the upstream name for the original, and shipping them under it would
need Adobe’s permission.
Adobe’s copyright notice and the OFL notice travel in every generated file’s name table.
The rename also settles font matching, since a generated family never shares a weight
range or a code-point range with the face it came from; see
[Print Sans Faces](../../../../../docs/kpress-design.md#print-sans-faces) and
[Quotation Marks](../../../../../docs/kpress-design.md#quotation-marks).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
