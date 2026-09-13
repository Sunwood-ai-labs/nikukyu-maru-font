"""Verify that the 0.104 Latin cat treatment changes only the 104 Latin letters."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
DEFAULT_BASELINE = ROOT / "work" / "latin-cats" / "baseline-0103.ttf"
DEFAULT_CURRENT = ROOT / "outputs" / "NikukyuMaru-Regular.ttf"
DEFAULT_REPORT = ROOT / "outputs" / "latin-review" / "regression.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def allowed_codepoints() -> set[int]:
    return {
        *range(ord("A"), ord("Z") + 1),
        *range(ord("a"), ord("z") + 1),
        *range(ord("Ａ"), ord("Ｚ") + 1),
        *range(ord("ａ"), ord("ｚ") + 1),
    }


def cp_label(cp: int) -> str:
    return f"U+{cp:04X} {chr(cp)}"


def stable_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [stable_value(item) for item in value]
    if isinstance(value, list):
        return [stable_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): stable_value(item) for key, item in value.items()}
    return value


def outline_record(font: TTFont, glyph_name: str) -> list[Any]:
    glyph_set = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return stable_value(pen.value)


def outline_digest(font: TTFont, glyph_name: str) -> str:
    data = json.dumps(outline_record(font, glyph_name), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def table_bytes(font: TTFont, tag: str) -> bytes | None:
    if tag not in font:
        return None
    return font.getTableData(tag)


def display_path(path: Path) -> str:
    """Prefer a workspace-relative path while supporting external fixtures."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def file_record(path: Path) -> dict[str, Any]:
    return {"path": display_path(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def compile_reproduction(ufo_path: Path, output_dir: Path, current_path: Path) -> dict[str, Any]:
    """Compile a copied UFO by redirecting build.py's output globals only."""

    import build

    output_dir.mkdir(parents=True, exist_ok=True)
    current_woff2_path = current_path.with_suffix(".woff2")
    current_before = {
        "ttf": file_record(current_path),
        "woff2": file_record(current_woff2_path),
    }
    build.UFO = ufo_path
    build.OUT = output_dir
    build.compile_font()
    compiled_ttf = output_dir / "NikukyuMaru-Regular.ttf"
    compiled_woff2 = output_dir / "NikukyuMaru-Regular.woff2"
    current_after = {
        "ttf": file_record(current_path),
        "woff2": file_record(current_woff2_path),
    }
    ttf = file_record(compiled_ttf)
    woff2 = file_record(compiled_woff2)
    return {
        "ufo": display_path(ufo_path),
        "output_directory": display_path(output_dir),
        "current_before": current_before,
        "current_after": current_after,
        "current_unchanged": current_before == current_after,
        "compiled_ttf": ttf,
        "compiled_woff2": woff2,
        "ttf_bytes_equal": ttf["sha256"] == current_after["ttf"]["sha256"] and ttf["bytes"] == current_after["ttf"]["bytes"],
        "woff2_bytes_equal": woff2["sha256"] == current_after["woff2"]["sha256"] and woff2["bytes"] == current_after["woff2"]["bytes"],
    }


def ufo_outline_digest(glyph: Any) -> str:
    pen = RecordingPen()
    glyph.draw(pen)
    data = json.dumps(stable_value(pen.value), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def reapply_latin_cats(ufo_path: Path) -> dict[str, Any]:
    """Reapply the 52 masters, then derive the 52 fullwidth variants in memory."""

    from ufoLib2 import Font

    import latin_cats

    font = Font.open(ufo_path)
    letters = latin_cats.LETTERS
    names = {ch: f"uni{ord(ch):04X}" for ch in letters}
    full_names = {ch: f"uni{ord(ch) + 0xFEE0:04X}" for ch in letters}
    before_ascii = {ch: (ufo_outline_digest(font[names[ch]]), font[names[ch]].width) for ch in letters}
    before_full = {ch: (ufo_outline_digest(font[full_names[ch]]), font[full_names[ch]].width) for ch in letters}

    modifications: dict[str, list[str]] = {}
    latin_cats.apply_latin_cats(font, modifications)
    after_ascii = {ch: (ufo_outline_digest(font[names[ch]]), font[names[ch]].width) for ch in letters}
    ascii_changes = [
        {"character": ch, "before": list(before_ascii[ch]), "after": list(after_ascii[ch])}
        for ch in letters
        if before_ascii[ch] != after_ascii[ch]
    ]

    for ch in letters:
        source = font[names[ch]]
        target = font[full_names[ch]]
        scale = min(1, 900 / source.width)
        target.clearContours()
        source.draw(TransformPen(target.getPen(), (scale, 0, 0, 1, (1000 - source.width * scale) / 2, 0)))
        target.width = 1000
    after_full = {ch: (ufo_outline_digest(font[full_names[ch]]), font[full_names[ch]].width) for ch in letters}
    full_changes = [
        {"character": ch, "before": list(before_full[ch]), "after": list(after_full[ch])}
        for ch in letters
        if before_full[ch] != after_full[ch]
    ]
    return {
        "ufo": display_path(ufo_path),
        "ascii_count": len(letters),
        "fullwidth_count": len(letters),
        "ascii_changed": ascii_changes,
        "ascii_changed_count": len(ascii_changes),
        "ascii_matches_current": not ascii_changes,
        "fullwidth_changed": full_changes,
        "fullwidth_changed_count": len(full_changes),
        "fullwidth_matches_current": not full_changes,
        "pass": not ascii_changes and not full_changes,
    }


def compare_fonts(baseline_path: Path, current_path: Path) -> dict[str, Any]:
    baseline = TTFont(baseline_path, recalcBBoxes=False, recalcTimestamp=False)
    current = TTFont(current_path, recalcBBoxes=False, recalcTimestamp=False)
    allowed = allowed_codepoints()
    baseline_cmap = baseline.getBestCmap() or {}
    current_cmap = current.getBestCmap() or {}
    baseline_order = baseline.getGlyphOrder()
    current_order = current.getGlyphOrder()

    baseline_unicodes = set(baseline_cmap)
    current_unicodes = set(current_cmap)
    added_unicodes = sorted(current_unicodes - baseline_unicodes)
    removed_unicodes = sorted(baseline_unicodes - current_unicodes)
    mapping_changes = sorted(
        cp for cp in baseline_unicodes & current_unicodes if baseline_cmap[cp] != current_cmap[cp]
    )

    baseline_reverse: dict[str, set[int]] = {}
    current_reverse: dict[str, set[int]] = {}
    for cp, name in baseline_cmap.items():
        baseline_reverse.setdefault(name, set()).add(cp)
    for cp, name in current_cmap.items():
        current_reverse.setdefault(name, set()).add(cp)

    baseline_metrics = baseline["hmtx"].metrics
    current_metrics = current["hmtx"].metrics
    metric_changes: list[dict[str, Any]] = []
    outline_changes: list[dict[str, Any]] = []
    all_glyphs = sorted(set(baseline_order) | set(current_order), key=lambda name: (baseline_order.index(name) if name in baseline_order else 10**9, name))
    for name in all_glyphs:
        if name not in baseline_metrics or name not in current_metrics:
            metric_changes.append({"glyph": name, "kind": "glyph_added_or_removed"})
        elif tuple(baseline_metrics[name]) != tuple(current_metrics[name]):
            metric_changes.append({
                "glyph": name,
                "codepoints": [cp_label(cp) for cp in sorted(baseline_reverse.get(name, set()) | current_reverse.get(name, set()))],
                "baseline": list(baseline_metrics[name]),
                "current": list(current_metrics[name]),
            })
        if name not in baseline_order or name not in current_order:
            continue
        if outline_digest(baseline, name) != outline_digest(current, name):
            outline_changes.append({
                "glyph": name,
                "codepoints": [cp_label(cp) for cp in sorted(baseline_reverse.get(name, set()) | current_reverse.get(name, set()))],
            })

    def unexpected(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for item in changes:
            cps = set(baseline_reverse.get(item["glyph"], set())) | set(current_reverse.get(item["glyph"], set()))
            if not cps or not cps.issubset(allowed):
                result.append(item)
        return result

    def changed_codepoints(changes: list[dict[str, Any]]) -> set[int]:
        codepoints: set[int] = set()
        for item in changes:
            codepoints.update(baseline_reverse.get(item["glyph"], set()))
            codepoints.update(current_reverse.get(item["glyph"], set()))
        return codepoints

    outline_changed_codepoints = changed_codepoints(outline_changes)
    metric_changed_codepoints = changed_codepoints(metric_changes)

    gsub_baseline = table_bytes(baseline, "GSUB")
    gsub_current = table_bytes(current, "GSUB")
    gsub_equal = gsub_baseline == gsub_current
    report = {
        "allowed_codepoints": sorted(allowed),
        "allowed_count": len(allowed),
        "allowed_labels": [cp_label(cp) for cp in sorted(allowed)],
        "files": {"baseline": file_record(baseline_path), "current": file_record(current_path)},
        "unicode_set": {
            "baseline_count": len(baseline_unicodes),
            "current_count": len(current_unicodes),
            "equal": baseline_unicodes == current_unicodes,
            "added": [cp_label(cp) for cp in added_unicodes],
            "removed": [cp_label(cp) for cp in removed_unicodes],
            "mapping_changes": [cp_label(cp) for cp in mapping_changes],
        },
        "glyph_order": {
            "baseline_count": len(baseline_order),
            "current_count": len(current_order),
            "equal": baseline_order == current_order,
            "first_difference": next((index for index, pair in enumerate(zip(baseline_order, current_order)) if pair[0] != pair[1]), None),
            "only_in_baseline": [name for name in baseline_order if name not in current_order],
            "only_in_current": [name for name in current_order if name not in baseline_order],
        },
        "gsub": {
            "baseline_present": gsub_baseline is not None,
            "current_present": gsub_current is not None,
            "equal_bytes": gsub_equal,
            "baseline_bytes": len(gsub_baseline or b""),
            "current_bytes": len(gsub_current or b""),
            "baseline_sha256": hashlib.sha256(gsub_baseline or b"").hexdigest(),
            "current_sha256": hashlib.sha256(gsub_current or b"").hexdigest(),
        },
        "outline_comparison": {
            "glyphs_compared": len(set(baseline_order) & set(current_order)),
            "changed_glyphs": outline_changes,
            "changed_count": len(outline_changes),
            "changed_codepoints": [cp_label(cp) for cp in sorted(outline_changed_codepoints)],
            "changed_codepoint_count": len(outline_changed_codepoints),
            "changed_codepoints_exactly_allowed": outline_changed_codepoints == allowed,
            "unexpected_changes": unexpected(outline_changes),
        },
        "metrics_comparison": {
            "glyphs_compared": len(all_glyphs),
            "changed_glyphs": metric_changes,
            "changed_count": len(metric_changes),
            "changed_codepoints": [cp_label(cp) for cp in sorted(metric_changed_codepoints)],
            "changed_codepoint_count": len(metric_changed_codepoints),
            "changed_codepoints_subset_allowed": metric_changed_codepoints.issubset(allowed),
            "unexpected_changes": unexpected(metric_changes),
        },
    }
    report["pass"] = all(
        (
            report["allowed_count"] == 104,
            report["unicode_set"]["equal"],
            not report["unicode_set"]["mapping_changes"],
            report["glyph_order"]["equal"],
            gsub_equal,
            report["outline_comparison"]["changed_codepoints_exactly_allowed"],
            not report["outline_comparison"]["unexpected_changes"],
            report["metrics_comparison"]["changed_codepoints_subset_allowed"],
            not report["metrics_comparison"]["unexpected_changes"],
        )
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--compile-ufo", type=Path, help="Copy of a UFO to compile into an isolated output directory")
    parser.add_argument("--compile-output", type=Path, help="Isolated output directory for --compile-ufo")
    parser.add_argument("--reapply-ufo", type=Path, help="Copy of a UFO for in-memory Latin master reapplication")
    args = parser.parse_args()
    baseline = args.baseline.resolve()
    current = args.current.resolve()
    report = compare_fonts(baseline, current)
    report["baseline"] = display_path(baseline)
    report["current"] = display_path(current)
    if args.compile_ufo is not None:
        if args.compile_output is None:
            parser.error("--compile-output is required with --compile-ufo")
        report["compile_reproduction"] = compile_reproduction(
            args.compile_ufo.resolve(), args.compile_output.resolve(), current
        )
        report["pass"] = bool(
            report["pass"]
            and report["compile_reproduction"]["current_unchanged"]
            and report["compile_reproduction"]["ttf_bytes_equal"]
            and report["compile_reproduction"]["woff2_bytes_equal"]
        )
    if args.reapply_ufo is not None:
        report["ufo_reapplication"] = reapply_latin_cats(args.reapply_ufo.resolve())
        report["pass"] = bool(report["pass"] and report["ufo_reapplication"]["pass"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    summary = {"pass": report["pass"], "outline_changed": report["outline_comparison"]["changed_count"], "metrics_changed": report["metrics_comparison"]["changed_count"], "unexpected_outline": len(report["outline_comparison"]["unexpected_changes"]), "unexpected_metrics": len(report["metrics_comparison"]["unexpected_changes"])}
    if "compile_reproduction" in report:
        summary["compile_ttf_equal"] = report["compile_reproduction"]["ttf_bytes_equal"]
        summary["compile_woff2_equal"] = report["compile_reproduction"]["woff2_bytes_equal"]
    if "ufo_reapplication" in report:
        summary["ascii_reapply_equal"] = report["ufo_reapplication"]["ascii_matches_current"]
        summary["fullwidth_reapply_equal"] = report["ufo_reapplication"]["fullwidth_matches_current"]
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
