"""Supplemental glyphs for the Japanese display repertoire.

The main master is Mochiy Pop One.  This module deliberately keeps the
fallback font out of the main build policy: callers decide which characters
are requested and whether an outline should be rounded.  The public helpers
make that decision reproducible and make it possible to add glyphs to an
existing UFO without regenerating the 6,355 kanji.

Source priority for a missing character is:

1. an already processed glyph in the destination UFO (for aliases);
2. the original Mochiy font (for aliases that have no UFO master yet);
3. Zen Maru Gothic Black for a genuinely missing outline.

``outline_for`` returns an unrounded outline.  Pass it through the same
``soften`` function used by ``build.py`` when adding a Zen outline inside the
main generation loop.  ``add_missing_glyphs`` accepts that function as the
``rounder`` argument for the in-place UFO workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, MutableMapping

import pathops
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from coverage import SYMBOLS


ROOT = Path(__file__).resolve().parent
SUPPLEMENTAL_FONT_PATH = ROOT / "vendor" / "ZenMaruGothic-Black.ttf"

# These URLs are pinned to the commit used to obtain the vendored files.  Do
# not silently replace the binary from a moving ``main`` URL: the hash and
# source record are part of the reproducible build input.
SUPPLEMENTAL_REPOSITORY = "https://github.com/googlefonts/zen-marugothic"
SUPPLEMENTAL_COMMIT = "553c872b216d1290e2902a466edcdc9682f0df6a"
SUPPLEMENTAL_FONT_URL = (
    f"{SUPPLEMENTAL_REPOSITORY}/raw/{SUPPLEMENTAL_COMMIT}/"
    "fonts/ttf/ZenMaruGothic-Black.ttf"
)
SUPPLEMENTAL_LICENSE_URL = (
    f"{SUPPLEMENTAL_REPOSITORY}/raw/{SUPPLEMENTAL_COMMIT}/OFL.txt"
)
SUPPLEMENTAL_COPYRIGHT = (
    "Copyright 2021 The Zen Maru Gothic Project Authors "
    "(https://github.com/googlefonts/zen-marugothic)"
)

# Unicode normalization maps most halfwidth katakana to one fullwidth code
# point.  Keep the punctuation and voiced marks explicit because U+FF9E and
# U+FF9F normalize to combining marks, while the source font contains spacing
# marks.  The first five entries are useful even when the caller requests only
# the JIS non-kanji set; they are part of the CP932 practical repertoire.
HALFWIDTH_TO_FULLWIDTH: Mapping[int, int] = {
    0xFF61: 0x3002,  # ｡ 。
    0xFF62: 0x300C,  # ｢ 「
    0xFF63: 0x300D,  # ｣ 」
    0xFF64: 0x3001,  # ､ 、
    0xFF65: 0x30FB,  # ･ ・
    0xFF66: 0x30F2,  # ｦ ヲ
    0xFF67: 0x30A1,  # ｧ ァ
    0xFF68: 0x30A3,  # ｨ ィ
    0xFF69: 0x30A5,  # ｩ ゥ
    0xFF6A: 0x30A7,  # ｪ ェ
    0xFF6B: 0x30A9,  # ｫ ォ
    0xFF6C: 0x30E3,  # ｬ ャ
    0xFF6D: 0x30E5,  # ｭ ュ
    0xFF6E: 0x30E7,  # ｮ ョ
    0xFF6F: 0x30C3,  # ｯ ッ
    0xFF70: 0x30FC,  # ｰ ー
    0xFF71: 0x30A2,  # ｱ ア
    0xFF72: 0x30A4,  # ｲ イ
    0xFF73: 0x30A6,  # ｳ ウ
    0xFF74: 0x30A8,  # ｴ エ
    0xFF75: 0x30AA,  # ｵ オ
    0xFF76: 0x30AB,  # ｶ カ
    0xFF77: 0x30AD,  # ｷ キ
    0xFF78: 0x30AF,  # ｸ ク
    0xFF79: 0x30B1,  # ｹ ケ
    0xFF7A: 0x30B3,  # ｺ コ
    0xFF7B: 0x30B5,  # ｻ サ
    0xFF7C: 0x30B7,  # ｼ シ
    0xFF7D: 0x30B9,  # ｽ ス
    0xFF7E: 0x30BB,  # ｾ セ
    0xFF7F: 0x30BD,  # ｿ ソ
    0xFF80: 0x30BF,  # ﾀ タ
    0xFF81: 0x30C1,  # ﾁ チ
    0xFF82: 0x30C4,  # ﾂ ツ
    0xFF83: 0x30C6,  # ﾃ テ
    0xFF84: 0x30C8,  # ﾄ ト
    0xFF85: 0x30CA,  # ﾅ ナ
    0xFF86: 0x30CB,  # ﾆ ニ
    0xFF87: 0x30CC,  # ﾇ ヌ
    0xFF88: 0x30CD,  # ﾈ ネ
    0xFF89: 0x30CE,  # ﾉ ノ
    0xFF8A: 0x30CF,  # ﾊ ハ
    0xFF8B: 0x30D2,  # ﾋ ヒ
    0xFF8C: 0x30D5,  # ﾌ フ
    0xFF8D: 0x30D8,  # ﾍ ヘ
    0xFF8E: 0x30DB,  # ﾎ ホ
    0xFF8F: 0x30DE,  # ﾏ マ
    0xFF90: 0x30DF,  # ﾐ ミ
    0xFF91: 0x30E0,  # ﾑ ム
    0xFF92: 0x30E1,  # ﾒ メ
    0xFF93: 0x30E2,  # ﾓ モ
    0xFF94: 0x30E4,  # ﾔ ヤ
    0xFF95: 0x30E6,  # ﾕ ユ
    0xFF96: 0x30E8,  # ﾖ ヨ
    0xFF97: 0x30E9,  # ﾗ ラ
    0xFF98: 0x30EA,  # ﾘ リ
    0xFF99: 0x30EB,  # ﾙ ル
    0xFF9A: 0x30EC,  # ﾚ レ
    0xFF9B: 0x30ED,  # ﾛ ロ
    0xFF9C: 0x30EF,  # ﾜ ワ
    0xFF9D: 0x30F3,  # ﾝ ン
    0xFF9E: 0x309B,  # ﾞ ゛ (spacing mark)
    0xFF9F: 0x309C,  # ﾟ ゜ (spacing mark)
}

# Fullwidth forms outside FF01..FF5E have no simple arithmetic relation to
# ASCII, but the matching source glyph is present in Mochiy Pop One.
EXPLICIT_BASE_ALIASES: Mapping[int, int] = {
    0xFFE0: 0x00A2,  # ￠ from ¢
    0xFFE1: 0x00A3,  # ￡ from £
    0xFFE2: 0x00AC,  # ￢ from ¬
    0xFFE3: 0x00AF,  # ￣ from ¯
    0xFFE4: 0x00A6,  # ￤ from ¦
    0xFFE5: 0x00A5,  # ￥ from ¥
    0x212B: 0x00C5,  # Å from Å
}

# Common Japanese business and era marks are not all represented by the
# strict JIS X 0208 symbol set.  Keeping these here lets callers use the
# helper with the practical CP932-plus repertoire used by coverage.py.
COMMON_JAPANESE_EXTRAS = frozenset("㈱㈲㈹№℡㍻㍼㍽㍾㍿㋿")


@dataclass(frozen=True)
class SupplementalOutline:
    """An unrounded outline and its provenance.

    ``operation`` is one of ``direct``, ``fullwidth``, ``halfwidth``, or
    ``base-alias``.  The operation tells a caller how to set the advance width
    while retaining the source's visual weight.  ``source_codepoint`` is
    ``None`` only for a future custom outline; all currently shipped glyphs
    have a concrete source glyph.
    """

    path: pathops.Path
    width: int
    source: str
    source_codepoint: int | None
    operation: str


@dataclass(frozen=True)
class SupplementReport:
    """Result of adding missing outlines to a UFO."""

    added: tuple[str, ...]
    skipped: tuple[str, ...]
    unresolved: tuple[str, ...]
    sources: Mapping[str, str]


def cp932_characters() -> frozenset[str]:
    """Return the valid characters represented by Windows CP932.

    CP932's double-byte extension is enumerated from the codec itself rather
    than from a copied table, keeping this helper independent of the host's
    locale and Python's codec implementation.
    """

    # CP932 has ASCII as its single-byte repertoire.  Latin-1 code points are
    # not a CP932 single-byte range; adding them here would overstate the
    # Japanese target and leave unrelated symbols looking like requirements.
    chars = {chr(cp) for cp in range(0x20, 0x7F)}
    for lead in (*range(0x81, 0xA0), *range(0xE0, 0xF0)):
        for trail in (*range(0x40, 0x7F), *range(0x80, 0xFD)):
            try:
                chars.add(bytes((lead, trail)).decode("cp932"))
            except UnicodeDecodeError:
                pass
    chars.update(chr(cp) for cp in range(0xFF61, 0xFFA0))
    return frozenset(chars)


def default_characters() -> frozenset[str]:
    """Return the practical supplement target set.

    The set intentionally includes existing characters.  Callers can pass it
    directly to ``missing_characters`` or ``add_missing_glyphs``; existing UFO
    glyphs are skipped and therefore never replaced by the fallback.
    """

    return frozenset(SYMBOLS) | cp932_characters() | COMMON_JAPANESE_EXTRAS | {"𠮟"}


def _as_codepoints(existing: Iterable[int | str]) -> set[int]:
    result: set[int] = set()
    for item in existing:
        result.add(item if isinstance(item, int) else ord(item))
    return result


def missing_characters(
    existing: Iterable[int | str],
    requested: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Return requested code points absent from ``existing``, sorted by code."""

    present = _as_codepoints(existing)
    target = default_characters() if requested is None else frozenset(requested)
    return tuple(sorted((ch for ch in target if ord(ch) not in present), key=ord))


