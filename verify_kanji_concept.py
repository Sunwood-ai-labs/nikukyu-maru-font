"""Validate and render the eight kanji concept outlines without touching production files.

The input TTF can be a prototype or the final output. This script checks the
source contour records and the compiled glyph metrics, then writes a side-by-side
Pillow render for a human review of glyph height and weight against kana.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTLINE = ROOT / "sources" / "kanji-concept-outlines.json"
DEFAULT_REFERENCE = ROOT / "references" / "03-kanji-refined.png"
DEFAULT_FONT = ROOT / "outputs" / "NikukyuMaru-Regular.ttf"
DEFAULT_BASELINE = None
DEFAULT_REPORT = ROOT / "work" / "concept-kanji-verification.json"
DEFAULT_IMAGE = ROOT / "work" / "concept-kanji-render-review.png"
DEFAULT_SMALL_IMAGE = ROOT / "work" / "concept-kanji-small-render-review.png"
SELECTED = "名今日月年店休住"
TRACE_CHARS = "名前今日月年時間店営業休価格住所"
TRACE_XS = [30, 330, 627, 919, 1230]
TRACE_YS = [45, 350, 635, 917, 1220]
KANA_REFERENCE = "あいうえおかきくけこさしすせそたちつてと"
RASTER_SIZE = 180
SMALL_SIZES = (16, 24, 32, 48)
UI_FONT_PATH = Path("C:/Windows/Fonts/meiryo.ttc")
if not UI_FONT_PATH.exists():
    UI_FONT_PATH = Path("C:/Windows/Fonts/arial.ttf")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def source_metrics(item: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    commands = item.get("commands")
    if not isinstance(commands, list) or not commands:
        return {"command_count": 0, "contour_count": 0}, ["commands are empty"]
    allowed = {"moveTo": 2, "cubicTo": 6, "close": 0}
    contour_count = 0
    active = False
    points: list[tuple[float, float]] = []
    for index, command in enumerate(commands):
        if not isinstance(command, list) or not command:
            errors.append(f"command {index} is not a non-empty list")
            continue
        op = command[0]
        if op not in allowed:
            errors.append(f"command {index} uses unsupported op {op!r}")
            continue
        values = command[1:]
        if len(values) != allowed[op]:
            errors.append(f"command {index} {op} has {len(values)} coordinates")
        if len(values) % 2:
            errors.append(f"command {index} has an odd coordinate count")
        for value in values:
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                errors.append(f"command {index} contains a non-finite coordinate")
        if op == "moveTo":
            if active:
                errors.append(f"command {index} starts a contour before close")
            active = True
            contour_count += 1
        elif op == "cubicTo" and not active:
            errors.append(f"command {index} has cubicTo before moveTo")
        elif op == "close":
            if not active:
                errors.append(f"command {index} closes without moveTo")
            active = False
        for pos in range(0, len(values) - 1, 2):
            points.append((float(values[pos]), float(values[pos + 1])))
    if active:
        errors.append("last contour is not closed")
    if not points:
        errors.append("no outline coordinates")
    bounds = None
    if points:
        bounds = [min(x for x, _ in points), min(y for _, y in points),
                  max(x for x, _ in points), max(y for _, y in points)]
        if bounds[0] < 0 or bounds[2] > 1000 or bounds[1] < -350 or bounds[3] > 1200:
            errors.append(f"source outline exceeds nominal font box: {bounds}")
    if item.get("width") != 1000:
        errors.append(f"source width is {item.get('width')!r}, expected 1000")
    return {
        "command_count": len(commands),
        "contour_count": contour_count,
        "coordinate_bounds": bounds,
        "width": item.get("width"),
    }, errors


def glyph_metrics(font: TTFont, char: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    cp = ord(char)
    cmap = font.getBestCmap()
    name = cmap.get(cp)
    if not name:
        return {"char": char, "codepoint": f"U+{cp:04X}", "glyph_name": None}, [
            f"{char} U+{cp:04X} is absent from cmap"
        ]
    glyph = font["glyf"][name]
    glyph.recalcBounds(font["glyf"])
    advance, lsb = font["hmtx"][name]
    os2 = font["OS/2"]
    bounds = [glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax] if glyph.numberOfContours else None
    within = True
    if bounds:
        within = bounds[0] >= 0 and bounds[2] <= advance and bounds[1] >= -os2.usWinDescent and bounds[3] <= os2.usWinAscent
    if advance != 1000:
        errors.append(f"{char} advance is {advance}, expected 1000")
    if glyph.numberOfContours == 0:
        errors.append(f"{char} has no contours")
    if bounds and not within:
        errors.append(f"{char} exceeds advance or Windows vertical bounds: {bounds}/{advance}")
    return {
        "char": char,
        "codepoint": f"U+{cp:04X}",
        "glyph_name": name,
        "advance": advance,
        "left_side_bearing": lsb,
        "contour_count": glyph.numberOfContours,
        "bounds": bounds,
        "within_advance_and_windows_bounds": within,
    }, errors


def raster_metrics(font_path: Path, char: str, size: int = RASTER_SIZE) -> dict[str, Any]:
    font = ImageFont.truetype(str(font_path), size)
    canvas = 360
    image = Image.new("L", (canvas, canvas), 255)
    draw = ImageDraw.Draw(image)
    baseline = 285
    draw.text((canvas // 2, baseline), char, font=font, fill=0, anchor="ms")
    array = np.asarray(image)
    mask = (array < 128).astype("uint8")
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {
            "font_size": size,
            "ink_pixels": 0,
            "bbox_px": None,
            "height_px": 0,
            "width_px": 0,
            "component_count": 0,
            "hole_count": 0,
            "ink_density": 0.0,
        }
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    components, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    component_areas = [int(area) for area in stats[1:, cv2.CC_STAT_AREA] if area >= 2]
    inverse = (1 - mask).astype("uint8")
    hole_components, hole_labels, hole_stats, _ = cv2.connectedComponentsWithStats(inverse, connectivity=8)
    boundary_labels = set(np.unique(np.concatenate([
        hole_labels[0, :], hole_labels[-1, :], hole_labels[:, 0], hole_labels[:, -1]
    ])))
    hole_count = sum(
        1 for index in range(1, hole_components)
        if index not in boundary_labels and hole_stats[index, cv2.CC_STAT_AREA] >= 2
    )
    ink = int(mask.sum())
    bbox_area = (x1 - x0 + 1) * (y1 - y0 + 1)
    return {
        "font_size": size,
        "ink_pixels": ink,
        "bbox_px": [x0, y0, x1 + 1, y1 + 1],
        "height_px": y1 - y0 + 1,
        "width_px": x1 - x0 + 1,
        "component_count": len(component_areas),
        "component_areas_px": sorted(component_areas, reverse=True),
        "hole_count": hole_count,
        "ink_density": round(ink / bbox_area, 4) if bbox_area else 0.0,
    }


def reference_metrics(reference_path: Path, char: str) -> dict[str, Any]:
    """Measure the source image cell used by trace_kanji_concept.py."""
    if not reference_path.exists():
        return {"available": False, "error": "reference image does not exist"}
    index = TRACE_CHARS.find(char)
    if index < 0:
        return {"available": False, "error": f"{char} is not in trace source order"}
    row, col = divmod(index, 4)
    gray = np.asarray(Image.open(reference_path).convert("L"))
    x0, x1 = TRACE_XS[col], TRACE_XS[col + 1]
    y0, y1 = TRACE_YS[row], TRACE_YS[row + 1]
    if y1 > gray.shape[0] or x1 > gray.shape[1]:
        return {"available": False, "error": "reference cell exceeds image bounds"}
    mask = (gray[y0:y1, x0:x1] < 128).astype("uint8")
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {"available": True, "ink_pixels": 0, "component_count": 0, "hole_count": 0}
    components, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    component_areas = [int(area) for area in stats[1:, cv2.CC_STAT_AREA] if area >= 2]
    inverse = (1 - mask).astype("uint8")
    hole_components, hole_labels, hole_stats, _ = cv2.connectedComponentsWithStats(inverse, connectivity=8)
    boundary_labels = set(np.unique(np.concatenate([
        hole_labels[0, :], hole_labels[-1, :], hole_labels[:, 0], hole_labels[:, -1]
    ])))
    hole_count = sum(
        1 for part in range(1, hole_components)
        if part not in boundary_labels and hole_stats[part, cv2.CC_STAT_AREA] >= 2
    )
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    return {
        "available": True,
        "cell": [x0, y0, x1, y1],
        "ink_pixels": int(mask.sum()),
        "bbox_px": [x_min, y_min, x_max + 1, y_max + 1],
        "component_count": len(component_areas),
        "component_areas_px": sorted(component_areas, reverse=True),
        "hole_count": hole_count,
    }


def draw_cell(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, char: str,
              x: int, y: int, width: int, height: int, fill: str = "#342622") -> None:
    draw.text((x + width // 2, y + height - 24), char, font=font, fill=fill, anchor="ms")


def render_review(font_path: Path, baseline_path: Path | None, output: Path) -> None:
    size = 180
    display_font = ImageFont.truetype(str(font_path), size)
    baseline_font = ImageFont.truetype(str(baseline_path), size) if baseline_path and baseline_path.exists() else None
    kana_font = display_font
    columns = 6
    cell_w, cell_h = 250, 270
    left, top = 50, 155
    width = left * 2 + columns * cell_w
    height = top + len(SELECTED) * cell_h + 120
    image = Image.new("RGB", (width, height), "#fff8eb")
    draw = ImageDraw.Draw(image)
    draw.text((left, 30), "漢字コンセプト / 実フォント描画", font=ImageFont.truetype(str(UI_FONT_PATH), 30), fill="#342622")
    draw.text((left, 68), "selected kanji + kana reference / same 180px baseline", font=ImageFont.truetype(str(UI_FONT_PATH), 18), fill="#806b60")
    headers = ["検証対象", "比較用の旧版" if baseline_font else "旧版指定なし", "あ", "か", "な", "の"]
    for col, header in enumerate(headers):
        x = left + col * cell_w
        draw.rounded_rectangle((x + 7, top - 50, x + cell_w - 7, top - 8), radius=12, fill="#f4decc")
        draw.text((x + cell_w // 2, top - 29), header, font=ImageFont.truetype(str(UI_FONT_PATH), 17), fill="#342622", anchor="mm")
    for row, char in enumerate(SELECTED):
        y = top + row * cell_h
        draw.text((left - 3, y + 18), f"{char}  U+{ord(char):04X}", font=ImageFont.truetype(str(UI_FONT_PATH), 18), fill="#806b60")
        row_top = y + 35
        draw.line((left, y + cell_h - 24, left + columns * cell_w, y + cell_h - 24), fill="#d8c9b9", width=1)
        draw_cell(draw, display_font, char, left, row_top, cell_w, cell_h - 35)
        if baseline_font:
            draw_cell(draw, baseline_font, char, left + cell_w, row_top, cell_w, cell_h - 35, fill="#6e5148")
        for col, kana in enumerate("あかなの", start=2):
            draw_cell(draw, kana_font, kana, left + col * cell_w, row_top, cell_w, cell_h - 35)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def render_small_review(font_path: Path, baseline_path: Path | None, output: Path) -> None:
    """Render true small pixel sizes, then enlarge with nearest-neighbor for review."""
    ui = ImageFont.truetype(str(UI_FONT_PATH), 14)
    sections: list[Image.Image] = []
    logical_width = 1120
    for size in SMALL_SIZES:
        glyph_font = ImageFont.truetype(str(font_path), size)
        old_font = ImageFont.truetype(str(baseline_path), size) if baseline_path and baseline_path.exists() else None
        row_height = max(54, size + 28)
        logical_height = 46 + len(SELECTED) * row_height + 18
        section = Image.new("RGB", (logical_width, logical_height), "#fff8eb")
        draw = ImageDraw.Draw(section)
        draw.text((24, 14), f"{size}px / 実サイズ×3", font=ui, fill="#342622")
        columns = [(170, "検証対象"), (340, "比較用の旧版" if old_font else "旧版指定なし"), (520, "あ"), (670, "か"), (820, "な"), (970, "の")]
        for x, label in columns:
            draw.text((x, 17), label, font=ui, fill="#806b60", anchor="mm")
        for row, char in enumerate(SELECTED):
            y = 46 + row * row_height
            draw.text((24, y + row_height // 2), f"{char} U+{ord(char):04X}", font=ui, fill="#806b60", anchor="lm")
            baseline = y + row_height - 12
            draw.text((170, baseline), char, font=glyph_font, fill="#342622", anchor="ms")
            if old_font:
                draw.text((340, baseline), char, font=old_font, fill="#805f52", anchor="ms")
            for x, kana in columns[2:]:
                draw.text((x, baseline), kana, font=glyph_font, fill="#342622", anchor="ms")
            draw.line((12, y + row_height - 1, logical_width - 12, y + row_height - 1), fill="#d8c9b9", width=1)
        sections.append(section.resize((logical_width * 3, logical_height * 3), Image.Resampling.NEAREST))
    total_height = sum(section.height for section in sections) + 12 * (len(sections) - 1)
    image = Image.new("RGB", (sections[0].width, total_height), "#fff8eb")
    cursor = 0
    for section in sections:
        image.paste(section, (0, cursor))
        cursor += section.height + 12
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def build_report(font_path: Path, outline_path: Path, reference_path: Path, baseline_path: Path | None, report_path: Path, image_path: Path, small_image_path: Path) -> dict[str, Any]:
    outline_data = json.loads(outline_path.read_text(encoding="utf-8"))
    font = TTFont(font_path)
    errors: list[str] = []
    warnings: list[str] = []
    source_entries: dict[str, Any] = {}
    if set(outline_data) != set(SELECTED):
        errors.append(f"source keys are {''.join(outline_data)}, expected {SELECTED}")
    for char in SELECTED:
        if char not in outline_data:
            continue
        metrics, item_errors = source_metrics(outline_data[char])
        source_entries[char] = metrics
        errors.extend(f"source {char}: {error}" for error in item_errors)
    glyph_entries: dict[str, Any] = {}
    for char in SELECTED:
        metrics, item_errors = glyph_metrics(font, char)
        glyph_entries[char] = metrics
        errors.extend(item_errors)
        source_contours = source_entries.get(char, {}).get("contour_count")
        if source_contours is not None:
            compiled_contours = metrics.get("contour_count")
            if compiled_contours < source_contours:
                errors.append(f"{char} compiled contour count decreased: {source_contours}/{compiled_contours}")
            elif compiled_contours != source_contours:
                warnings.append(f"{char} source/compiled contour count differs by outline decomposition: {source_contours}/{compiled_contours}")
    all_render_chars = SELECTED + KANA_REFERENCE
    raster = {char: raster_metrics(font_path, char) for char in all_render_chars}
    small_raster = {
        str(size): {char: raster_metrics(font_path, char, size) for char in all_render_chars}
        for size in SMALL_SIZES
    }
    reference = {char: reference_metrics(reference_path, char) for char in SELECTED}
    for char in SELECTED:
        ref = reference[char]
        compiled = raster[char]
        if not ref.get("available"):
            warnings.append(f"{char} source reference metrics unavailable: {ref.get('error', 'unknown error')}")
        elif ref.get("ink_pixels", 0) == 0:
            errors.append(f"{char} source reference cell is empty")
        else:
            if compiled.get("component_count", 0) < ref.get("component_count", 0):
                warnings.append(f"{char} compiled raster has fewer connected components than reference: {ref['component_count']}/{compiled['component_count']}")
            if compiled.get("hole_count", 0) < ref.get("hole_count", 0):
                warnings.append(f"{char} compiled raster has fewer holes than reference: {ref['hole_count']}/{compiled['hole_count']}")
    kana_metrics = [raster[ch] for ch in KANA_REFERENCE if raster[ch]["height_px"]]
    median_height = float(np.median([m["height_px"] for m in kana_metrics])) if kana_metrics else 0.0
    median_density = float(np.median([m["ink_density"] for m in kana_metrics])) if kana_metrics else 0.0
    comparisons = {}
    for char in SELECTED:
        current = raster[char]
        height_ratio = current["height_px"] / median_height if median_height else 0.0
        density_ratio = current["ink_density"] / median_density if median_density else 0.0
        if current["height_px"] == 0:
            errors.append(f"{char} has an empty raster at {RASTER_SIZE}px")
        if height_ratio < 0.80 or height_ratio > 1.20:
            warnings.append(f"{char} rendered height ratio to kana median is {height_ratio:.2f}")
        if density_ratio < 0.70 or density_ratio > 1.35:
            warnings.append(f"{char} ink density ratio to kana median is {density_ratio:.2f}")
        comparisons[char] = {
            "height_ratio_to_kana_median": round(height_ratio, 3),
            "ink_density_ratio_to_kana_median": round(density_ratio, 3),
        }
    render_review(font_path, baseline_path, image_path)
    render_small_review(font_path, baseline_path, small_image_path)
    small_comparisons: dict[str, dict[str, dict[str, float]]] = {}
    for size in SMALL_SIZES:
        by_char = small_raster[str(size)]
        kana_heights = [by_char[ch]["height_px"] for ch in KANA_REFERENCE if by_char[ch]["height_px"]]
        kana_densities = [by_char[ch]["ink_density"] for ch in KANA_REFERENCE if by_char[ch]["height_px"]]
        median_small_height = float(np.median(kana_heights)) if kana_heights else 0.0
        median_small_density = float(np.median(kana_densities)) if kana_densities else 0.0
        small_comparisons[str(size)] = {}
        for char in SELECTED:
            item = by_char[char]
            small_comparisons[str(size)][char] = {
                "height_ratio_to_kana_median": round(item["height_px"] / median_small_height, 3) if median_small_height else 0.0,
                "ink_density_ratio_to_kana_median": round(item["ink_density"] / median_small_density, 3) if median_small_density else 0.0,
            }
    result = {
        "font": rel(font_path),
        "font_sha256": hashlib.sha256(font_path.read_bytes()).hexdigest(),
        "outline_source": rel(outline_path),
        "baseline_font": rel(baseline_path) if baseline_path else None,
        "selected": list(SELECTED),
        "source": source_entries,
        "compiled_glyphs": glyph_entries,
        "reference_image": rel(reference_path),
        "reference_cells": reference,
        "raster": raster,
        "small_sizes_px": list(SMALL_SIZES),
        "small_raster": small_raster,
        "small_comparison_to_kana": small_comparisons,
        "kana_reference": list(KANA_REFERENCE),
        "comparison_to_kana": {
            "font_size_px": RASTER_SIZE,
            "median_kana_height_px": median_height,
            "median_kana_ink_density": median_density,
            "per_glyph": comparisons,
        },
        "review_image": rel(image_path),
        "small_review_image": rel(small_image_path),
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--outline", type=Path, default=DEFAULT_OUTLINE)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--baseline-font", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--small-image", type=Path, default=DEFAULT_SMALL_IMAGE)
    args = parser.parse_args()
    if args.baseline_font is not None and not args.baseline_font.is_file():
        parser.error("--baseline-font does not exist; omit this optional argument to verify without an old font")
    result = build_report(args.font.resolve(), args.outline.resolve(), args.reference.resolve(), args.baseline_font.resolve() if args.baseline_font else None, args.report.resolve(), args.image.resolve(), args.small_image.resolve())
    print(json.dumps({
        "passed": result["passed"],
        "selected": len(result["selected"]),
        "errors": result["errors"],
        "warnings": result["warnings"],
        "report": rel(args.report.resolve()),
        "image": rel(args.image.resolve()),
        "small_image": rel(args.small_image.resolve()),
        "median_kana_height_px": result["comparison_to_kana"]["median_kana_height_px"],
        "median_kana_ink_density": result["comparison_to_kana"]["median_kana_ink_density"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
