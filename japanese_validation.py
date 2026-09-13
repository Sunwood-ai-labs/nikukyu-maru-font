"""用途別の日本語コーパスとフォント構造を検証する。

このスクリプトはフォントやUFOを生成・変更しない。TTF/WOFF2を読み、
``outputs/japanese-validation.html``、輪郭比較PNG/HTML、機械可読なJSONを
作るだけである。
文字数のカウントだけではなく、実際の名前・住所・価格・日付・文章を
コードポイント単位で調べる。結合濁点と半角カナは代替表示で合格にせず、
未収録として明示する。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
DEFAULT_FONT = ROOT / "outputs" / "NikukyuMaru-Regular.ttf"
DEFAULT_WEBFONT = ROOT / "outputs" / "NikukyuMaru-Regular.woff2"
DEFAULT_REPORT = ROOT / "outputs" / "japanese-validation.json"
DEFAULT_PAGE = ROOT / "outputs" / "japanese-validation.html"
DEFAULT_OUTLINE_REVIEW_PNG = ROOT / "outputs" / "japanese-outline-review.png"
DEFAULT_OUTLINE_REVIEW_PAGE = ROOT / "outputs" / "japanese-outline-review.html"
REFERENCE_IMAGE = ROOT / "references" / "01-nikukyu.png"
DESIGN_CONFIG = ROOT / "sources" / "design.json"
MODIFICATIONS_FILE = ROOT / "sources" / "modifications.json"

# ``build.py`` always starts from Mochiy for the general repertoire, while
# ``design.json["kanji_base"]`` selects the actual CJK source.  Keep these
# names in one place so the outline review cannot accidentally use the first
# ``base=TTFont(...)`` occurrence (which is the supplemental Mochiy load).
BASE_FONT_PATHS: dict[str, Path] = {
    "Mochiy Pop One": ROOT / "vendor" / "MochiyPopOne-Regular.ttf",
    "Zen Maru Gothic Black": ROOT / "vendor" / "ZenMaruGothic-Black.ttf",
}
REFERENCE_VECTOR_TAGS = frozenset(
    {"concept-reference-vector-outline", "approved-reference-vector-outline"}
)

# Combining dakuten are intentionally zero-advance anchor marks. Their outline
# is placed to the left of the base kana, so a negative xMin is expected and
# must not be mistaken for a clipped visible glyph.
POSITIONED_COMBINING_MARKS = frozenset({0x3099, 0x309A})


@dataclass(frozen=True)
class CorpusCase:
    """A user-facing string and the reason it is in the test corpus."""

    key: str
    title: str
    text: str
    note: str


# Keep the raw combining marks written as escapes. This makes an accidental NFC
# normalization by an editor visible in review and preserves the test intent.
CORPUS: tuple[tuple[str, str, str, tuple[CorpusCase, ...]], ...] = (
    (
        "names",
        "名前",
        "氏名欄で使う一般的な漢字と、JIS外の異体字を分けて確認",
        (
            CorpusCase("name-common", "一般的な氏名", "山田太郎さん", "人名の基本的な漢字・ひらがな"),
            CorpusCase("name-repeated", "濁点と反復記号を含む氏名", "佐々木玲さん", "々と名の漢字を含む氏名"),
            CorpusCase("name-variant", "異体字を含む氏名", "髙橋美咲さん", "髙 U+9AD9 は標準の高とは別のコードポイント"),
            CorpusCase("name-extb", "BMP外の人名漢字", "𠮷野家で吉牛", "𠮷 U+20BB7 はBMP外で、JIS X 0208の対象外"),
        ),
    ),
    (
        "addresses",
        "住所",
        "郵便番号、都道府県、市区町村、丁目番地を含む住所表記",
        (
            CorpusCase("address-tokyo", "東京都の住所", "〒160-0023 東京都新宿区西新宿二丁目8番1号", "郵便記号と漢数字・算用数字の混在"),
            CorpusCase("address-osaka", "大阪府の住所", "大阪府大阪市北区梅田三丁目1番1号", "都道府県から番地までの連続した漢字"),
            CorpusCase("address-hokkaido", "北海道の住所", "北海道札幌市中央区北一条西2丁目3-4", "長い地名と算用数字の混在"),
            CorpusCase("address-variant", "異体字を含む住所", "京都市左京区𠮷田本町", "JIS X 0208外の𠮷を含む住所を確認"),
        ),
    ),
    (
        "prices",
        "価格",
        "円・通貨記号・桁区切り・小数・税込表記を含む価格欄",
        (
            CorpusCase("price-yen", "円価格", "価格：￥1,980（税込）", "全角記号・円記号・括弧・数字"),
            CorpusCase("price-tax", "税込みと値引き", "合計 12,345円（10％引き）", "桁区切りと全角パーセント"),
            CorpusCase("price-fullwidth", "全角数字の価格", "本体価格：１００円＋税", "全角数字と全角コロン・プラス"),
            CorpusCase("price-foreign", "外貨の価格", "＄19.99 / €18.50", "€ U+20AC と全角ドル記号を確認"),
        ),
    ),
    (
        "dates",
        "年月日・時刻",
        "和暦・西暦・曜日・期間・締切を含む日付表記",
        (
            CorpusCase("date-weekday", "曜日付きの日付", "2026年9月12日（土）", "年月日と曜日の括弧"),
            CorpusCase("date-era", "和暦の月", "令和8年9月", "元号の漢字"),
            CorpusCase("date-time", "ISO風の日時", "2026-09-13 16:30", "数字・ハイフン・コロン・空白"),
            CorpusCase("date-deadline", "締切と期間", "締切：9月30日 / 2026/09/13〜2026/09/30", "波ダッシュ・スラッシュを含む"),
        ),
    ),
    (
        "daily",
        "日常文章",
        "実際の見出し・本文で使う短文。句読点と助詞を含む",
        (
            CorpusCase("daily-cat", "猫の一日", "今日は猫とお昼寝をしました。", "既存見本に近い猫・暮らしの文章"),
            CorpusCase("daily-greeting", "あいさつ", "おはようございます。よろしくお願いします。", "日常的な定型文"),
            CorpusCase("daily-meeting", "予定", "明日の朝、駅で待ち合わせ。", "日常の予定を表す短文"),
            CorpusCase("daily-font", "フォントの説明", "にくきゅう丸で楽しく文字を組みます。", "フォント名を含む日本語文章"),
            CorpusCase("daily-weather", "誘い文句", "天気がよければ公園へ行きましょう！", "促音・句読点・感嘆符"),
        ),
    ),
    (
        "symbols",
        "記号",
        "日本語組版で遭遇する全角記号、矢印、音符、装飾記号",
        (
            CorpusCase("symbol-japanese", "日本語組版記号", "！？＠＃＄％＆＊＋＝／：；。、・「」『』【】〈〉《》〔〕［］｛｝（）", "括弧類と全角記号をまとめて確認"),
            CorpusCase("symbol-dots", "点とダッシュ", "…‥〜ー―—－×÷±°￥", "点・波ダッシュ・長音・ダッシュ・演算記号"),
            CorpusCase("symbol-decorative", "装飾記号", "矢印←↑→↓ / 音符♪ / ハート♡♥ / 星★☆", "既存見本の装飾文字を含む"),
            CorpusCase("symbol-extended", "拡張記号", "© ® ™ § ± × ÷ ≠ ≤ ≥", "著作権・商標・演算記号の対応と形を確認"),
        ),
    ),
    (
        "halfwidth-kana",
        "半角カナ",
        "半角カタカナ、濁点・半濁点、半角句読点を全角代替と分けて確認",
        (
            CorpusCase("halfwidth-basic", "半角カナの文章", "ｶﾀｶﾅ ﾃｽﾄ ｼﾞｭｰｽ", "半角カナと半角スペース"),
            CorpusCase("halfwidth-voiced", "半角濁点・半濁点", "ｱｲｳｴｵ ｶﾞｷﾞｸﾞｹﾞｺﾞ ﾊﾟﾋﾟﾌﾟﾍﾟﾎﾟ", "半角カナの濁点・半濁点"),
            CorpusCase("halfwidth-punctuation", "半角カナ記号", "｡､･｢｣ 半角ｶﾅﾞﾟと全角カナ", "U+FF61–U+FF65 と U+FF9E/U+FF9F"),
        ),
    ),
    (
        "decomposed-dakuten",
        "分解濁点",
        "U+3099/U+309Aを含むNFD文字列と、NFCへ正規化した表示を比較",
        (
            CorpusCase("decomposed-voiced", "分解濁点のかな", "か\u3099き\u3099く\u3099け\u3099こ\u3099", "かな本体と結合濁点U+3099"),
            CorpusCase("decomposed-semi", "分解半濁点のかな", "は\u309Aひ\u309Aふ\u309Aへ\u309Aほ\u309A", "かな本体と結合半濁点U+309A"),
            CorpusCase("decomposed-mixed", "分解と合成の比較", "う\u3099ゔ / か\u3099き\u3099", "rawは結合マーク、NFCは合成済み文字として検査"),
        ),
    ),
)


REFERENCE_CASES: tuple[CorpusCase, ...] = (
    CorpusCase(
        "reference-kanji",
        "見本比較用の漢字",
        "猫 肉 球 暮 丸 日 月 春 夏 秋 冬 花 空 小 大 幸 色 白 黒 茶 店 休 中",
        "採用見本と既存スペシメンに登場する漢字",
    ),
    CorpusCase(
        "reference-hiragana",
        "見本比較用のひらがな",
        "ねこのいる 暮らし にくきゅう丸 にゃんこ",
        "採用見本のひらがな見出し",
    ),
    CorpusCase(
        "reference-katakana",
        "見本比較用のカタカナ",
        "ニクキュウマル ネコとおひるね",
        "カタカナの見出しと本文の比較",
    ),
)


def cp_name(cp: int) -> str:
    """Return a stable codepoint label suitable for JSON and HTML."""

    return f"U+{cp:04X} {unicodedata.name(chr(cp), 'UNNAMED')}"


def cp_short(cp: int) -> str:
    return f"U+{cp:04X}"


def unique_codepoints(text: str) -> list[int]:
    return sorted({ord(ch) for ch in text})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object without making a stale optional report fatal."""

    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _selected_base_name() -> str | None:
    """Return the CJK base selected by ``sources/design.json``."""

    value = _read_json_object(DESIGN_CONFIG).get("kanji_base")
    return value.strip() if isinstance(value, str) and value.strip() else None