def open_supplemental_font(path: str | Path = SUPPLEMENTAL_FONT_PATH) -> TTFont:
    """Open the pinned Zen Maru Gothic fallback font."""

    return TTFont(str(path), recalcBBoxes=False, recalcTimestamp=False)


def _glyph_name(codepoint: int) -> str:
    return f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"


def _draw_tt_glyph(font: TTFont, codepoint: int) -> tuple[pathops.Path, int]:
    cmap = font.getBestCmap()
    glyph_name = cmap.get(codepoint)
    if glyph_name is None:
        raise KeyError(f"U+{codepoint:04X} is not in {font.reader.file.name}")
    glyph_set = font.getGlyphSet()
    path = pathops.Path()
    recording = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(recording)
    recording.replay(path.getPen())
    return path, int(round(glyph_set[glyph_name].width))


def _draw_ufo_glyph(ufo, codepoint: int) -> tuple[pathops.Path, int]:
    name = _glyph_name(codepoint)
    if name not in ufo:
        raise KeyError(f"U+{codepoint:04X} is not in the destination UFO")
    glyph = ufo[name]
    path = pathops.Path()
    glyph.draw(path.getPen())
    return path, int(round(glyph.width))


def _fullwidth_alias(codepoint: int) -> int | None:
    if 0xFF01 <= codepoint <= 0xFF5E:
        return codepoint - 0xFEE0
    return EXPLICIT_BASE_ALIASES.get(codepoint)


