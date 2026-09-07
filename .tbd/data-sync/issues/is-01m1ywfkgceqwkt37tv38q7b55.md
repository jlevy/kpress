---
type: is
id: is-01m1ywfkgceqwkt37tv38q7b55
title: Document the print sans faces and the host weight contract
kind: task
status: in_progress
priority: 2
version: 2
labels:
  - docs
dependencies: []
parent_id: is-01m1ywfjt036hrzk0tk8p9je6v
created_at: 2026-09-07T21:30:41.547Z
updated_at: 2026-09-07T21:35:02.258Z
---
kpress-design.md: a Print Sans Faces note beside the fonts section (why Type3, the smoothing measurement, the family split). kpress-operations-and-host-integration.md: a host that overrides the sans weight tokens instances its own set with devtools/instance_sans.py's instance_face and face_rule (the file is importable standalone, fontTools only) and declares them for the 'Source Sans 3' family, or sets --kpress-host-font-sans-print. A short research note under docs/project/research/ recording the measurement (fonts in the PDF, stem widths, Quartz smoothing on/off table) following the tbd research conventions; docs/README.md index updated.
