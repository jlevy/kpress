---
type: is
id: is-01kyv0jmhxzvnv00kgpkkh7tz4
title: "PR #40 review F2: sanctioned ramp-override tier in the contract"
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/done/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxz9k3cjy0drxwt3xsq9d8
created_at: 2026-07-31T02:38:12.029Z
updated_at: 2026-07-31T23:21:03.232Z
closed_at: 2026-07-31T02:40:43.311Z
close_reason: Ramp tier public in both contract lists with docs + guidance rewording; tooltip portal case and fallback-literal lint test added; 33 focused tests green.
---
Per jlevy's PR #40 spec review finding 2: promote the full size ramp (large/smaller/tiny/mono-small/mono-tiny), --kpress-caps-label-size, --kpress-bullet-size, and the h2/h3/h4 tokens into PUBLIC_CSS_VARIABLES and PUBLIC_FRAGMENT_CSS_VARIABLES so hosts have a sanctioned divergence tier; reword guidance to 'set the base; override ramp tokens only for deliberate design divergence'. Add portaled-tooltip case to the two-root sizing test (acceptance bar).