def _halfwidth_alias(codepoint: int) -> int | None:
    return HALFWIDTH_TO_FULLWIDTH.get(codepoint)


def _candidate_source(
    codepoint: int,
    *,
    base_cmap: Mapping[int, str] | None,
    supplemental_cmap: Mapping[int, str],
) -> tuple[int, str, str] | None:
    """Return ``(source codepoint, source kind, operation)``."""

    fullwidth = _fullwidth_alias(codepoint)
    if fullwidth is not None and (base_cmap is None or fullwidth in base_cmap):
        return fullwidth, "alias", "fullwidth" if codepoint >= 0xFF00 else "base-alias"

    halfwidth = _halfwidth_alias(codepoint)
    if halfwidth is not None and (base_cmap is None or halfwidth in base_cmap):
        return halfwidth, "alias", "halfwidth"

    if codepoint in supplemental_cmap:
        return codepoint, "Zen Maru Gothic Black", "direct"

    return None


def _centered_transform(width: int, target_width: int, max_ink: int) -> tuple[float, float, float, float, float, float]:
    scale = min(1.0, max_ink / max(width, 1))
    return (scale, 0.0, 0.0, 1.0, (target_width - width * scale) / 2.0, 0.0)


def _apply_operation(path: pathops.Path, width: int, operation: str) -> tuple[pathops.Path, int]:
    if operation == "fullwidth":
        path = path.transform(*_centered_transform(width, 1000, 900))
        return path, 1000
    if operation == "halfwidth":
        path = path.transform(*_centered_transform(width, 500, 450))
        return path, 500
    return path, width