def find_source_font() -> Path | None:
    """Find the CJK source selected by the current build configuration.

    ``build.py`` also loads Mochiy in ``finish_japanese_sources``.  Parsing the
    first generic ``base=TTFont`` assignment therefore reports the wrong
    source after the CJK base is switched to Zen Maru.  The design setting is
    authoritative; the ``cjk_base`` expression is retained for older configs
    that do not yet have ``kanji_base``.
    """

    selected = _selected_base_name()
    if selected is not None:
        candidate = BASE_FONT_PATHS.get(selected)
        # A configured source must not silently fall back to another font.
        return candidate if candidate is not None and candidate.exists() else None

    build_path = ROOT / "build.py"
    if build_path.exists():
        source = build_path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"cjk_base\s*=\s*TTFont\(ROOT\s*/\s*['\"]([^'\"]+)['\"]\)", source)
        if match:
            candidate = ROOT / match.group(1)
            if candidate.exists():
                return candidate
        # Older build scripts had no separate CJK variable and used Mochiy.
        match = re.search(r"base\s*=\s*TTFont\(ROOT\s*/\s*['\"]([^'\"]+)['\"]\)", source)
        if match:
            candidate = ROOT / match.group(1)
            if candidate.exists():
                return candidate
    for candidate in BASE_FONT_PATHS.values():
        if candidate.exists():
            return candidate
    return None


def _source_font_name(source_path: Path | None = None) -> str | None:
    """Return the configured source label, or infer it from a vendor path."""

    selected = _selected_base_name()
    if selected:
        return selected
    if source_path is not None:
        resolved = source_path.resolve()
        for name, path in BASE_FONT_PATHS.items():
            if path.resolve() == resolved:
                return name
    return None


def _read_modifications() -> dict[str, list[str]]:
    """Load per-glyph provenance tags emitted by ``build.py``."""

    raw = _read_json_object(MODIFICATIONS_FILE)
    result: dict[str, list[str]] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, list):
            continue
        result[key] = [tag for tag in value if isinstance(tag, str)]
    return result


def _modification_codepoint(key: str) -> int | None:
    """Map a modification key such as ``こ.alt`` to its Unicode scalar."""

    character = key.split(".", 1)[0]
    return ord(character) if len(character) == 1 else None


def _tagged_codepoints(modifications: dict[str, list[str]], tag: str) -> set[int]:
    codepoints: set[int] = set()
    for key, tags in modifications.items():
        if tag not in tags:
            continue
        codepoint = _modification_codepoint(key)
        if codepoint is not None:
            codepoints.add(codepoint)
    return codepoints


def _reference_vector_records(modifications: dict[str, list[str]]) -> list[dict[str, Any]]:
    """Describe intentional reference-vector overrides by Unicode scalar."""

    grouped: dict[int, set[str]] = {}
    for key, tags in modifications.items():
        codepoint = _modification_codepoint(key)
        if codepoint is None:
            continue
        selected = set(tags) & REFERENCE_VECTOR_TAGS
        if selected:
            grouped.setdefault(codepoint, set()).update(selected)
    return [
        {
            "codepoint": codepoint,
            "character": chr(codepoint),
            "tags": sorted(tags),
            "intentional_design_difference": True,
        }
        for codepoint, tags in sorted(grouped.items())
    ]


def _reference_vector_tag_counts(modifications: dict[str, list[str]]) -> dict[str, int]:
    """Count tagged source keys, retaining ``.alt`` entries as separate keys."""

    return {
        tag: sum(tag in tags for tags in modifications.values())
        for tag in sorted(REFERENCE_VECTOR_TAGS)
    }


def _unicode_cjk_codepoints(cmap: dict[int, str]) -> set[int]:
    """Best-effort CJK scope for old reports without provenance tags."""

    return {
        codepoint
        for codepoint in cmap
        if (
            0x3400 <= codepoint <= 0x4DBF
            or 0x4E00 <= codepoint <= 0x9FFF
            or 0xF900 <= codepoint <= 0xFAFF
            or 0x20000 <= codepoint <= 0x323AF
        )
    }


