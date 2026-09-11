---
type: is
id: is-01m215h3jrb38j3yedkt15rtys
title: Re-vendor Planetaire from the v0.2.0 release archive, not the git-tree pin
kind: task
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T18:47:16.823Z
updated_at: 2026-09-08T18:47:16.823Z
---
PR #62 review K62-R3. The vendored subsets carry 'Version 0.1.5' in nameID 5 and nameID 3 because upstream's release.py built the fonts before finalize created the tag, and src/planetaire/version.py resolves from `git describe --tags --abbrev=0`. Two divergent v0.2.0 artifact sets exist:

- the git tree at tag v0.2.0, which the jsDelivr pin in devtools/subset_mono.py and src/kpress/format/static/fonts/README.md fetches: stamped 0.1.5, ships OFL only;
- the GitHub release archive (PlanetaireMono-Text.tar.xz), built by CI at the tagged commit: stamped 0.2.0, ships all five licence texts including EPL-2.0 and EDL-1.0.

Verified metadata-only between them: 1317 glyphs, identical glyph order, zero outline-differing glyphs, identical advances/lsb, identical 1316-entry cmap, identical OS/2. Only name[3], name[5], head.fontRevision and head.checkSumAdjustment move.

PR #62 took the cheap path: NOTICE.md and the fonts README now record what the bytes say. The durable fix is to source from the release archive instead, which corrects the stamps at the same time. Frictions: the archive's web/ faces are pre-split by unicode-range so the ttf/ directory is the natural input, and every source_sha256 in SOURCES plus the README table changes. Alternative: wait for a planetaire release that re-tags, but nothing on fix/release-font-version-stamp does that, so the jsDelivr pin serves 0.1.5 bytes indefinitely. Upstream bead: see the planetaire repo.