def _draw_available(
    codepoint: int,
    *,
    ufo,
    base_font: TTFont | None,
    supplemental_font: TTFont,
) -> tuple[pathops.Path, int, str] | None:
    """Draw one source glyph, preferring the processed destination master."""

    if ufo is not None:
        try:
            path, width = _draw_ufo_glyph(ufo, codepoint)
            return path, width, "destination UFO"
        except KeyError:
            pass
    if base_font is not None and codepoint in base_font.getBestCmap():
        path, width = _draw_tt_glyph(base_font, codepoint)
        return path, width, "Mochiy Pop One"
    if codepoint in supplemental_font.getBestCmap():
        path, width = _draw_tt_glyph(supplemental_font, codepoint)
        return path, width, "Zen Maru Gothic Black"
    return None


def _parallel_outline(
    *,
    ufo,
    base_font: TTFont | None,
    supplemental_font: TTFont,
) -> SupplementalOutline | None:
    """Build U+2225 from two rounded vertical bars.

    Zen Maru Gothic 1.001 does not contain U+2225.  Two copies of the existing
    bar are more faithful than using the single-bar approximation that older
    fallback code used.
    """

    source = _draw_available(
        0x007C,
        ufo=ufo,
        base_font=base_font,
        supplemental_font=supplemental_font,
    )
    if source is None:
        return None
    bar, _width, source_kind = source
    bounds = bar.bounds
    if bounds is None:
        return None
    center = (bounds[0] + bounds[2]) / 2.0
    left = bar.transform(1, 0, 0, 1, 360 - center, 0)
    right = bar.transform(1, 0, 0, 1, 640 - center, 0)
    return SupplementalOutline(
        pathops.op(left, right, pathops.PathOp.UNION),
        1000,
        source_kind,
        0x007C,
        "direct",
    )


def _sigma_outline(
    *,
    ufo,
    base_font: TTFont | None,
    supplemental_font: TTFont,
) -> SupplementalOutline | None:
    """Use the rounded Greek capital sigma as the CP932 summation mark.

    U+2211 is not present in the pinned Zen Maru release.  Its Greek sigma
    master has the same silhouette and is scaled into a fullwidth cell.  The
    provenance remains explicit in ``source_codepoint`` and the modification
    ledger rather than pretending that an unrelated glyph was found.
    """

    source = _draw_available(
        0x03A3,
        ufo=ufo,
        base_font=base_font,
        supplemental_font=supplemental_font,
    )
    if source is None:
        return None
    path, width, source_kind = source
    path, _ = _apply_operation(path, width, "fullwidth")
    return SupplementalOutline(path, 1000, source_kind, 0x03A3, "direct")