def outline_comparison_scope(
    generated_cmap: dict[int, str],
    source_name: str | None,
    modifications: dict[str, list[str]],
    reference_vectors: list[dict[str, Any]],
    reference_vector_tag_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Choose only glyphs whose generated source is the selected CJK base."""

    selected_tag = f"base:{source_name}" if source_name else None
    reference_codepoints = {item["codepoint"] for item in reference_vectors}
    base_tags = {
        tag
        for tags in modifications.values()
        for tag in tags
        if tag.startswith("base:")
    }
    if selected_tag and selected_tag in base_tags:
        eligible = _tagged_codepoints(modifications, selected_tag)
        mode = "modifications-base-tag"
        note = (
            f"sources/modifications.json の {selected_tag} を持つ生成文字だけを、"
            f"{source_name} の元書体と比較する。"
        )
    elif base_tags:
        # A mismatched/stale provenance file is evidence of an invalid scope;
        # do not compare glyphs against a different base just to fill a table.
        eligible = set()
        mode = "base-tag-mismatch"
        note = (
            f"選択された {selected_tag or 'base tag'} が modifications.json にないため、"
            "別の基準フォントとの推測比較を実施していない。"
        )
    else:
        eligible = _unicode_cjk_codepoints(generated_cmap)
        mode = "unicode-cjk-fallback"
        note = (
            "modifications.json に base:* の provenance がないため、"
            "旧形式互換としてUnicode CJK範囲だけを比較対象にした。"
        )
    excluded = eligible & reference_codepoints
    eligible -= reference_codepoints
    return {
        "mode": mode,
        "source_font_name": source_name,
        "source_tag": selected_tag,
        # Internal input to compare_outlines; it is removed from the JSON
        # report below because the per-glyph structure already carries the
        # detailed codepoint evidence.
        "eligible_codepoints": sorted(eligible),
        "eligible_codepoint_count": len(eligible),
        "reference_vector_codepoint_count": len(reference_vectors),
        "reference_vector_tag_counts": reference_vector_tag_counts or {},
        "excluded_reference_vector_codepoint_count": len(excluded),
        "excluded_reference_vector_codepoints": sorted(excluded),
        "reference_vector_characters": reference_vectors,
        "note": note,
        "reference_vector_note": (
            "concept-reference-vector-outline と approved-reference-vector-outline は、"
            "見本に合わせた意図的なベクトル差分として元書体ランキングから除外し、"
            "別のデザイン目視対象として扱う。"
        ),
    }


def _signed_area(points: Any) -> float:
    """Approximate a contour's direction from its on/off-curve points."""

    if len(points) < 3:
        return 0.0
    area = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        area += float(point[0]) * float(next_point[1])
        area -= float(next_point[0]) * float(point[1])
    return area / 2.0


def _outline_counts(font: TTFont, glyph_name: str) -> tuple[int, int]:
    """Return (contours, inferred counters) for simple or composite glyphs.

    TrueType uses clockwise outer contours and counter-clockwise hole contours
    in this font's y-up coordinate system. Positive signed area therefore
    counts holes and negative signed area counts exteriors. The estimate is
    used for a review ranking, never as a visual pass/fail assertion.
    """

    glyf = font["glyf"]
    glyph = glyf[glyph_name]
    try:
        coordinates, end_points, _ = glyph.getCoordinates(glyf)
    except (AttributeError, KeyError, TypeError, ValueError):
        return (0, 0)
    starts = 0
    areas: list[float] = []
    for end in end_points:
        points = coordinates[starts : int(end) + 1]
        areas.append(_signed_area(points))
        starts = int(end) + 1
    nonzero = [area for area in areas if abs(area) > 1e-6]
    positive = sum(area > 0 for area in nonzero)
    # Positive area is the CCW winding used by TrueType for counters/holes.
    return (len(end_points), positive)


def glyph_metrics(font: TTFont, codepoint: int, cmap: dict[int, str] | None = None) -> dict[str, Any] | None:
    """Collect bounds, advance, contour count, and counter estimate."""

    cmap = cmap if cmap is not None else font.getBestCmap()
    glyph_name = cmap.get(codepoint)
    if glyph_name is None:
        return None
    glyf = font["glyf"]
    glyph = glyf[glyph_name]
    try:
        glyph.recalcBounds(glyf)
    except (AttributeError, KeyError, TypeError, ValueError):
        pass
    advance = int(font["hmtx"].metrics[glyph_name][0])
    contours, counters = _outline_counts(font, glyph_name)
    bounds = None
    if contours and all(hasattr(glyph, attr) for attr in ("xMin", "yMin", "xMax", "yMax")):
        bounds = [int(glyph.xMin), int(glyph.yMin), int(glyph.xMax), int(glyph.yMax)]
    return {
        "codepoint": codepoint,
        "glyph": glyph_name,
        "advance": advance,
        "contours": contours,
        "counters_inferred": counters,
        "exteriors_inferred": max(0, contours - counters),
        "bounds": bounds,
    }


def all_cases() -> Iterable[tuple[str, str, str, CorpusCase]]:
    for group_id, group_title, group_note, cases in CORPUS:
        for case in cases:
            yield group_id, group_title, group_note, case
    for case in REFERENCE_CASES:
        yield "reference", "見本デザイン比較", "採用画像に近い漢字・かなを比較", case


def analyze_case(case: CorpusCase, cmap: dict[int, str]) -> dict[str, Any]:
    raw_codepoints = unique_codepoints(case.text)
    missing = [cp for cp in raw_codepoints if cp not in cmap]
    nfc_text = unicodedata.normalize("NFC", case.text)
    nfc_codepoints = unique_codepoints(nfc_text)
    nfc_missing = [cp for cp in nfc_codepoints if cp not in cmap]
    mapped_count = len(raw_codepoints) - len(missing)
    if not missing:
        status = "pass"
    elif nfc_text != case.text and not nfc_missing:
        status = "missing-raw-only"
    elif mapped_count:
        status = "partial"
    else:
        status = "missing"
    return {
        "key": case.key,
        "title": case.title,
        "text": case.text,
        "note": case.note,
        "codepoints": raw_codepoints,
        "missing_codepoints": missing,
        "nfc_text": nfc_text,
        "nfc_changed": nfc_text != case.text,
        "nfc_codepoints": nfc_codepoints,
        "nfc_missing_codepoints": nfc_missing,
        "mapped_codepoint_count": mapped_count,
        "status": status,
    }


def inspect_structure(font: TTFont, cmap: dict[int, str], codepoints: Iterable[int]) -> dict[str, Any]:
    """Check generated metrics for every mapped codepoint.

    The corpus is deliberately small and use-focused, but bounds and contour
    checks must cover the full generated repertoire so a rare JIS glyph cannot
    disappear merely because it was absent from a sample sentence.
    """

    os2 = font["OS/2"]
    win_ascent = int(getattr(os2, "usWinAscent", 0))
    win_descent = int(getattr(os2, "usWinDescent", 0))
    metrics: list[dict[str, Any]] = []
    bounds_errors: list[dict[str, Any]] = []
    empty_mapped: list[int] = []
    for cp in sorted(set(codepoints)):
        item = glyph_metrics(font, cp, cmap)
        if item is None:
            continue
        item["codepoint_label"] = cp_name(cp)
        bounds = item["bounds"]
        if not item["contours"] and not chr(cp).isspace():
            empty_mapped.append(cp)
        if bounds is not None:
            x_min, y_min, x_max, y_max = bounds
            problems: list[str] = []
            if (x_min < 0 or x_max > item["advance"]) and cp not in POSITIONED_COMBINING_MARKS:
                problems.append("horizontal-overflow")
            if y_min < -win_descent or y_max > win_ascent:
                problems.append("vertical-overflow")
            if x_min > x_max or y_min > y_max:
                problems.append("inverted-bounds")
            if problems:
                bounds_errors.append(
                    {
                        "codepoint": cp,
                        "glyph": item["glyph"],
                        "bounds": bounds,
                        "advance": item["advance"],
                        "problems": problems,
                    }
                )
        metrics.append(item)
    return {
        "checked_codepoints": len(metrics),
        "checked_visible_codepoints": sum(not chr(item["codepoint"]).isspace() for item in metrics),
        "empty_mapped_codepoints": empty_mapped,
        "bounds_errors": bounds_errors,
        "bounds_limits": {
            "x_min": 0,
            "x_max": "advance",
            "y_min": -win_descent,
            "y_max": win_ascent,
            "positioned_zero_advance_marks": [cp_short(cp) for cp in sorted(POSITIONED_COMBINING_MARKS)],
        },
        "vertical_extrema": [
            min((item["bounds"][1] for item in metrics if item["bounds"] is not None), default=None),
            max((item["bounds"][3] for item in metrics if item["bounds"] is not None), default=None),
        ],
        "per_codepoint": metrics,
    }


def compare_outlines(
    source: TTFont | None,
    generated: TTFont,
    generated_cmap: dict[int, str],
    source_path: Path | None = None,
    comparison_scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rank outline/counter reductions against the selected source for review.

    The scope is intentionally provenance-based.  A Zen-generated Kanji must
    be compared with Zen, while a reference-vector override is a deliberate
    design difference and must not be presented as a source-outline failure.
    """

    comparison_scope = comparison_scope or {}
    reference_codepoints = set(comparison_scope.get("excluded_reference_vector_codepoints", ()))
    eligible_codepoints = comparison_scope.get("eligible_codepoints")
    if eligible_codepoints is not None:
        eligible_codepoints = set(eligible_codepoints)

    if source is None:
        return {
            "source_font": None,
            "source_font_name": comparison_scope.get("source_font_name"),
            "source_sha256": None,
            "common_codepoints": 0,
            "compared_codepoints": 0,
            "changed_codepoints": 0,
            "loss_codepoints": 0,
            "top_review_candidates": [],
            "comparison_scope": {
                key: value for key, value in comparison_scope.items() if key != "eligible_codepoints"
            },
            "note": "元書体が見つからないため比較を実施していない。"
            + (f" {comparison_scope.get('note')}" if comparison_scope.get("note") else ""),
        }
    source_cmap = source.getBestCmap()
    common_codepoints = set(generated_cmap) & set(source_cmap)
    if eligible_codepoints is not None:
        common_codepoints &= eligible_codepoints
    common_codepoints -= reference_codepoints
    records: list[dict[str, Any]] = []
    for cp in sorted(common_codepoints):
        before = glyph_metrics(source, cp, source_cmap)
        after = glyph_metrics(generated, cp, generated_cmap)
        if before is None or after is None:
            continue
        contour_loss = max(0, int(before["contours"]) - int(after["contours"]))
        counter_loss = max(0, int(before["counters_inferred"]) - int(after["counters_inferred"]))
        exterior_loss = max(0, int(before["exteriors_inferred"]) - int(after["exteriors_inferred"]))
        contour_delta = int(after["contours"]) - int(before["contours"])
        counter_delta = int(after["counters_inferred"]) - int(before["counters_inferred"])
        exterior_delta = int(after["exteriors_inferred"]) - int(before["exteriors_inferred"])
        # The score only prioritizes inspection. It never labels a glyph FAIL.
        score = exterior_loss * 4 + counter_loss * 4
        if contour_loss or counter_loss or exterior_loss:
            records.append(
                {
                    "codepoint": cp,
                    "character": chr(cp),
                    "codepoint_label": cp_name(cp),
                    "source": {
                        "glyph": before["glyph"],
                        "contours": before["contours"],
                        "counters_inferred": before["counters_inferred"],
                        "exteriors_inferred": before["exteriors_inferred"],
                        "bounds": before["bounds"],
                    },
                    "generated": {
                        "glyph": after["glyph"],
                        "contours": after["contours"],
                        "counters_inferred": after["counters_inferred"],
                        "exteriors_inferred": after["exteriors_inferred"],
                        "bounds": after["bounds"],
                    },
                    "contour_delta": contour_delta,
                    "counter_delta": counter_delta,
                    "exterior_delta": exterior_delta,
                    "contour_loss": contour_loss,
                    "counter_loss": counter_loss,
                    "exterior_loss": exterior_loss,
                    "priority_score": score,
                    "review_only": True,
                }
            )
    records.sort(key=lambda item: (-item["priority_score"], -item["contour_loss"], -item["counter_loss"], item["codepoint"]))
    return {
        "source_font": (
            str(source_path.relative_to(ROOT)).replace("\\", "/")
            if source_path is not None
            else "unknown"
        ),
        "source_font_name": comparison_scope.get("source_font_name"),
        "source_sha256": sha256(source_path) if source_path is not None else None,
        "common_codepoints": len(set(generated_cmap) & set(source_cmap)),
        "compared_codepoints": len(common_codepoints),
        "changed_codepoints": len(records),
        "loss_codepoints": len(records),
        "top_review_candidates": records[:80],
        "comparison_scope": {
            key: value for key, value in comparison_scope.items() if key != "eligible_codepoints"
        },
        "note": (
            "輪郭・推定カウンターの減少順。装飾差も含むため目視候補であり自動FAILではない。"
            + (f" {comparison_scope.get('note')}" if comparison_scope.get("note") else "")
        ),
    }


def status_label(status: str) -> str:
    return {
        "pass": "対応",
        "partial": "一部未収録",
        "missing": "未収録",
        "missing-raw-only": "分解形は未収録 / NFC代替あり",
    }.get(status, status)


def status_class(status: str) -> str:
    return {
        "pass": "ok",
        "partial": "warn",
        "missing": "bad",
        "missing-raw-only": "warn",
    }.get(status, "warn")


def render_codepoint_list(codepoints: Iterable[int], *, missing: set[int] | None = None) -> str:
    missing = missing or set()
    chunks = []
    for cp in codepoints:
        cls = " missing-codepoint" if cp in missing else ""
        title = html.escape(cp_name(cp), quote=True)
        chunks.append(f'<code class="codepoint{cls}" title="{title}">{cp_short(cp)}</code>')
    return " ".join(chunks) or '<span class="muted">なし</span>'


def render_text(text: str, cmap: dict[int, str]) -> str:
    """Render each scalar as a tooltip-bearing span for screenshot inspection."""

    chunks = []
    for character in text:
        cp = ord(character)
        supported = cp in cmap
        classes = ["char", "supported" if supported else "missing"]
        if character.isspace():
            classes.append("space")
        title = f"{cp_name(cp)} / {'対応' if supported else '未収録'}"
        value = html.escape(character)
        if character == " ":
            value = "&nbsp;"
        chunks.append(
            f'<span class="{" ".join(classes)}" data-codepoint="{cp_short(cp)}" title="{html.escape(title, quote=True)}">{value}</span>'
        )
    return "".join(chunks)


def _case_html(result: dict[str, Any], cmap: dict[int, str]) -> str:
    missing = set(result["missing_codepoints"])
    missing_text = render_codepoint_list(result["missing_codepoints"], missing=missing)
    nfc_block = ""
    if result["nfc_changed"]:
        nfc_missing = set(result["nfc_missing_codepoints"])
        nfc_block = f'''
          <div class="sample-label">NFC正規化後 <span class="normalization-note">結合マークを合成済み文字へ変換した比較</span></div>
          <div class="sample sample-nfc">{render_text(result["nfc_text"], cmap)}</div>
          <div class="codepoints"><span class="label">NFC:</span> {render_codepoint_list(result["nfc_codepoints"], missing=nfc_missing)}</div>
          <div class="codepoints"><span class="label">NFC未収録:</span> {render_codepoint_list(result["nfc_missing_codepoints"], missing=nfc_missing)}</div>
        '''
    return f'''
      <article class="case {status_class(result["status"])}">
        <div class="case-heading"><h3>{html.escape(result["title"])}</h3><span class="badge">{status_label(result["status"])}</span></div>
        <p class="case-note">{html.escape(result["note"])}</p>
        <div class="sample-label">入力文字列（raw）</div>
        <div class="sample">{render_text(result["text"], cmap)}</div>
        <div class="codepoints"><span class="label">コードポイント:</span> {render_codepoint_list(result["codepoints"], missing=missing)}</div>
        <div class="codepoints"><span class="label">未収録:</span> {missing_text}</div>
        {nfc_block}
      </article>
    '''


def _summary_cards(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    structure = report["structure"]
    cards = (
        ("フォント対応", f'{coverage["font_unicode_count"]:,}', "TTF cmapのUnicode数"),
        ("コーパス固有文字", f'{coverage["corpus_unique_codepoint_count"]:,}', "用途別＋見本比較"),
        ("コーパス対応", f'{coverage["corpus_supported_codepoint_count"]:,}', "cmapに存在する文字"),
        ("未収録", f'{coverage["corpus_missing_codepoint_count"]:,}', "隠さず用途別に表示"),
        ("bounds異常", f'{len(structure["bounds_errors"]):,}', "自動構造検査"),
        ("空輪郭", f'{len(structure["empty_mapped_codepoints"]):,}', "空白以外の対応文字"),
    )
    return "".join(
        f'<div class="summary-card"><strong>{html.escape(value)}</strong><span>{html.escape(title)}</span><small>{html.escape(note)}</small></div>'
        for title, value, note in cards
    )


def _category_html(category_results: list[dict[str, Any]], cmap: dict[int, str]) -> str:
    blocks = []
    for category in category_results:
        cases = "".join(_case_html(case, cmap) for case in category["cases"])
        blocks.append(
            f'''
            <section class="category" id="{html.escape(category["id"])}">
              <div class="category-heading"><div><p class="eyebrow">USE CASE</p><h2>{html.escape(category["title"])}</h2></div><span class="category-count">{category["supported_case_count"]}/{category["case_count"]} ケース完全対応</span></div>
              <p class="category-note">{html.escape(category["note"])}</p>
              <div class="cases">{cases}</div>
            </section>
            '''
        )
    return "".join(blocks)


def _reference_html(cmap: dict[int, str]) -> str:
    cases = "".join(_case_html(analyze_case(case, cmap), cmap) for case in REFERENCE_CASES)
    return f'''
      <section class="category reference" id="reference">
        <div class="category-heading"><div><p class="eyebrow">DESIGN REFERENCE</p><h2>見本とのデザイン比較</h2></div><span class="category-count">画像＋漢字・かな</span></div>
        <p class="category-note">採用画像を隣に置き、見本由来の丸みと実フォントの漢字・かなを同じ画面で比較する。ここでの一致は構造検査の合格を意味しない。</p>
        <div class="reference-layout">
          <figure><img src="../references/01-nikukyu.png" alt="採用されたにくきゅう丸の元見本"><figcaption>references/01-nikukyu.png</figcaption></figure>
          <div class="reference-copy">
            <div class="reference-swatch"><div class="sample reference-large">ねこのいる<br>暮らし</div><div class="sample reference-medium">にくきゅう丸　猫 肉 球 暮 丸</div><div class="sample reference-small">あいうえお　アイウエオ　春 夏 秋 冬</div></div>
            <p>色・猫耳・肉球の印象は目視で記録し、輪郭数やboundsの数値とは別に扱う。</p>
          </div>
        </div>
        <div class="cases">{cases}</div>
      </section>
    '''


def _candidate_html(
    candidates: list[dict[str, Any]], outline: dict[str, Any] | None = None
) -> str:
    outline = outline or {}
    scope = outline.get("comparison_scope") or {}
    scope_note = html.escape(str(scope.get("note", "")))
    reference_note = html.escape(str(scope.get("reference_vector_note", "")))
    scope_details = "".join(
        part
        for part in (
            f'<p class="footnote">{scope_note}</p>' if scope_note else "",
            f'<p class="footnote">{reference_note}</p>' if reference_note else "",
        )
    )
    if not candidates:
        return (
            '<p class="muted">元書体との比較で輪郭・推定カウンターの減少はありません。</p>'
            + scope_details
        )
    rows = []
    for item in candidates[:30]:
        source = item["source"]
        generated = item["generated"]
        rows.append(
            f'''<tr><td class="candidate-char">{html.escape(item["character"])}</td><td><code>{cp_short(item["codepoint"])}</code></td><td>{source["exteriors_inferred"]} / {source["counters_inferred"]}</td><td>{generated["exteriors_inferred"]} / {generated["counters_inferred"]}</td><td><strong>{item["exterior_loss"]}</strong> / <strong>{item["counter_loss"]}</strong></td><td>{item["priority_score"]}</td></tr>'''
        )
    return f'''
      <table class="candidate-table"><thead><tr><th>字</th><th>コード</th><th>元: 外周 / 穴*</th><th>生成: 外周 / 穴*</th><th>減少: 外周 / 穴</th><th>優先度</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
      <p class="footnote">* 穴はTrueTypeの輪郭方向から推定。装飾や合成差を含むため、ランキングは目視確認の候補であり自動FAIL判定ではない。</p>
      {scope_details}
    '''


def write_outline_review_png(
    source_path: Path | None,
    generated_path: Path,
    candidates: list[dict[str, Any]],
    output_path: Path,
    limit: int = 30,
) -> dict[str, Any]:
    """Render source/generated glyph pairs for the highest-risk candidates."""

    from PIL import Image, ImageDraw, ImageFont

    output_path.parent.mkdir(parents=True, exist_ok=True)
    selected = candidates[:limit]
    if source_path is None or not selected:
        # Keep a valid, inspectable artifact even when no source font exists.
        image = Image.new("RGB", (1200, 180), "#fff8eb")
        draw = ImageDraw.Draw(image)
        label = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
        draw.text((36, 60), "No outline comparison candidates", font=label, fill="#342622")
        from artifact_io import save_png

        save_png(image, output_path)
        return {"path": str(output_path.relative_to(ROOT)).replace("\\", "/"), "candidate_count": 0}

    from artifact_io import save_png

    ink = "#342622"
    cream = "#fff8eb"
    line = "#e6d7c8"
    muted = "#806b60"
    source_fill = "#f4e6dc"
    generated_fill = "#e7f0e9"
    width = 1520
    header_height = 130
    row_height = 145
    image = Image.new("RGB", (width, header_height + row_height * len(selected) + 42), cream)
    draw = ImageDraw.Draw(image)
    ui_path = ROOT / "vendor" / "ZenMaruGothic-Black.ttf"
    ui = ImageFont.truetype(str(ui_path), 18)
    small = ImageFont.truetype(str(ui_path), 14)
    glyph_source = ImageFont.truetype(str(source_path), 104)
    glyph_generated = ImageFont.truetype(str(generated_path), 104)
    draw.text((34, 22), "NIKUKYU MARU / OUTLINE REVIEW", font=ui, fill=ink)
    draw.text(
        (34, 52),
        "元書体と生成後の実TTFを同じ大きさで比較。優先度順・目視候補。",
        font=small,
        fill=muted,
    )
    draw.text((620, 96), "元書体", font=small, fill=muted, anchor="mm")
    draw.text((1000, 96), "生成後", font=small, fill=muted, anchor="mm")
    draw.text((1322, 96), "外周 / 穴*", font=small, fill=muted, anchor="mm")
    for index, item in enumerate(selected, start=1):
        top = header_height + (index - 1) * row_height
        draw.rounded_rectangle((26, top, width - 26, top + row_height - 10), radius=12, fill="#fffdf9", outline=line, width=1)
        draw.rounded_rectangle((360, top + 17, 880, top + row_height - 28), radius=8, fill=source_fill)
        draw.rounded_rectangle((890, top + 17, 1190, top + row_height - 28), radius=8, fill=generated_fill)
        draw.text((50, top + 30), f"{index:02d}", font=ui, fill=muted)
        draw.text((180, top + 63), item["character"], font=glyph_generated, fill=ink, anchor="mm")
        draw.text((106, top + 104), cp_short(item["codepoint"]), font=small, fill=muted)
        draw.text((620, top + 70), item["character"], font=glyph_source, fill=ink, anchor="mm")
        draw.text((1000, top + 70), item["character"], font=glyph_generated, fill=ink, anchor="mm")
        source = item["source"]
        generated = item["generated"]
        draw.text((1215, top + 42), f"{source['exteriors_inferred']} / {source['counters_inferred']} →", font=small, fill=muted)
        draw.text((1345, top + 42), f"{generated['exteriors_inferred']} / {generated['counters_inferred']}", font=small, fill=ink)
        draw.text((1215, top + 75), f"減少 {item['exterior_loss']} / {item['counter_loss']}", font=small, fill="#a6302d")
        draw.text((1215, top + 106), f"score {item['priority_score']}", font=small, fill=muted)
    draw.text((34, image.height - 20), "* 穴は輪郭方向から推定。実際の潰れ・融合はブラウザー/画像で目視確認する。", font=small, fill=muted, anchor="lm")
    save_png(image, output_path)
    return {
        "path": str(output_path.relative_to(ROOT)).replace("\\", "/"),
        "candidate_count": len(selected),
        "source_font": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        "generated_font": str(generated_path.relative_to(ROOT)).replace("\\", "/"),
    }


def _webfont_url(report: dict[str, Any]) -> str:
    """Return a sibling WOFF2 URL with the report's content hash as a nonce."""

    artifact = report.get("artifacts", {}).get("woff2", {})
    path = artifact.get("path") if isinstance(artifact, dict) else None
    filename = Path(str(path or DEFAULT_WEBFONT.name)).name
    digest = artifact.get("sha256") if isinstance(artifact, dict) else None
    return f"{filename}?v={digest}" if isinstance(digest, str) and digest else filename


def render_outline_review_page(report: dict[str, Any]) -> str:
    """Create a focused page for image-based source/generated review."""

    outline = report["outline_comparison"]
    candidates = outline["top_review_candidates"]
    artifact = report["artifacts"].get("outline_review_png", {})
    image_href = Path(artifact.get("path", "japanese-outline-review.png")).name
    webfont_href = html.escape(_webfont_url(report), quote=True)
    scope = outline.get("comparison_scope") or {}
    source_name = html.escape(str(outline.get("source_font_name") or "不明"))
    scope_note = str(scope.get("note", ""))
    reference_note = str(scope.get("reference_vector_note", ""))
    reference_count = int(scope.get("reference_vector_codepoint_count", 0) or 0)
    rows = []
    for index, item in enumerate(candidates, start=1):
        source = item["source"]
        generated = item["generated"]
        rows.append(
            f'''<tr><td>{index}</td><td class="glyph">{html.escape(item["character"])}</td><td><code>{cp_short(item["codepoint"])}</code></td><td>{source["exteriors_inferred"]} / {source["counters_inferred"]}</td><td>{generated["exteriors_inferred"]} / {generated["counters_inferred"]}</td><td>{item["exterior_loss"]} / {item["counter_loss"]}</td><td>{item["priority_score"]}</td></tr>'''
        )
    table = "".join(rows) or '<tr><td colspan="7">候補なし</td></tr>'
    source = html.escape(outline.get("source_font") or "不明")
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>にくきゅう丸 輪郭候補比較</title>
<style>
  :root {{ --ink:#342622; --cream:#fff8eb; --paper:#fffdf9; --line:#e6d7c8; --muted:#806b60; }}
  @font-face {{ font-family:"NikuValidation"; src:url("{webfont_href}") format("woff2"); font-weight:800; font-style:normal; font-display:block; }}
  * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--cream); color:var(--ink); font:15px/1.6 system-ui,-apple-system,"Yu Gothic","Meiryo",sans-serif; }}
  .wrap {{ width:min(1500px,calc(100% - 40px)); margin:0 auto; }} header {{ padding:34px 0 20px; }}
  h1 {{ margin:0; font:800 clamp(28px,4vw,48px)/1.2 "NikuValidation",sans-serif; }} h2 {{ margin:28px 0 10px; font-size:22px; }}
  .meta, .note, .foot {{ color:var(--muted); font-size:12px; }} .note {{ background:#fff1e7; border-left:5px solid #ef927f; border-radius:10px; padding:12px 15px; }}
  .review-image {{ overflow:auto; border:1px solid var(--line); border-radius:14px; background:#fff; padding:10px; }} .review-image img {{ display:block; max-width:none; width:1520px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--paper); font-size:12px; }} th,td {{ padding:7px 8px; border-bottom:1px solid var(--line); text-align:left; white-space:nowrap; }} th {{ color:var(--muted); font-size:11px; }} .glyph {{ font:800 26px/1 "NikuValidation",sans-serif; }}
  .table-scroll {{ overflow:auto; border:1px solid var(--line); border-radius:10px; }} a {{ color:#96503e; }}
</style></head><body><div class="wrap">
  <header><p class="meta">NIKUKYU MARU / OUTLINE REVIEW</p><h1>元書体と生成後の輪郭比較</h1><p class="meta">元書体: <code>{source}</code> / 選択基準: {source_name} / 共通Unicode: {outline["common_codepoints"]:,} / 比較対象: {outline.get("compared_codepoints", 0):,} / 差分候補: {outline["changed_codepoints"]:,}</p></header>
  <p class="note">外周 / 穴はTrueType輪郭方向からの推定値。{html.escape(scope_note) if scope_note else "選択された基準フォントの比較対象を使う。"} {html.escape(reference_note) if reference_note else ""} 参照ベクトル別扱い: {reference_count} codepoints。装飾差を含むため、このランキングは自動FAILではなく目視確認の入口である。</p>
  <h2>画像比較</h2><div class="review-image"><img src="{html.escape(image_href)}" alt="元書体と生成後の上位輪郭候補比較"></div>
  <h2>候補一覧</h2><div class="table-scroll"><table><thead><tr><th>#</th><th>字</th><th>コード</th><th>元: 外周 / 穴</th><th>生成: 外周 / 穴</th><th>減少: 外周 / 穴</th><th>優先度</th></tr></thead><tbody>{table}</tbody></table></div>
  <p class="foot">メインの用途別検証: <a href="japanese-validation.html">japanese-validation.html</a> / JSON: <a href="japanese-validation.json">japanese-validation.json</a></p>
</div></body></html>'''


def render_html(report: dict[str, Any], category_results: list[dict[str, Any]], cmap: dict[int, str]) -> str:
    font_path = report["artifacts"]["ttf"]["path"]
    webfont_href = html.escape(_webfont_url(report), quote=True)
    version = report["font"]["version"]
    structure = report["structure"]
    coverage = report["coverage"]
    outline = report["outline_comparison"]
    generated = report["generated_at"]
    title = "にくきゅう丸 日本語用途別検証"
    failed_structure = bool(structure["bounds_errors"] or structure["empty_mapped_codepoints"] or not report["artifacts"]["ttf_woff2_cmap_match"])
    structure_label = "要確認" if failed_structure else "自動検査OK"
    structure_class = "bad" if failed_structure else "ok"
    browser_note = "このページをHTTPで開き、上のWebフォント表示と赤い未収録印を実Chromeで目視する。スクリーンショットによる目視結果はこのJSONのbrowser_evidenceには自動記録しない。"
    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    @font-face {{ font-family: "NikuValidation"; src: url("{webfont_href}") format("woff2"); font-weight: 800; font-style: normal; font-display: block; }}
    :root {{ --ink:#342622; --cream:#fff8eb; --paper:#fffdf9; --line:#e6d7c8; --muted:#806b60; --pink:#ef927f; --good:#2d7d63; --good-bg:#e4f3ec; --warn:#9a6500; --warn-bg:#fff0c8; --bad:#a6302d; --bad-bg:#ffe1dc; }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin:0; background:var(--cream); color:var(--ink); font:15px/1.6 system-ui, -apple-system, "Yu Gothic", "Meiryo", sans-serif; }}
    .wrap {{ width:min(1360px, calc(100% - 40px)); margin:0 auto; }}
    header.hero {{ padding:44px 0 30px; }}
    .hero-panel {{ background:var(--ink); color:var(--cream); border-radius:24px; padding:34px 38px; box-shadow:0 10px 30px #6d4b381c; }}
    .eyebrow {{ margin:0 0 5px; color:var(--pink); font-size:11px; font-weight:800; letter-spacing:.14em; }}
    h1 {{ margin:0; font:800 clamp(30px,4vw,54px)/1.15 "NikuValidation", sans-serif; letter-spacing:.02em; }}
    h2 {{ margin:0; font-size:28px; line-height:1.2; }}
    h3 {{ margin:0; font-size:18px; line-height:1.3; }}
    .hero-meta {{ display:flex; flex-wrap:wrap; gap:8px 20px; margin:18px 0 0; color:#ead9cb; font-size:13px; }}
    .hero-meta code, code {{ font:12px ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .hero-links {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:22px; }}
    .hero-links a {{ color:var(--cream); border:1px solid #ead9cb66; border-radius:999px; padding:6px 12px; text-decoration:none; }}
    .hero-links a:hover {{ background:#ffffff18; }}
    .summary {{ display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin:-2px 0 28px; }}
    .summary-card {{ background:var(--paper); border:1px solid var(--line); border-radius:15px; padding:14px; min-height:104px; display:flex; flex-direction:column; }}
    .summary-card strong {{ font-size:28px; line-height:1; }}
    .summary-card span {{ margin-top:8px; font-weight:800; }}
    .summary-card small {{ color:var(--muted); font-size:11px; }}
    .notice {{ border-left:5px solid var(--pink); background:#fff1e7; border-radius:12px; padding:13px 16px; margin-bottom:22px; }}
    .notice strong {{ display:block; margin-bottom:3px; }}
    .category {{ background:var(--paper); border:1px solid var(--line); border-radius:22px; padding:26px; margin:24px 0; scroll-margin-top:18px; }}
    .category-heading {{ display:flex; align-items:end; justify-content:space-between; gap:20px; border-bottom:1px solid var(--line); padding-bottom:14px; }}
    .category-count {{ color:var(--muted); font-size:12px; white-space:nowrap; }}
    .category-note {{ color:var(--muted); margin:14px 0 18px; }}
    .cases {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
    .case {{ min-width:0; border:1px solid var(--line); border-top:5px solid var(--muted); border-radius:14px; padding:16px; background:#fff; }}
    .case.ok {{ border-top-color:var(--good); }}
    .case.warn {{ border-top-color:var(--warn); }}
    .case.bad {{ border-top-color:var(--bad); }}
    .case-heading {{ display:flex; justify-content:space-between; align-items:start; gap:12px; }}
    .badge {{ border-radius:999px; font-size:11px; font-weight:800; padding:3px 8px; white-space:nowrap; background:var(--warn-bg); color:var(--warn); }}
    .ok .badge {{ background:var(--good-bg); color:var(--good); }}
    .bad .badge {{ background:var(--bad-bg); color:var(--bad); }}
    .case-note {{ color:var(--muted); font-size:12px; min-height:38px; margin:8px 0 12px; }}
    .sample-label, .label {{ color:var(--muted); font-size:11px; font-weight:800; letter-spacing:.03em; }}
    .sample {{ overflow-wrap:anywhere; padding:12px 11px; border-radius:10px; background:#fffaf3; font:800 clamp(24px,3.5vw,42px)/1.45 "NikuValidation", sans-serif; letter-spacing:.02em; }}
    .sample-nfc {{ background:#f4f8f1; }}
    .char {{ border-radius:4px; }}
    .char.missing {{ color:var(--bad); background:var(--bad-bg); text-decoration:underline wavy var(--bad); text-decoration-thickness:1px; }}
    .char.space {{ border-bottom:1px dotted #bda99c; }}
    .codepoints {{ margin-top:8px; color:var(--muted); font-size:11px; line-height:1.9; overflow-wrap:anywhere; }}
    .codepoint {{ display:inline-block; border:1px solid var(--line); border-radius:4px; padding:0 4px; margin:1px 1px; color:var(--ink); background:#fff; }}
    .codepoint.missing-codepoint {{ border-color:#efa89b; color:var(--bad); background:var(--bad-bg); }}
    .normalization-note {{ font-weight:400; margin-left:5px; }}
    .reference-layout {{ display:grid; grid-template-columns:minmax(240px, .85fr) minmax(0, 1.15fr); gap:20px; align-items:start; margin-bottom:18px; }}
    figure {{ margin:0; }}
    figure img {{ width:100%; max-height:430px; object-fit:contain; object-position:left top; border:1px solid var(--line); border-radius:12px; background:#f6e4d8; }}
    figcaption {{ color:var(--muted); font-size:11px; margin-top:5px; }}
    .reference-swatch {{ border:1px solid var(--line); border-radius:14px; padding:20px; background:#f9eee4; }}
    .reference-large {{ font-size:clamp(35px,5vw,72px); line-height:1.25; background:transparent; padding:0; }}
    .reference-medium {{ margin-top:15px; font-size:clamp(22px,3vw,40px); background:transparent; padding:0; }}
    .reference-small {{ margin-top:15px; font-size:clamp(17px,2vw,26px); background:transparent; padding:0; }}
    .reference-copy > p {{ color:var(--muted); font-size:12px; }}
    .structure-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.5fr); gap:20px; align-items:start; }}
    .metric-table, .candidate-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    .metric-table th, .metric-table td, .candidate-table th, .candidate-table td {{ border-bottom:1px solid var(--line); padding:7px 8px; text-align:left; vertical-align:top; }}
    .metric-table th, .candidate-table th {{ color:var(--muted); font-size:11px; font-weight:800; }}
    .candidate-table {{ background:#fff; }}
    .candidate-table th, .candidate-table td {{ white-space:nowrap; }}
    .candidate-char {{ font:800 24px/1 "NikuValidation", sans-serif; }}
    .footnote, .muted {{ color:var(--muted); font-size:11px; }}
    .scroll-table {{ overflow:auto; max-height:560px; border:1px solid var(--line); border-radius:10px; }}
    .scroll-table table {{ min-width:680px; }}
    footer {{ color:var(--muted); font-size:12px; padding:8px 0 46px; }}
    @media (max-width: 980px) {{ .summary {{ grid-template-columns:repeat(3,1fr); }} .reference-layout, .structure-grid {{ grid-template-columns:1fr; }} }}
    @media (max-width: 650px) {{ .wrap {{ width:min(100% - 22px,1360px); }} .hero-panel, .category {{ padding:19px; border-radius:17px; }} .summary {{ grid-template-columns:repeat(2,1fr); }} .cases {{ grid-template-columns:1fr; }} .category-heading {{ align-items:start; flex-direction:column; gap:8px; }} .category-count {{ white-space:normal; }} }}
    @media print {{ body {{ background:#fff; }} .hero-links {{ display:none; }} .category {{ break-inside:avoid; box-shadow:none; }} .case {{ break-inside:avoid; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <div class="hero-panel">
        <p class="eyebrow">NIKUKYU MARU / JAPANESE VALIDATION</p>
        <h1>{html.escape(title)}</h1>
        <div class="hero-meta"><span>font: <code>{html.escape(font_path)}</code></span><span>version: <code>{html.escape(version)}</code></span><span>生成: <code>{html.escape(generated)}</code></span><span id="webfont-status">Webフォント確認中…</span></div>
        <div class="hero-links"><a href="#reference">見本比較</a><a href="#names">名前</a><a href="#addresses">住所</a><a href="#prices">価格</a><a href="#dates">年月日</a><a href="#daily">日常文章</a><a href="#symbols">記号</a><a href="#halfwidth-kana">半角カナ</a><a href="#decomposed-dakuten">分解濁点</a><a href="#structure">構造検査</a><a href="japanese-outline-review.html">輪郭候補画像</a><a href="japanese-validation.json">JSON</a></div>
      </div>
    </header>
    <main>
      <div class="summary">{_summary_cards(report)}</div>
      <div class="notice"><strong>検査の境界</strong><span>{html.escape(browser_note)}</span><br><span>赤い文字・コード欄はTTF cmapにないコードポイント。ブラウザーのOSフォールバックが描画しても対応済みには数えない。</span></div>
      {_reference_html(cmap)}
      {_category_html(category_results, cmap)}
      <section class="category" id="structure">
        <div class="category-heading"><div><p class="eyebrow">AUTOMATED STRUCTURE CHECK</p><h2>構造検査</h2></div><span class="category-count {structure_class}">{html.escape(structure_label)}</span></div>
        <p class="category-note">対応範囲・輪郭bounds・推定カウンターはTTF/WOFF2から計測する。ブラウザーでの見た目、元見本との印象、行間の衝突はこの数値検査の合否に含めない。</p>
        <div class="structure-grid">
          <table class="metric-table"><tbody>
            <tr><th>TTF Unicode cmap</th><td>{coverage["font_unicode_count"]:,}</td></tr>
            <tr><th>TTF glyph order</th><td>{report["font"]["glyph_count"]:,}</td></tr>
            <tr><th>WOFF2 cmap一致</th><td>{"一致" if report["artifacts"]["ttf_woff2_cmap_match"] else "不一致"}</td></tr>
            <tr><th>全対応文字で計測</th><td>{structure["checked_codepoints"]:,} codepoints</td></tr>
            <tr><th>bounds異常</th><td>{len(structure["bounds_errors"]):,}</td></tr>
            <tr><th>空輪郭（空白除外）</th><td>{len(structure["empty_mapped_codepoints"]):,}</td></tr>
            <tr><th>vertical extrema</th><td>{html.escape(str(structure["vertical_extrema"]))}</td></tr>
          </tbody></table>
          <div><h3>元書体との差分 — 目視候補ランキング</h3><p class="muted">{html.escape(outline["note"])}</p><p class="muted"><a href="japanese-outline-review.html">元書体と生成後の実TTFを描画したPNGを開く →</a></p><div class="scroll-table">{_candidate_html(outline["top_review_candidates"], outline)}</div></div>
        </div>
        <details style="margin-top:18px"><summary>bounds異常と空輪郭の詳細</summary><pre>{html.escape(json.dumps({"bounds_errors": structure["bounds_errors"], "empty_mapped_codepoints": [cp_name(cp) for cp in structure["empty_mapped_codepoints"]]}, ensure_ascii=False, indent=2))}</pre></details>
      </section>
    </main>
    <footer>自動生成: japanese_validation.py / <a href="japanese-validation.json">機械可読レポート</a>。font: {html.escape(font_path)}。スクリーンショットによる目視判定は別記録。</footer>
  </div>
  <script>
    (async () => {{
      const label = document.getElementById("webfont-status");
      try {{
        await document.fonts.load('800 32px "NikuValidation"', 'にくきゅう丸 日本語');
        const loaded = document.fonts.check('800 32px "NikuValidation"');
        label.textContent = loaded ? "Webフォント読込OK / TTF cmap検査済み" : "Webフォント未確認";
        label.style.color = loaded ? "#a7e2c8" : "#ffd08a";
      }} catch (error) {{
        label.textContent = "Webフォント読込エラー / 詳細は開発者コンソール";
        label.style.color = "#ffb0a2";
      }}
    }})();
  </script>
</body>
</html>
'''


def build_report(
    font_path: Path,
    webfont_path: Path,
    outline_png_path: Path = DEFAULT_OUTLINE_REVIEW_PNG,
) -> tuple[dict[str, Any], str, str]:
    if not font_path.exists():
        raise FileNotFoundError(f"TTF not found: {font_path}")
    if not webfont_path.exists():
        raise FileNotFoundError(f"WOFF2 not found: {webfont_path}")
    generated = TTFont(font_path)
    webfont = TTFont(webfont_path)
    cmap = generated.getBestCmap()
    web_cmap = webfont.getBestCmap()

    case_results: dict[str, list[dict[str, Any]]] = {}
    category_results: list[dict[str, Any]] = []
    used_codepoints: set[int] = set()
    for group_id, group_title, group_note, cases in CORPUS:
        results = [analyze_case(case, cmap) for case in cases]
        case_results[group_id] = results
        for item in results:
            used_codepoints.update(item["codepoints"])
        category_results.append(
            {
                "id": group_id,
                "title": group_title,
                "note": group_note,
                "case_count": len(results),
                "supported_case_count": sum(item["status"] == "pass" for item in results),
                "cases": results,
            }
        )
    reference_results = [analyze_case(case, cmap) for case in REFERENCE_CASES]
    for item in reference_results:
        used_codepoints.update(item["codepoints"])

    all_requested = sorted(used_codepoints)
    missing = sorted(cp for cp in all_requested if cp not in cmap)
    # Bounds/counters are checked over the full generated cmap, independently
    # from the use-case corpus coverage calculated above.
    structure = inspect_structure(generated, cmap, cmap)
    source_path = find_source_font()
    source_name = _source_font_name(source_path)
    modifications = _read_modifications()
    reference_vectors = _reference_vector_records(modifications)
    comparison_scope = outline_comparison_scope(
        cmap,
        source_name,
        modifications,
        reference_vectors,
        _reference_vector_tag_counts(modifications),
    )
    source = TTFont(source_path) if source_path is not None else None
    outline_comparison = compare_outlines(
        source,
        generated,
        cmap,
        source_path,
        comparison_scope=comparison_scope,
    )
    outline_png = write_outline_review_png(
        source_path,
        font_path,
        outline_comparison["top_review_candidates"],
        outline_png_path,
    )
    ttf_woff2_match = cmap == web_cmap
    version = generated["name"].getDebugName(5) or generated["name"].getDebugName(4) or "unknown"
    # Strip the non-semantic label prefix from common name-table versions only
    # when it is present; retaining the original is useful evidence in JSON.
    report: dict[str, Any] = {
        "schema": "nikukyu-japanese-validation/1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": {
            "script": "japanese_validation.py",
            "command": "python -X utf8 japanese_validation.py",
        },
        "design_reference": {
            "image": str(REFERENCE_IMAGE.relative_to(ROOT)).replace("\\", "/"),
            "exists": REFERENCE_IMAGE.exists(),
            "sha256": sha256(REFERENCE_IMAGE) if REFERENCE_IMAGE.exists() else None,
        },
        "font": {
            "path": str(font_path.relative_to(ROOT)).replace("\\", "/"),
            "version": version,
            "units_per_em": int(generated["head"].unitsPerEm),
            "glyph_count": len(generated.getGlyphOrder()),
        },
        "artifacts": {
            "ttf": {"path": str(font_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(font_path)},
            "woff2": {"path": str(webfont_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(webfont_path)},
            "ttf_woff2_cmap_match": ttf_woff2_match,
            "outline_review_png": outline_png,
        },
        "coverage": {
            "font_unicode_count": len(cmap),
            "corpus_unique_codepoint_count": len(all_requested),
            "corpus_supported_codepoint_count": len(all_requested) - len(missing),
            "corpus_missing_codepoint_count": len(missing),
            "corpus_missing_codepoints": missing,
            "corpus_missing_labels": [cp_name(cp) for cp in missing],
            "category_order": [group_id for group_id, *_ in CORPUS] + ["reference"],
        },
        "category_summary": [
            {
                "id": category["id"],
                "title": category["title"],
                "case_count": category["case_count"],
                "fully_supported_case_count": category["supported_case_count"],
                "status": "pass" if category["supported_case_count"] == category["case_count"] else "review",
                "missing_codepoints": sorted(
                    {
                        cp
                        for case in category["cases"]
                        for cp in case["missing_codepoints"]
                    }
                ),
            }
            for category in category_results
        ]
        + [
            {
                "id": "reference",
                "title": "見本デザイン比較",
                "case_count": len(reference_results),
                "fully_supported_case_count": sum(item["status"] == "pass" for item in reference_results),
                "status": "pass" if all(item["status"] == "pass" for item in reference_results) else "review",
                "missing_codepoints": sorted(
                    {
                        cp
                        for case in reference_results
                        for cp in case["missing_codepoints"]
                    }
                ),
            }
        ],
        "cases": case_results,
        "reference_cases": reference_results,
        "structure": structure,
        "outline_comparison": outline_comparison,
        "browser_evidence": {
            "page": "outputs/japanese-validation.html",
            "outline_review_page": "outputs/japanese-outline-review.html",
            "outline_review_png": outline_png.get("path"),
            "font_face": f"{webfont_path.name}?v={sha256(webfont_path)}",
            "status": "page-generated; この生成処理は目視判定を行わない。別記録 outputs/visual-verification.json の対象ハッシュと結果を参照。",
            "checks_to_record": [
                "Webフォント読込OKが表示されること",
                "赤い表示がTTF cmap未収録コードポイントと一致すること",
                "見本画像と漢字・かなの丸み、太さ、字間を比較すること",
                "半角カナと分解濁点が代替フォントで合格扱いされないこと",
                "構造検査のランキング上位字を拡大目視すること",
            ],
            "font_face_url": _webfont_url(
                {
                    "artifacts": {
                        "woff2": {
                            "path": str(webfont_path.relative_to(ROOT)).replace("\\", "/"),
                            "sha256": sha256(webfont_path),
                        }
                    }
                }
            ),
        },
    }
    return report, render_html(report, category_results, cmap), render_outline_review_page(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT, help="生成済みTTF")
    parser.add_argument("--webfont", type=Path, default=DEFAULT_WEBFONT, help="生成済みWOFF2")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="JSON出力先")
    parser.add_argument("--page", type=Path, default=DEFAULT_PAGE, help="HTML出力先")
    parser.add_argument("--outline-page", type=Path, default=DEFAULT_OUTLINE_REVIEW_PAGE, help="輪郭比較HTML出力先")
    parser.add_argument("--outline-png", type=Path, default=DEFAULT_OUTLINE_REVIEW_PNG, help="輪郭比較PNG出力先")
    args = parser.parse_args()
    report, page, outline_page = build_report(args.font.resolve(), args.webfont.resolve(), args.outline_png.resolve())
    args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.page.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.outline_page.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.report.resolve().write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.page.resolve().write_text(page, encoding="utf-8")
    args.outline_page.resolve().write_text(outline_page, encoding="utf-8")
    hard_errors = report["structure"]["bounds_errors"] or report["structure"]["empty_mapped_codepoints"] or not report["artifacts"]["ttf_woff2_cmap_match"]
    print(
        json.dumps(
            {
                "page": str(args.page.resolve().relative_to(ROOT)).replace("\\", "/"),
                "report": str(args.report.resolve().relative_to(ROOT)).replace("\\", "/"),
                "outline_page": str(args.outline_page.resolve().relative_to(ROOT)).replace("\\", "/"),
                "outline_png": str(args.outline_png.resolve().relative_to(ROOT)).replace("\\", "/"),
                "font_unicode_count": report["coverage"]["font_unicode_count"],
                "corpus_unique": report["coverage"]["corpus_unique_codepoint_count"],
                "corpus_missing": report["coverage"]["corpus_missing_codepoint_count"],
                "bounds_errors": len(report["structure"]["bounds_errors"]),
                "empty_mapped": len(report["structure"]["empty_mapped_codepoints"]),
                "ttf_woff2_cmap_match": report["artifacts"]["ttf_woff2_cmap_match"],
            },
            ensure_ascii=False,
        )
    )
    return 1 if hard_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
