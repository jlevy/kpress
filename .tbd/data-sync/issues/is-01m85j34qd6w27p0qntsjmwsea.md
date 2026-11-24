---
type: is
id: is-01m85j34qd6w27p0qntsjmwsea
title: Each Playwright math page launches and closes its own Chromium, which on the macOS dev host idles 9-30 s after Browser.close until Playwright 1.60 kills it, so a test with three pages passes the 60 s timeout
kind: bug
status: open
priority: 2
version: 1
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-11-24T01:17:59.404Z
updated_at: 2026-11-24T01:17:59.404Z
---
Seen 2026-11-23 15:12 on claude/task-list-checkboxes (attic/full_pytest_1.txt): a full pytest run was ended by pytest-timeout (60 s, thread method, pyproject.toml) at test 435 of 848-857. Collection order since then is unchanged up to that index (the x/s pattern of tests 361-432 matches the current collection exactly, and no commit since touched a test file that sorts before it), so the test was tests/test_playwright_math_loading.py::test_missing_composite_uses_matching_stock_fonts_and_metrics[stylesheet]. The dump showed the Playwright sync greenlet waiting in its event loop and the fixture's ThreadingHTTPServer idle.

Mechanism, measured on the same host (10-core M1 Pro, macOS 26.5.2, load average 140-230) with a timing plugin outside the repository:
- Each case calls _page three times (lines 386-415), and each _page starts sync_playwright, launches Chromium and closes it. Builds, launch, goto, wait_for_function and evaluate together took under 2 s per case.
- browser.close() took 21.5-30.1 s in eight of the nine calls (2.3 s once). The three cases took 67.8, 78.8 and 86.7 s, with only about 1 s of CPU per browser session in all child processes.
- The same happens with no KPress page at all: launch, goto about:blank, close took 8.7-30.0 s to close, with Playwright's chromium_headless_shell-1223 and with the installed Google Chrome (channel chrome) alike.
- DEBUG=pw:browser with Chromium's --enable-logging --v=1: after '<gracefully close start>' Chromium logs its histograms within 12 ms and then nothing; exactly 30.00 s later Playwright logs '<kill> <will force kill>' and the process exits on SIGKILL. In other runs it exits by itself, exit code 0, after 9-25 s. The 30 s is Playwright 1.60.0's closeOrKill(DEFAULT_PLAYWRIGHT_TIMEOUT) (driver/package/lib/coreBundle.js, around line 38378).
- A 4 s macOS sample of the closing browser: every thread idle in mach_msg or kevent64 (main thread in its CFRunLoop), no I/O and no CPU, children already gone. Chromium is waiting for something, not working; what it waits for is not identified (the binary's symbols are stripped).
- On Linux CI the same tests are fast: the browser job of run 45088054034 (ubuntu-24.04) ran all 74 browser tests in 106 s.

Not established: whether the stall happens at a low load average; it was not below 140 during these measurements.

So the time is per browser, not per test: a test that opens N browsers costs up to N x 30 s here. Options, not chosen: open one browser per module (a module-scoped fixture that each _page takes a new context from), which pays the close once; or give the tests that open several browsers a measured timeout marker. Read-only investigation by a metabrowser agent; nothing in this checkout was changed.