def _rounded_frame(x0: float, y0: float, x1: float, y1: float, radius: float, width: float) -> pathops.Path:
    """Return a rounded rectangular outline used by the Reiwa mark."""

    k = 0.55228474983
    p = pathops.Path()
    p.moveTo(x0 + radius, y0)
    p.lineTo(x1 - radius, y0)
    p.cubicTo(x1 - radius + k * radius, y0, x1, y0 + radius - k * radius, x1, y0 + radius)
    p.lineTo(x1, y1 - radius)
    p.cubicTo(x1, y1 - radius + k * radius, x1 - radius + k * radius, y1, x1 - radius, y1)
    p.lineTo(x0 + radius, y1)
    p.cubicTo(x0 + radius - k * radius, y1, x0, y1 - radius + k * radius, x0, y1 - radius)
    p.lineTo(x0, y0 + radius)
    p.cubicTo(x0, y0 + radius - k * radius, x0 + radius - k * radius, y0, x0 + radius, y0)
    p.close()
    stroked = pathops.Path(p)
    stroked.stroke(width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    return stroked


def _fit_path(
    path: pathops.Path,
    box: tuple[float, float, float, float],
) -> pathops.Path:
    bounds = path.bounds
    if bounds is None:
        return pathops.Path()
    x0, y0, x1, y1 = bounds
    bx0, by0, bx1, by1 = box
    scale = min((bx1 - bx0) / max(x1 - x0, 1), (by1 - by0) / max(y1 - y0, 1))
    tx = (bx0 + bx1 - (x0 + x1) * scale) / 2
    ty = (by0 + by1 - (y0 + y1) * scale) / 2
    return path.transform(scale, 0, 0, scale, tx, ty)


def _reiwa_outline(
    *,
    ufo,
    base_font: TTFont | None,
    supplemental_font: TTFont,
) -> SupplementalOutline | None:
    """Construct U+32FF (SQUARE ERA NAME REIWA) from the two kanji.

    The pinned fallback predates the Reiwa code point.  The mark is therefore
    drawn from its constituent ``令`` and ``和`` masters inside a rounded
    square, which keeps the meaning visible at display sizes and avoids
    substituting the unrelated Heisei mark U+337B.
    """

    rei = _draw_available(0x4EE4, ufo=ufo, base_font=base_font, supplemental_font=supplemental_font)
    wa = _draw_available(0x548C, ufo=ufo, base_font=base_font, supplemental_font=supplemental_font)
    if rei is None or wa is None:
        return None
    rei_path = _fit_path(rei[0], (200, 280, 490, 720))
    wa_path = _fit_path(wa[0], (510, 280, 800, 720))
    frame = _rounded_frame(100, 170, 900, 830, 54, 56)
    body = pathops.op(frame, rei_path, pathops.PathOp.UNION)
    body = pathops.op(body, wa_path, pathops.PathOp.UNION)
    source_kind = "destination UFO" if rei[2] == wa[2] == "destination UFO" else "Zen Maru Gothic Black"
    return SupplementalOutline(body, 1000, source_kind + " (composed 令和)", None, "direct")


def _inequality_outline(
    codepoint: int,
    *,
    ufo,
    base_font: TTFont | None,
    supplemental_font: TTFont,
) -> SupplementalOutline | None:
    """Compose U+2264/U+2265 from the matching ASCII relation and ``_``.

    Neither the Mochiy nor the pinned Zen source has the precomposed
    less-than-or-equal marks.  Reusing the processed ``<``/``>`` keeps the
    diagonal weight in the same family, while a single underscore supplies
    the lower rule.  Each component is fitted independently to a fullwidth
    cell so the result is stable whether it is built from a destination UFO,
    the original Mochiy TTF, or the Zen fallback.
    """

    relation_cp = 0x003C if codepoint == 0x2264 else 0x003E
    relation = _draw_available(
        relation_cp,
        ufo=ufo,
        base_font=base_font,
        supplemental_font=supplemental_font,
    )
    rule = _draw_available(
        0x005F,
        ufo=ufo,
        base_font=base_font,
        supplemental_font=supplemental_font,
    )
    if relation is None or rule is None:
        return None

    # The relation sits high and the rule sits below it, with a small clear
    # gap that survives the optional rounder used by build.py.
    relation_path = _fit_path(relation[0], (165, 400, 835, 820))
    rule_path = _fit_path(rule[0], (165, 185, 835, 295))
    body = pathops.op(relation_path, rule_path, pathops.PathOp.UNION)
    source_kind = (
        "destination UFO"
        if relation[2] == rule[2] == "destination UFO"
        else relation[2] if relation[2] == rule[2] else "Mochiy Pop One"
    )
    return SupplementalOutline(
        body,
        1000,
        source_kind + " (composed relation + underscore)",
        relation_cp,
        # The components have already been fitted to the fullwidth cell.  A
        # second CJK optical transform in add_missing_glyphs would make this
        # comparison mark needlessly narrow.
        "fullwidth",
    )


def outline_for(
    char: str,
    *,
    ufo=None,
    base_font: TTFont | None = None,
    supplemental_font: TTFont | None = None,
) -> SupplementalOutline | None:
    """Resolve one missing character to an unrounded source outline.

    ``ufo`` should be the current editable font when available.  For a
    fullwidth or halfwidth alias, the already rounded destination master is
    used first, preserving the Mochiy-derived visual language.  If no UFO is
    supplied, ``base_font`` can provide the same source outline.  A direct
    Zen outline is used only when neither alias is available.

    The returned path is already width-normalized for fullwidth and halfwidth
    operations.  Direct fallback glyphs retain their source advance and should
    receive the caller's normal CJK transform and rounder.
    """

    if len(char) != 1:
        raise ValueError("outline_for expects one Unicode character")
    codepoint = ord(char)
    supplemental_font = supplemental_font or open_supplemental_font()
    supplemental_cmap = supplemental_font.getBestCmap()
    base_cmap = base_font.getBestCmap() if base_font is not None else None

    # Four practical CP932 marks need a small construction because the pinned
    # fallback lacks them as individual code points.
    if codepoint == 0x2225:
        return _parallel_outline(
            ufo=ufo,
            base_font=base_font,
            supplemental_font=supplemental_font,
        )
    if codepoint == 0x2211:
        return _sigma_outline(
            ufo=ufo,
            base_font=base_font,
            supplemental_font=supplemental_font,
        )
    if codepoint == 0x32FF:
        return _reiwa_outline(
            ufo=ufo,
            base_font=base_font,
            supplemental_font=supplemental_font,
        )
    if codepoint in (0x2264, 0x2265):
        return _inequality_outline(
            codepoint,
            ufo=ufo,
            base_font=base_font,
            supplemental_font=supplemental_font,
        )
    candidate = _candidate_source(
        codepoint,
        base_cmap=base_cmap,
        supplemental_cmap=supplemental_cmap,
    )
    if candidate is None:
        return None
    source_cp, source_kind, operation = candidate

    # Prefer the processed source in the destination UFO for an alias.  A
    # direct fallback never exists there at this point, so it naturally falls
    # through.
    if source_kind == "alias" and ufo is not None:
        try:
            path, width = _draw_ufo_glyph(ufo, source_cp)
            path, width = _apply_operation(path, width, operation)
            return SupplementalOutline(path, width, "destination UFO", source_cp, operation)
        except KeyError:
            pass

    if source_kind == "alias" and base_font is not None:
        try:
            path, width = _draw_tt_glyph(base_font, source_cp)
            path, width = _apply_operation(path, width, operation)
            return SupplementalOutline(path, width, "Mochiy Pop One", source_cp, operation)
        except KeyError:
            pass

    try:
        path, width = _draw_tt_glyph(supplemental_font, source_cp)
    except KeyError:
        return None
    path, width = _apply_operation(path, width, operation)
    source_label = "Zen Maru Gothic Black" if source_kind == "alias" else source_kind
    return SupplementalOutline(path, width, source_label, source_cp, operation)


def _copy_to_ufo(glyph, path: pathops.Path, width: int) -> None:
    glyph.clearContours()
    path.draw(glyph.getPen())
    glyph.width = int(round(width))


def add_missing_glyphs(
    ufo,
    *,
    base_font: TTFont | None = None,
    supplemental_font: TTFont | None = None,
    characters: Iterable[str] | None = None,
    rounder: Callable[[pathops.Path, float, float], pathops.Path] | None = None,
    rounding_radius: float = 72,
    weight_expansion: float = 20,
    direct_transform: tuple[float, float, float, float, float, float] | None = None,
    modifications: MutableMapping[str, list] | None = None,
) -> SupplementReport:
    """Add missing supplemental outlines to an existing UFO in place.

    This is the fast integration point for the expanded build.  It leaves all
    existing glyphs untouched, so it can run after the current UFO has been
    generated without repeating the expensive kanji outline pass.

    ``rounder`` is intentionally injectable: pass ``build.soften`` from the
    main build so fallback glyphs use precisely the same path operation.  If
    omitted, outlines are copied as supplied by the source.  ``direct_transform``
    can be set to ``(.90, 0, 0, .92, 50, 0)`` to mirror build.py's CJK optical
    transform for direct Zen glyphs; aliases are already normalized by
    ``outline_for`` and are not transformed a second time.  Direct Latin-1
    additions receive proportional sidebearings automatically.  Box-drawing
    code points retain their edge-to-edge 1em source outline so repeated rules
    connect without seams.
    """

    supplemental_font = supplemental_font or open_supplemental_font()
    base_cmap = base_font.getBestCmap() if base_font is not None else None
    target = default_characters() if characters is None else frozenset(characters)
    existing = {u for glyph in ufo for u in glyph.unicodes}
    pending = tuple(sorted((ch for ch in target if ord(ch) not in existing), key=ord))
    added: list[str] = []
    skipped: list[str] = []
    unresolved: list[str] = []
    sources: dict[str, str] = {}

    for char in pending:
        outline = outline_for(
            char,
            ufo=ufo,
            base_font=base_font,
            supplemental_font=supplemental_font,
        )
        if outline is None:
            unresolved.append(char)
            continue
        path = outline.path
        width = outline.width
        codepoint = ord(char)
        is_box_drawing = 0x2500 <= codepoint <= 0x257F
        if (
            codepoint >= 0x100
            and not is_box_drawing
            and outline.operation not in ("fullwidth", "halfwidth", "base-alias")
            and direct_transform is not None
        ):
            path = path.transform(*direct_transform)
        is_external_source = not outline.source.startswith("destination UFO")
        # Box drawing glyphs use edge-to-edge advances by design.  Applying
        # the optical inset or rounding them would introduce visible seams
        # when ``────`` or ``┼┼┼`` is repeated, so retain the pinned source
        # outline and 1em advance verbatim.
        if rounder is not None and is_external_source and not is_box_drawing:
            for attempt in range(6):
                try:
                    path = rounder(
                        path,
                        rounding_radius * (0.7**attempt),
                        weight_expansion * (0.7**attempt),
                    )
                    break
                except pathops.PathOpsError:
                    if attempt == 5:
                        raise RuntimeError(
                            f"Rounding failed for supplemental U+{ord(char):04X} {char!r}"
                        ) from None

        # Keep Latin-1 and other compact CP932 additions proportional, just as
        # build.py does for ASCII.  This is intentionally after rounding so
        # the sidebearing follows the actual final ink bounds.
        if ord(char) < 0x100 and outline.operation not in ("fullwidth", "halfwidth"):
            bounds = path.bounds
            if bounds is not None:
                path = path.transform(1, 0, 0, 1, 45 - bounds[0], 0)
                width = int(round(bounds[2] - bounds[0] + 90))

        name = _glyph_name(ord(char))
        glyph = ufo[name] if name in ufo else ufo.newGlyph(name)
        glyph.unicodes = [ord(char)]
        _copy_to_ufo(glyph, path, width)
        added.append(char)
        sources[char] = outline.source
        if modifications is not None:
            if outline.source.startswith("Zen Maru Gothic"):
                modifications[char] = ["supplemental-zen-maru-gothic", outline.operation]
            else:
                modifications[char] = ["supplemental-derived", outline.source_codepoint]

    # ``skipped`` is intentionally empty for a missing-only operation.  Keep
    # the field for callers that pass a target containing existing characters,
    # and report those without mutating their outlines.
    skipped = sorted(
        (ch for ch in target if ord(ch) in existing), key=ord
    )
    return SupplementReport(tuple(added), tuple(skipped), tuple(unresolved), sources)


__all__ = [
    "COMMON_JAPANESE_EXTRAS",
    "HALFWIDTH_TO_FULLWIDTH",
    "EXPLICIT_BASE_ALIASES",
    "ROOT",
    "SUPPLEMENTAL_COMMIT",
    "SUPPLEMENTAL_COPYRIGHT",
    "SUPPLEMENTAL_FONT_PATH",
    "SUPPLEMENTAL_FONT_URL",
    "SUPPLEMENTAL_LICENSE_URL",
    "SupplementalOutline",
    "SupplementReport",
    "add_missing_glyphs",
    "cp932_characters",
    "default_characters",
    "missing_characters",
    "open_supplemental_font",
    "outline_for",
]
