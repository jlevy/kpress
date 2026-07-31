---
type: is
id: is-01kyty6newbj90y6j0ab8y01vn
title: "Sizing core patch: base knob, calc conversions, contract, goldens"
kind: task
status: closed
priority: 1
version: 8
spec_path: docs/done/declarative-embedding.plan.md
labels: []
dependencies:
  - type: blocks
    target: is-01kyty81qvckvd016d7xbk24na
  - type: blocks
    target: is-01kyty825353x5bwv2j6znd8e5
  - type: blocks
    target: is-01kyty82gxnmdx4dz28hassyba
parent_id: is-01kytxz9k3cjy0drxwt3xsq9d8
created_at: 2026-07-31T01:56:42.587Z
updated_at: 2026-07-31T23:21:01.833Z
closed_at: 2026-07-31T02:10:29.072Z
close_reason: "Implemented: base knob + calc derivations across style-tokens/document/components/print, contract + docs additions, goldens regenerated; make lint-check and full pytest green."
---
Declare --kpress-font-size-base: var(--kpress-host-font-size-base, 1rem) on the four token scopes in style-tokens.css. Convert to calc(var(--kpress-font-size-base) * R): the size ramp (large/normal/small/smaller/tiny/mono/mono-small/mono-tiny), h2/h3/h4 tokens + wide-band redeclarations, caps-label + doc-actions-badge derivations, bullet size + offsets (-0.85/0.1), and every font-size literal in document.css (h1 1.7, h5/h6 1.0, doc-header clamp 1.75..2.3) and components.css (hero 1.6/1.5, sans-text 1.75/1.25, key-claims 1.2×mult). print.css: set base from --kpress-print-font-size inside @media print. contract.py: base -> PUBLIC_CSS_VARIABLES + PUBLIC_FRAGMENT_CSS_VARIABLES; hook -> PUBLIC_HOST_CSS_VARIABLES. Sizing-policy comment atop style-tokens.css. Update test_asset_contract.py pinned strings; regenerate goldens. Keep em/% where intentionally local (chevron 0.85em, checkbox 1.15em, sup/sub 85%).
