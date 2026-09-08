"""Measure a resolved font's em advance independently of platform pixel hinting."""

# Linux Chromium can round a small glyph's advance to a whole CSS pixel: PT Serif's
# 0.533em digit becomes 9/16 = 0.5625em, and Source Sans's 0.497em becomes 8/16 =
# 0.5em. Measuring the same resolved face at 1024px bounds a pixel's error below
# 0.001em without widening the tests' distinction between those fonts. It also
# stays below Firefox's 2000-device-pixel cap in the 1x test context (Mozilla
# bug 1188579), which truncates a 4096px probe. The page's actual KaTeX layout
# stays untouched, so fraction heights, accents, and size ratios
# continue to test the real renderer at its normal size.
FONT_ADVANCE_INIT = """(() => {
  globalThis.__kpressFontAdvance = (element) => {
    const style = getComputedStyle(element);
    const probe = document.createElement('span');
    probe.textContent = element.textContent;
    Object.assign(probe.style, {
      position: 'fixed',
      visibility: 'hidden',
      display: 'inline-block',
      whiteSpace: 'pre',
      width: 'max-content',
      maxWidth: 'none',
      fontFamily: style.fontFamily,
      fontStyle: style.fontStyle,
      fontWeight: style.fontWeight,
      fontStretch: style.fontStretch,
      fontKerning: style.fontKerning,
      fontFeatureSettings: style.fontFeatureSettings,
      fontVariationSettings: style.fontVariationSettings,
      fontSize: '1024px',
    });
    document.body.append(probe);
    try {
      return probe.getBoundingClientRect().width / 1024;
    } finally {
      probe.remove();
    }
  };
})();"""
