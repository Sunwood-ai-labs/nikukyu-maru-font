"""Shape kana extension fixtures and production fonts with HarfBuzz.

The normal Pillow proof images cannot exercise OpenType substitutions.  This
small verifier builds a deliberately simple UFO in memory, installs the
helpers from :mod:`kana_features`, compiles a real TTF, and asks HarfBuzz to
shape every supported sequence.  Pass ``--font`` to repeat the same checks on
the production TTF after a build.

The generated fixture and JSON report stay under ``work/`` and never write to
``sources/`` or ``outputs/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from ufoLib2 import Font

# Keep generated fixture/report files under ``work/`` while resolving source
# helpers from the project root when this command is run from any directory.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from artifact_io import save_font
from kana_features import (
    COMBINING_MARKS,
    HALFWIDTH_ADVANCE,
    HALFWIDTH_COMPOSED,
    HALFWIDTH_LIGATURE_ADVANCE,
    HALFWIDTH_SEMIVOICED,
    HALFWIDTH_TO_FULLWIDTH,
    HALFWIDTH_VOICED,
    add_halfwidth_glyphs,
    canonical_compositions,
    ccmp_feature_text,
    glyph_name,
    halfwidth_ligature_map,
    halfwidth_ligature_name,
)


DEFAULT_FIXTURE = ROOT / "work" / "kana-shaping-fixture.ttf"
DEFAULT_REPORT = ROOT / "work" / "kana-shaping-verification.json"


def expected_codepoints() -> set[int]:
    """Return enough codepoints to exercise all 58 canonical kana pairs."""

    cps = set(range(0x3041, 0x3097))
    cps.update((0x309D, 0x309E))
    cps.update(range(0x30A1, 0x30FB))
    cps.update((0x30FD, 0x30FE))
    cps.update(COMBINING_MARKS)
    cps.update(HALFWIDTH_TO_FULLWIDTH)
    cps.update(HALFWIDTH_TO_FULLWIDTH.values())
    cps.update(cp for pair in HALFWIDTH_COMPOSED for cp in pair)
    cps.update(HALFWIDTH_COMPOSED.values())
    return cps


EXPECTED_CANONICAL = canonical_compositions(expected_codepoints())
EXPECTED_HALF_WIDTH = tuple(sorted(HALFWIDTH_COMPOSED.items()))


def make_fixture(path: Path) -> tuple[Path, dict[tuple[int, int], str]]:
    """Create a tiny real TTF whose outlines make substitutions inspectable."""

    font = Font()
    font.info.familyName = "Nikukyu Kana Shaping Fixture"
    font.info.styleName = "Regular"
    font.info.unitsPerEm = 1000
    order = [".notdef"]
    notdef = font.newGlyph(".notdef")
    notdef.width = 1000
    p = notdef.getPen()
    p.moveTo((100, 0))
    p.lineTo((100, 800))
    p.lineTo((900, 800))
    p.lineTo((900, 0))
    p.closePath()

    for cp in sorted(expected_codepoints()):
        name = glyph_name(cp)
        glyph = font.newGlyph(name)
        glyph.unicodes = [cp]
        glyph.width = 0 if cp in COMBINING_MARKS else 1000
        # A simple rectangle is intentional: this test checks glyph identity,
        # substitution count, and advances rather than the production art.
        left = -160 if cp in COMBINING_MARKS else 100
        right = 160 if cp in COMBINING_MARKS else 900
        pen = glyph.getPen()
        pen.moveTo((left, 100))
        pen.lineTo((right, 100))
        pen.lineTo((right, 800))
        pen.lineTo((left, 800))
        pen.closePath()
        order.append(name)

    modifications: dict[str, list[str]] = {}
    ligatures = add_halfwidth_glyphs(font, order, modifications)
    font.glyphOrder = order

    glyphs = {}
    metrics = {}
    cmap = {}
    for name in order:
        glyph = font[name]
        pen = TTGlyphPen(None)
        glyph.draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=True))
        glyphs[name] = pen.glyph()
        metrics[name] = (round(glyph.width), 0)
        for cp in glyph.unicodes:
            cmap[cp] = name

    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=1000, descent=-200, lineGap=0)
    builder.setupNameTable(
        {
            "familyName": "Nikukyu Kana Shaping Fixture",
            "styleName": "Regular",
            "fullName": "Nikukyu Kana Shaping Fixture Regular",
            "psName": "NikukyuKanaShapingFixture-Regular",
            "version": "Version 1.0",
        }
    )
    builder.setupOS2(
        version=4,
        sTypoAscender=1000,
        sTypoDescender=-200,
        sTypoLineGap=0,
        usWinAscent=1000,
        usWinDescent=200,
        usWeightClass=400,
        usWidthClass=5,
        fsType=0,
        fsSelection=0x40,
    )
    builder.setupPost()
    builder.setupMaxp()
    features = ccmp_feature_text(
        cmap,
        halfwidth_ligatures=halfwidth_ligature_map(order),
        strict=True,
    )
    addOpenTypeFeaturesFromString(builder.font, features)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_font(builder, path)
    return path, ligatures


def shape(path: Path, text: str):
    """Return ``(glyph name, x advance, cluster)`` tuples from HarfBuzz."""

    face = hb.Face(path.read_bytes())
    font = hb.Font(face)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer)
    return tuple(
        (font.get_glyph_name(info.codepoint), position.x_advance, info.cluster)
        for info, position in zip(buffer.glyph_infos, buffer.glyph_positions)
    )


def check_font(path: Path) -> dict:
    """Check all canonical and half-width sequences in one TTF."""

    errors: list[str] = []
    font = TTFont(path)
    cmap = font.getBestCmap()
    tags = []
    if "GSUB" in font and font["GSUB"].table.FeatureList:
        tags = [record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord]
    if "ccmp" not in tags:
        errors.append("GSUB ccmp feature is missing")

    canonical_results = []
    for base, mark, composed in EXPECTED_CANONICAL:
        text = chr(base) + chr(mark)
        expected = glyph_name(composed)
        expected_advance = (
            font["hmtx"][expected][0]
            if expected in font.getGlyphOrder()
            else None
        )
        result = shape(path, text)
        passed = (
            len(result) == 1
            and result[0][0] == expected
            and expected_advance is not None
            and result[0][1] == expected_advance
        )
        if not passed:
            errors.append(
                f"canonical U+{base:04X}+U+{mark:04X}: "
                f"expected {expected}/{expected_advance}, got {result!r}"
            )
        canonical_results.append(
            {
                "base": f"U+{base:04X}",
                "mark": f"U+{mark:04X}",
                "composed": f"U+{composed:04X}",
                "expected_advance": expected_advance,
                "glyphs": result,
                "passed": passed,
            }
        )

    halfwidth_results = []
    for (base, mark), composed in EXPECTED_HALF_WIDTH:
        text = chr(base) + chr(mark)
        expected = halfwidth_ligature_name(base, mark)
        result = shape(path, text)
        passed = (
            len(result) == 1
            and result[0][0] == expected
            and result[0][1] == HALFWIDTH_LIGATURE_ADVANCE
        )
        if not passed:
            errors.append(
                f"half-width U+{base:04X}+U+{mark:04X}: "
                f"expected {expected}/{HALFWIDTH_LIGATURE_ADVANCE}, got {result!r}"
            )
        halfwidth_results.append(
            {
                "base": f"U+{base:04X}",
                "mark": f"U+{mark:04X}",
                "composed": f"U+{composed:04X}",
                "glyphs": result,
                "passed": passed,
            }
        )

    plain_halfwidth_failures = []
    for cp in sorted(HALFWIDTH_TO_FULLWIDTH):
        result = shape(path, chr(cp))
        if len(result) != 1 or result[0][1] != HALFWIDTH_ADVANCE:
            plain_halfwidth_failures.append(
                f"U+{cp:04X}: expected one glyph/500, got {result!r}"
            )
    for cp in (HALFWIDTH_VOICED, HALFWIDTH_SEMIVOICED):
        result = shape(path, chr(cp))
        if len(result) != 1 or result[0][1] != HALFWIDTH_ADVANCE:
            plain_halfwidth_failures.append(
                f"U+{cp:04X}: expected standalone one glyph/500, got {result!r}"
            )
    errors.extend(plain_halfwidth_failures)

    missing = [cp for cp in (*COMBINING_MARKS, *HALFWIDTH_TO_FULLWIDTH) if cp not in cmap]
    if missing:
        errors.append(
            "missing cmap entries: " + ", ".join(f"U+{cp:04X}" for cp in missing)
        )

    return {
        "font": str(path),
        "units_per_em": font["head"].unitsPerEm,
        "unicode_characters": len(cmap),
        "gsub_features": tags,
        "canonical_pairs_expected": len(EXPECTED_CANONICAL),
        "canonical_pairs_passed": sum(item["passed"] for item in canonical_results),
        "halfwidth_pairs_expected": len(EXPECTED_HALF_WIDTH),
        "halfwidth_pairs_passed": sum(item["passed"] for item in halfwidth_results),
        "plain_halfwidth_checked": len(HALFWIDTH_TO_FULLWIDTH) + 2,
        "plain_halfwidth_failures": plain_halfwidth_failures,
        "canonical": canonical_results,
        "halfwidth": halfwidth_results,
        "errors": errors,
        "passed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--font",
        type=Path,
        help="also check a production TTF (for example outputs/NikukyuMaru-Regular.ttf)",
    )
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    fixture, _ligatures = make_fixture(args.fixture)
    reports = {"fixture": check_font(fixture)}
    if args.font:
        if not args.font.exists():
            reports["production"] = {
                "font": str(args.font),
                "errors": ["font does not exist"],
                "passed": False,
            }
        else:
            reports["production"] = check_font(args.font)

    report = {
        "harfbuzz": getattr(hb, "version_string", lambda: "unknown")(),
        "fixture_artifact": str(fixture),
        "expected_canonical_pairs": len(EXPECTED_CANONICAL),
        "expected_halfwidth_pairs": len(EXPECTED_HALF_WIDTH),
        "reports": reports,
        "passed": all(item.get("passed", False) for item in reports.values()),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
