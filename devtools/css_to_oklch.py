#!/usr/bin/env python3
"""Convert CSS color literals (hex / rgb[a]() / hsl[a]()) to exact oklch().

Exactness contract: every emitted oklch() value, parsed back through the CSS
Color 4 reference math (Ottosson OKLab), must round-trip to the *identical*
8-bit sRGB channels as the original literal. Decimal precision is increased
per-color until the round-trip is byte-exact. Alpha is preserved verbatim.

Skips /* comments */ and url(...) spans. Keywords (white, transparent,
currentColor) and var()/color-mix() expressions are untouched.

Usage: python3 css_to_oklch.py file.css [file2.css ...]
       (rewrites in place; prints an original -> oklch report)
"""

from __future__ import annotations

import math
import re
import sys

# --- sRGB <-> OKLab reference math (Bjorn Ottosson, CSS Color 4) ---


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def _cbrt(v: float) -> float:
    return v ** (1 / 3) if v >= 0 else -((-v) ** (1 / 3))


def srgb8_to_oklch(r8: int, g8: int, b8: int) -> tuple[float, float, float]:
    r = srgb_to_linear(r8 / 255.0)
    g = srgb_to_linear(g8 / 255.0)
    b = srgb_to_linear(b8 / 255.0)
    lv = 0.41222147079999993 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034981999999 * r + 0.6806995450999999 * g + 0.1073969566 * b
    s = 0.08830246189999998 * r + 0.2817188376 * g + 0.6299787005000002 * b
    l_, m_, s_ = _cbrt(lv), _cbrt(m), _cbrt(s)
    L = 0.2104542553 * l_ + 0.793617785 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.428592205 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.808675766 * s_
    C = math.hypot(a, bb)
    H = math.degrees(math.atan2(bb, a)) % 360.0
    return L, C, H


def oklch_to_srgb8(L: float, C: float, H: float) -> tuple[int, int, int]:
    a = C * math.cos(math.radians(H))
    bb = C * math.sin(math.radians(H))
    l_ = L + 0.3963377774 * a + 0.2158037573 * bb
    m_ = L - 0.1055613458 * a - 0.0638541728 * bb
    s_ = L - 0.0894841775 * a - 1.291485548 * bb
    lv, m, s = l_**3, m_**3, s_**3
    r = 4.0767416621 * lv - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * lv + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * lv - 0.7034186147 * m + 1.707614701 * s
    out: list[int] = []
    for v in (r, g, b):
        v = linear_to_srgb(min(max(v, 0.0), 1.0))
        out.append(round(min(max(v, 0.0), 1.0) * 255))
    return out[0], out[1], out[2]


def fmt_alpha(alpha: float | None) -> str:
    if alpha is None or alpha >= 1.0:
        return ""
    s = f"{alpha:.4f}".rstrip("0").rstrip(".")
    return f" / {s}"


def to_oklch_exact(r8: int, g8: int, b8: int, alpha: float | None) -> str:
    """Emit oklch() with the fewest decimals that round-trips byte-exactly."""
    L, C, H = srgb8_to_oklch(r8, g8, b8)
    achromatic = C < 1e-7
    for lp in range(2, 8):  # decimals on L%
        for cp in range(4, 9):  # decimals on C
            for hp in range(1, 7):  # decimals on H
                Ls = f"{L * 100:.{lp}f}"
                Cs = "0" if achromatic else f"{C:.{cp}f}"
                Hs = "0" if achromatic else f"{H:.{hp}f}"
                cand = f"oklch({Ls}% {Cs} {Hs}{fmt_alpha(alpha)})"
                if oklch_to_srgb8(float(Ls) / 100, float(Cs), float(Hs)) == (r8, g8, b8):
                    return cand
                if achromatic:
                    break
            if achromatic:
                break
    raise SystemExit(f"no exact oklch for rgb({r8},{g8},{b8})")


# --- literal parsing ---

HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
FUNC_RE = re.compile(r"\b(rgba?|hsla?)\(([^()]*)\)")


def parse_hex(h: str) -> tuple[int, int, int, float | None] | None:
    if len(h) == 3:
        r, g, b = (int(c * 2, 16) for c in h)
        return r, g, b, None
    if len(h) == 6:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), None
    if len(h) == 8:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255.0
    return None  # length 4/5/7: malformed or #rgba shorthand we don't expect


def parse_component(tok: str, scale: float) -> float:
    tok = tok.strip()
    if tok.endswith("%"):
        return float(tok[:-1]) / 100.0 * scale
    return float(tok)


def parse_func(name: str, body: str) -> tuple[int, int, int, float | None] | None:
    body = body.replace("/", " ").replace(",", " ")
    toks = body.split()
    if len(toks) not in (3, 4):
        return None
    alpha: float | None = None
    if len(toks) == 4:
        a = toks[3]
        alpha = float(a[:-1]) / 100.0 if a.endswith("%") else float(a)
    if name.startswith("rgb"):
        vals: list[int] = []
        for t in toks[:3]:
            v = parse_component(t, 255.0)
            if not (0 <= v <= 255):
                return None
            vals.append(round(v))
        return vals[0], vals[1], vals[2], alpha
    # hsl
    h = float(toks[0].rstrip("deg")) % 360.0
    s = parse_component(toks[1], 1.0)
    li = parse_component(toks[2], 1.0)
    c = (1 - abs(2 * li - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = li - c / 2
    sector = [(c, x, 0.0), (x, c, 0.0), (0.0, c, x), (0.0, x, c), (x, 0.0, c), (c, 0.0, x)][
        int(h // 60) % 6
    ]
    return (
        round((sector[0] + m) * 255),
        round((sector[1] + m) * 255),
        round((sector[2] + m) * 255),
        alpha,
    )


def protected_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for m in re.finditer(r"/\*.*?\*/", text, flags=re.S):
        spans.append(m.span())
    for m in re.finditer(r"url\([^)]*\)", text):
        spans.append(m.span())
    return spans


def in_spans(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in spans)


def convert_file(path: str) -> list[tuple[str, str]]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    spans = protected_spans(text)
    report: list[tuple[str, str]] = []
    out: list[str] = []
    last = 0
    events: list[tuple[int, int, str]] = []

    for m in HEX_RE.finditer(text):
        if in_spans(m.start(), spans):
            continue
        parsed = parse_hex(m.group(1))
        if parsed:
            events.append((m.start(), m.end(), to_oklch_exact(*parsed)))
    for m in FUNC_RE.finditer(text):
        if in_spans(m.start(), spans):
            continue
        parsed = parse_func(m.group(1), m.group(2))
        if parsed:
            events.append((m.start(), m.end(), to_oklch_exact(*parsed)))

    for start, end, repl in sorted(events):
        out.append(text[last:start])
        report.append((text[start:end], repl))
        out.append(repl)
        last = end
    out.append(text[last:])
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(out))
    return report


def main() -> None:
    for path in sys.argv[1:]:
        report = convert_file(path)
        print(f"== {path}: {len(report)} conversions")
        for orig, new in report:
            print(f"   {orig:40s} -> {new}")


if __name__ == "__main__":
    main()
