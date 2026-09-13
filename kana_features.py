"""OpenType and outline helpers for Japanese kana extensions.

The source font already contains useful full-width kana outlines, including
the precomposed voiced forms.  This module keeps the extension work separate
from the source generator so that a build can add:

* U+3099/U+309A as real combining-mark glyphs;
* a ``ccmp`` lookup for canonical base + combining-mark sequences; and
* half-width katakana whose one-cell forms stay at a 500-unit advance.

Half-width voiced sequences need their own ligature glyphs.  Substituting to
the full-width target directly would make ``\uff76\uff9e`` look full-width in
shape.  The ligature outlines below are horizontally fitted copies of the
corresponding full-width precomposed glyphs while retaining the two half-width
advances of the source sequence.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Mapping, MutableMapping

from fontTools.pens.transformPen import TransformPen


COMBINING_VOICED = 0x3099
COMBINING_SEMIVOICED = 0x309A
COMBINING_MARKS = (COMBINING_VOICED, COMBINING_SEMIVOICED)
HALFWIDTH_VOICED = 0xFF9E
HALFWIDTH_SEMIVOICED = 0xFF9F
HALFWIDTH_ADVANCE = 500
HALFWIDTH_LIGATURE_ADVANCE = HALFWIDTH_ADVANCE * 2


# U+FF61..U+FF9D follow the JIS X 0201 half-width katakana order.  Keep this
# explicit instead of relying on a compatibility-normalization table: NFKC
# does not preserve the half-width glyph/metric policy needed by this font.
HALFWIDTH_TO_FULLWIDTH: dict[int, int] = {
    0xFF61: 0x3002,  # ｡ -> 。
    0xFF62: 0x300C,  # ｢ -> 「
    0xFF63: 0x300D,  # ｣ -> 」
    0xFF64: 0x3001,  # ､ -> 、
    0xFF65: 0x30FB,  # ･ -> ・
    0xFF66: 0x30F2,  # ｦ -> ヲ
    0xFF67: 0x30A1,  # ｧ -> ァ
    0xFF68: 0x30A3,  # ｨ -> ィ
    0xFF69: 0x30A5,  # ｩ -> ゥ
    0xFF6A: 0x30A7,  # ｪ -> ェ
    0xFF6B: 0x30A9,  # ｫ -> ォ
    0xFF6C: 0x30E3,  # ｬ -> ャ
    0xFF6D: 0x30E5,  # ｭ -> ュ
    0xFF6E: 0x30E7,  # ｮ -> ョ
    0xFF6F: 0x30C3,  # ｯ -> ッ
    0xFF70: 0x30FC,  # ｰ -> ー
    0xFF71: 0x30A2,  # ｱ -> ア
    0xFF72: 0x30A4,  # ｲ -> イ
    0xFF73: 0x30A6,  # ｳ -> ウ
    0xFF74: 0x30A8,  # ｴ -> エ
    0xFF75: 0x30AA,  # ｵ -> オ
    0xFF76: 0x30AB,  # ｶ -> カ
    0xFF77: 0x30AD,  # ｷ -> キ
    0xFF78: 0x30AF,  # ｸ -> ク
    0xFF79: 0x30B1,  # ｹ -> ケ
    0xFF7A: 0x30B3,  # ｺ -> コ
    0xFF7B: 0x30B5,  # ｻ -> サ
    0xFF7C: 0x30B7,  # ｼ -> シ
    0xFF7D: 0x30B9,  # ｽ -> ス
    0xFF7E: 0x30BB,  # ｾ -> セ
    0xFF7F: 0x30BD,  # ｿ -> ソ
    0xFF80: 0x30BF,  # ﾀ -> タ
    0xFF81: 0x30C1,  # ﾁ -> チ
    0xFF82: 0x30C4,  # ﾂ -> ツ
    0xFF83: 0x30C6,  # ﾃ -> テ
    0xFF84: 0x30C8,  # ﾄ -> ト
    0xFF85: 0x30CA,  # ﾅ -> ナ
    0xFF86: 0x30CB,  # ﾆ -> ニ
    0xFF87: 0x30CC,  # ﾇ -> ヌ
    0xFF88: 0x30CD,  # ﾈ -> ネ
    0xFF89: 0x30CE,  # ﾉ -> ノ
    0xFF8A: 0x30CF,  # ﾊ -> ハ
    0xFF8B: 0x30D2,  # ﾋ -> ヒ
    0xFF8C: 0x30D5,  # ﾌ -> フ
    0xFF8D: 0x30D8,  # ﾍ -> ヘ
    0xFF8E: 0x30DB,  # ﾎ -> ホ
    0xFF8F: 0x30DE,  # ﾏ -> マ
    0xFF90: 0x30DF,  # ﾐ -> ミ
    0xFF91: 0x30E0,  # ﾑ -> ム
    0xFF92: 0x30E1,  # ﾒ -> メ
    0xFF93: 0x30E2,  # ﾓ -> モ
    0xFF94: 0x30E4,  # ﾔ -> ヤ
    0xFF95: 0x30E6,  # ﾕ -> ユ
    0xFF96: 0x30E8,  # ﾖ -> ヨ
    0xFF97: 0x30E9,  # ﾗ -> ラ
    0xFF98: 0x30EA,  # ﾘ -> リ
    0xFF99: 0x30EB,  # ﾙ -> ル
    0xFF9A: 0x30EC,  # ﾚ -> レ
    0xFF9B: 0x30ED,  # ﾛ -> ロ
    0xFF9C: 0x30EF,  # ﾜ -> ワ
    0xFF9D: 0x30F3,  # ﾝ -> ン
}


# A half-width voiced sequence is represented by one of these full-width
# precomposed targets.  Unicode intentionally leaves half-width kana + mark
# sequences decomposed, so this table is explicit and easy to audit.
HALFWIDTH_COMPOSED: dict[tuple[int, int], int] = {
    (0xFF66, HALFWIDTH_VOICED): 0x30FA,  # ｦﾞ -> ヺ
    (0xFF73, HALFWIDTH_VOICED): 0x30F4,  # ｳﾞ -> ヴ
    (0xFF76, HALFWIDTH_VOICED): 0x30AC,  # ｶﾞ -> ガ
    (0xFF77, HALFWIDTH_VOICED): 0x30AE,  # ｷﾞ -> ギ
    (0xFF78, HALFWIDTH_VOICED): 0x30B0,  # ｸﾞ -> グ
    (0xFF79, HALFWIDTH_VOICED): 0x30B2,  # ｹﾞ -> ゲ
    (0xFF7A, HALFWIDTH_VOICED): 0x30B4,  # ｺﾞ -> ゴ
    (0xFF7B, HALFWIDTH_VOICED): 0x30B6,  # ｻﾞ -> ザ
    (0xFF7C, HALFWIDTH_VOICED): 0x30B8,  # ｼﾞ -> ジ
    (0xFF7D, HALFWIDTH_VOICED): 0x30BA,  # ｽﾞ -> ズ
    (0xFF7E, HALFWIDTH_VOICED): 0x30BC,  # ｾﾞ -> ゼ
    (0xFF7F, HALFWIDTH_VOICED): 0x30BE,  # ｿﾞ -> ゾ
    (0xFF80, HALFWIDTH_VOICED): 0x30C0,  # ﾀﾞ -> ダ
    (0xFF81, HALFWIDTH_VOICED): 0x30C2,  # ﾁﾞ -> ヂ
    (0xFF82, HALFWIDTH_VOICED): 0x30C5,  # ﾂﾞ -> ヅ
    (0xFF83, HALFWIDTH_VOICED): 0x30C7,  # ﾃﾞ -> デ
    (0xFF84, HALFWIDTH_VOICED): 0x30C9,  # ﾄﾞ -> ド
    (0xFF8A, HALFWIDTH_VOICED): 0x30D0,  # ﾊﾞ -> バ
    (0xFF8B, HALFWIDTH_VOICED): 0x30D3,  # ﾋﾞ -> ビ
    (0xFF8C, HALFWIDTH_VOICED): 0x30D6,  # ﾌﾞ -> ブ
    (0xFF8D, HALFWIDTH_VOICED): 0x30D9,  # ﾍﾞ -> ベ
    (0xFF8E, HALFWIDTH_VOICED): 0x30DC,  # ﾎﾞ -> ボ
    (0xFF9C, HALFWIDTH_VOICED): 0x30F7,  # ﾜﾞ -> ヷ
    (0xFF8A, HALFWIDTH_SEMIVOICED): 0x30D1,  # ﾊﾟ -> パ
    (0xFF8B, HALFWIDTH_SEMIVOICED): 0x30D4,  # ﾋﾟ -> ピ
    (0xFF8C, HALFWIDTH_SEMIVOICED): 0x30D7,  # ﾌﾟ -> プ
    (0xFF8D, HALFWIDTH_SEMIVOICED): 0x30DA,  # ﾍﾟ -> ペ
    (0xFF8E, HALFWIDTH_SEMIVOICED): 0x30DD,  # ﾎﾟ -> ポ
}


def glyph_name(codepoint: int) -> str:
    """Return the glyph naming convention used by ``build.py``."""

    return f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"


def halfwidth_ligature_name(base: int, mark: int) -> str:
    """Return a stable glyph name for a synthetic half-width ligature."""

    return f"hw{base:04X}{mark:04X}"


def halfwidth_ligature_map(glyph_names: Iterable[str] | None = None) -> dict[tuple[int, int], str]:
    """Return ``(half-width base, half-width mark) -> glyph name`` mappings.

    Pass the compiled glyph-name iterable when constructing features from an
    already-open UFO.  This filters out synthetic ligatures that were not
    installed in a partial fixture while keeping the normal full-build call
    concise.
    """

    result = {
        pair: halfwidth_ligature_name(*pair) for pair in HALFWIDTH_COMPOSED
    }
    if glyph_names is None:
        return result
    names = set(glyph_names)
    return {pair: name for pair, name in result.items() if name in names}


def combining_codepoints() -> tuple[int, int]:
    """Return the two combining marks that this font supports."""

    return COMBINING_MARKS


def canonical_compositions(
    codepoints: Iterable[int],
) -> tuple[tuple[int, int, int], ...]:
    """Find covered precomposed kana and their NFD base/mark pairs.

    The return values are ``(base, mark, composed)`` and are sorted by the
    composed codepoint.  Restricting the result to the supplied coverage keeps
    the generated feature file valid for partial fixtures as well as the full
    font.
    """

    covered = set(codepoints)
    return tuple(
        (base, mark, composed)
        for base, mark, composed in canonical_composition_candidates(covered)
        if composed in covered
    )


def canonical_composition_candidates(
    codepoints: Iterable[int],
) -> tuple[tuple[int, int, int], ...]:
    """Find all kana compositions whose base and mark are covered.

    Unlike :func:`canonical_compositions`, this also reports a missing target
    glyph.  It is used by strict feature generation to prevent a partial cmap
    from silently omitting a ``ccmp`` substitution.
    """

    covered = set(codepoints)
    result: list[tuple[int, int, int]] = []
    # All Unicode canonical kana + combining-mark pairs are in this block.
    for composed in range(0x3040, 0x3100):
        nfd = unicodedata.normalize("NFD", chr(composed))
        if len(nfd) != 2:
            continue
        base, mark = map(ord, nfd)
        if mark in COMBINING_MARKS and base in covered and mark in covered:
            result.append((base, mark, composed))
    return tuple(result)


def missing_canonical_glyphs(codepoints: Iterable[int]) -> tuple[int, ...]:
    """List combining marks missing from a codepoint coverage set."""

    covered = set(codepoints)
    return tuple(cp for cp in COMBINING_MARKS if cp not in covered)


def _halfwidth_transform(font, source_name: str, advance: int, sidebearing: int):
    """Fit a source glyph horizontally into a half-width cell.

    Half-width kana keep the full vertical scale.  We compress only x and
    center the actual outline, which also handles source overhangs cleanly.
    """

    source = font[source_name]
    bounds = source.getBounds(font)
    if not bounds or bounds[2] <= bounds[0]:
        return (0.5, 0, 0, 1, advance / 4, 0)
    x0, _y0, x1, _y1 = bounds
    sx = min(0.5, (advance - 2 * sidebearing) / (x1 - x0))
    tx = (advance - (x1 - x0) * sx) / 2 - x0 * sx
    return (sx, 0, 0, 1, tx, 0)


def add_halfwidth_glyphs(
    font,
    glyph_order: list[str],
    modifications: MutableMapping[str, list[str]],
    *,
    advance: int = HALFWIDTH_ADVANCE,
    sidebearing: int = 20,
) -> dict[tuple[int, int], str]:
    """Install half-width kana and return synthetic ligature names.

    ``font`` is a ``ufoLib2.Font``.  The caller should invoke this after the
    ordinary source glyph loop and before assigning ``font.glyphOrder``.  All
    half-width base glyphs are mapped to their full-width counterparts and
    compressed in x only.  The U+FF9E/U+FF9F marks remain usable as standalone
    half-width glyphs; in a text run they are consumed by the generated
    ``ccmp`` ligatures.  A voiced ligature has a 1000-unit advance (two
    500-unit source characters), so shaping does not silently change the text
    width.

    The function intentionally raises ``KeyError`` when a requested
    full-width source or U+3099/U+309A mark is absent.  A silent empty glyph
    would make the coverage look complete while producing a broken font.
    """

    cmap = {u: g.name for g in font for u in g.unicodes}
    for cp in COMBINING_MARKS:
        if cp not in cmap:
            raise KeyError(f"combining source glyph U+{cp:04X} is missing")

    def ensure_target(cp: int):
        name = glyph_name(cp)
        target = font[name] if name in font else font.newGlyph(name)
        if name not in glyph_order:
            glyph_order.append(name)
        target.clearContours()
        target.unicodes = [cp]
        return target

    for halfwidth, fullwidth in sorted(HALFWIDTH_TO_FULLWIDTH.items()):
        if fullwidth not in cmap:
            raise KeyError(
                f"full-width source glyph U+{fullwidth:04X} for U+{halfwidth:04X} is missing"
            )
        source_name = cmap[fullwidth]
        target = ensure_target(halfwidth)
        target.width = advance
        target.lib["com.example.nikukyu.source"] = source_name
        target.lib["com.example.nikukyu.scale"] = "x-compressed"
        source = font[source_name]
        source.draw(
            TransformPen(
                target.getPen(),
                _halfwidth_transform(font, source_name, advance, sidebearing),
            )
        )
        modifications[chr(halfwidth)] = ["halfwidth-derived", chr(fullwidth)]

    # The half-width compatibility marks are separate glyphs with a normal
    # half-width advance.  Their outline is copied from the real combining
    # source, so standalone ``ﾞ``/``ﾟ`` still render even when a shaping engine
    # has ccmp disabled.
    for halfwidth, combining in [
        (HALFWIDTH_VOICED, COMBINING_VOICED),
        (HALFWIDTH_SEMIVOICED, COMBINING_SEMIVOICED),
    ]:
        target = ensure_target(halfwidth)
        target.width = advance
        source_name = cmap[combining]
        target.lib["com.example.nikukyu.source"] = source_name
        target.lib["com.example.nikukyu.scale"] = "x-compressed"
        font[source_name].draw(
            TransformPen(
                target.getPen(),
                _halfwidth_transform(font, source_name, advance, sidebearing),
            )
        )
        modifications[chr(halfwidth)] = ["halfwidth-mark-derived", chr(combining)]

    ligatures: dict[tuple[int, int], str] = {}
    for (base, mark), fullwidth_composed in sorted(HALFWIDTH_COMPOSED.items()):
        if fullwidth_composed not in cmap:
            raise KeyError(
                f"precomposed source glyph U+{fullwidth_composed:04X} for "
                f"U+{base:04X}+U+{mark:04X} is missing"
            )
        name = halfwidth_ligature_name(base, mark)
        target = font[name] if name in font else font.newGlyph(name)
        target.clearContours()
        target.unicodes = []
        target.width = HALFWIDTH_LIGATURE_ADVANCE
        source_name = cmap[fullwidth_composed]
        target.lib["com.example.nikukyu.source"] = source_name
        target.lib["com.example.nikukyu.sequence"] = f"U+{base:04X} U+{mark:04X}"
        font[source_name].draw(
            TransformPen(
                target.getPen(),
                _halfwidth_transform(font, source_name, HALFWIDTH_LIGATURE_ADVANCE, sidebearing),
            )
        )
        if name not in glyph_order:
            glyph_order.append(name)
        ligatures[(base, mark)] = name
        modifications[f"{chr(base)}{chr(mark)}"] = [
            "halfwidth-voiced-ligature",
            chr(fullwidth_composed),
        ]
    return ligatures


def ccmp_feature_text(
    cmap: Mapping[int, str],
    *,
    halfwidth_ligatures: Mapping[tuple[int, int], str] | None = None,
    strict: bool = False,
) -> str:
    """Build a compact ``ccmp`` feature for canonical and half-width kana.

    ``cmap`` maps Unicode codepoints to glyph names (as returned by
    ``TTFont.getBestCmap`` or the small map in ``add_halfwidth_glyphs``).
    ``halfwidth_ligatures`` is the return value of
    :func:`add_halfwidth_glyphs`.  If ``strict`` is true, missing combining
    inputs or targets raise ``ValueError`` instead of being silently skipped.
    """

    lines = ["feature ccmp {"]
    canonical_missing: list[tuple[int, int, int]] = []
    for base, mark, composed in canonical_composition_candidates(cmap):
        names = (cmap.get(base), cmap.get(mark), cmap.get(composed))
        if any(name is None for name in names):
            canonical_missing.append((base, mark, composed))
            continue
        lines.append(f"    sub {names[0]} {names[1]} by {names[2]};")

    if halfwidth_ligatures:
        for (base, mark), target in sorted(halfwidth_ligatures.items()):
            source_base = cmap.get(base)
            source_mark = cmap.get(mark)
            if source_base is None or source_mark is None:
                canonical_missing.append((base, mark, 0))
                continue
            lines.append(f"    sub {source_base} {source_mark} by {target};")

    if strict and canonical_missing:
        details = ", ".join(
            f"U+{a:04X}+U+{b:04X}->U+{c:04X}" for a, b, c in canonical_missing
        )
        raise ValueError(f"missing ccmp glyphs: {details}")
    lines.append("} ccmp;")
    return "\n".join(lines)


def ccmp_pairs(cmap: Mapping[int, str], *, halfwidth_ligatures=None):
    """Return source/target glyph-name triples for inspection and tests."""

    result = []
    for base, mark, composed in canonical_compositions(cmap):
        if base in cmap and mark in cmap and composed in cmap:
            result.append((cmap[base], cmap[mark], cmap[composed]))
    if halfwidth_ligatures:
        for (base, mark), target in sorted(halfwidth_ligatures.items()):
            if base in cmap and mark in cmap:
                result.append((cmap[base], cmap[mark], target))
    return tuple(result)


__all__ = [
    "COMBINING_MARKS",
    "COMBINING_SEMIVOICED",
    "COMBINING_VOICED",
    "HALFWIDTH_ADVANCE",
    "HALFWIDTH_COMPOSED",
    "HALFWIDTH_LIGATURE_ADVANCE",
    "HALFWIDTH_SEMIVOICED",
    "HALFWIDTH_TO_FULLWIDTH",
    "HALFWIDTH_VOICED",
    "add_halfwidth_glyphs",
    "canonical_composition_candidates",
    "canonical_compositions",
    "ccmp_feature_text",
    "ccmp_pairs",
    "combining_codepoints",
    "glyph_name",
    "halfwidth_ligature_name",
    "halfwidth_ligature_map",
    "missing_canonical_glyphs",
]
