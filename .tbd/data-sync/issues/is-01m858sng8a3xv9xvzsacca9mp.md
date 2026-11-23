---
type: is
id: is-01m858sng8a3xv9xvzsacca9mp
title: "PR #82 S1: sanitized <input> output is not byte-stable"
kind: bug
status: closed
priority: 1
version: 3
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-23T22:35:31.719Z
updated_at: 2026-11-23T23:42:37.963Z
started_at: 2026-11-23T22:36:02.520Z
closed_at: 2026-11-23T23:42:37.962Z
close_reason: "fixed in 69a8b7f and 5c60a81: every kept input is written in KPress box order (_canonical_inputs); tests test_an_input_missing_type_and_disabled_has_one_serialization (200 calls) and test_input_serialization_is_the_same_in_every_process (8 processes, PYTHONHASHSEED 0-3 and random)"
resolution: null
duplicate_of: null
---
Security review of PR #82 (head 92ef5ad), should-fix, introduced by the PR. src/kpress/format/sanitize.py:472 set_tag_attribute_values={'input': _INPUT_SET_VALUES}: when an <input> has neither type nor disabled, nh3 0.3.5 adds both in HashMap order, so '<input>' sanitizes to either '<input disabled="disabled" type="checkbox">' or '<input type="checkbox" disabled="disabled">' about 50/50 per call (reproduced: 99/101 of 200).
