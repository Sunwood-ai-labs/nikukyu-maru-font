"""Generate browser proofs for the 0.105 Latin cat concept outlines.

The reference artwork is kept intact.  Each card uses an overflow-hidden CSS
window to show the part of the original PNG described by ``reference_box``.
This makes the comparison reproducible while avoiding derived/cropped image
artifacts in the repository.
"""

from __future__ import annotations

import hashlib
import html
import json
import struct
import string
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "latin-concept-review"
OUTLINE_FILE = ROOT / "sources" / "latin-concept-outlines.json"
CONCEPT_IMAGE = ROOT / "references" / "04-latin-cat-concept.png"
FONT_FILE = ROOT / "outputs" / "NikukyuMaru-Regular.woff2"
FONT_FAMILY = "NikuConcept"
LETTERS = string.ascii_uppercase + string.ascii_lowercase
GLYPHS = LETTERS + "&"
FULLWIDTH_GLYPHS = "".join(chr(ord(char) + 0xFEE0) for char in GLYPHS)
IMAGE_SRC = "../../references/04-latin-cat-concept.png"
FONT_SRC = "../NikukyuMaru-Regular.woff2"


def sha256(path: Path) -> str:
    """Return the content digest used for both cache busting and the footer."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    """Read a PNG's dimensions without requiring an image-processing package."""

    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Not a PNG with an IHDR header: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if not width or not height:
        raise ValueError(f"PNG has an invalid size: {path}")
    return width, height


def number(value: Any, field: str) -> float:
    """Convert a numeric outline field and produce a useful validation error."""

    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric, got {value!r}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric, got {value!r}") from exc
    if result != result or result in (float("inf"), float("-inf")):
        raise ValueError(f"{field} must be finite, got {value!r}")
    return result


def css_number(value: float) -> str:
    """Format a CSS length compactly while retaining sub-pixel precision."""

    return f"{value:.3f}".rstrip("0").rstrip(".") or "0"


def load_outlines() -> dict[str, dict[str, Any]]:
    """Load and validate the concept trace's per-character records."""

    if not OUTLINE_FILE.is_file():
        raise FileNotFoundError(
            f"Missing {OUTLINE_FILE}; run trace_latin_concept.py before this generator."
        )
    raw = json.loads(OUTLINE_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("latin-concept-outlines.json must contain an object")

    expected = set(GLYPHS)
    actual = set(raw)
    missing = "".join(char for char in GLYPHS if char not in actual)
    extra = "".join(sorted(actual - expected))
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing={missing!r}")
        if extra:
            details.append(f"extra={extra!r}")
        raise ValueError("Concept outline key set must contain exactly ASCII A-Z/a-z: " + ", ".join(details))

    outlines: dict[str, dict[str, Any]] = {}
    for char in GLYPHS:
        record = raw[char]
        if not isinstance(record, dict):
            raise ValueError(f"Outline record for {char!r} must be an object")
        if not isinstance(record.get("commands"), list):
            raise ValueError(f"Outline record for {char!r} needs a commands list")
        box = record.get("reference_box")
        if not isinstance(box, list) or len(box) != 4:
            raise ValueError(f"Outline record for {char!r} needs reference_box=[x0,y0,x1,y1]")
        x0, y0, x1, y1 = (number(value, f"{char}.reference_box[{index}]") for index, value in enumerate(box))
        scale = number(record.get("scale"), f"{char}.scale")
        if scale <= 0:
            raise ValueError(f"{char}.scale must be greater than zero")
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"{char}.reference_box must have positive dimensions")
        if "baseline" not in record:
            raise ValueError(f"Outline record for {char!r} needs baseline: originalY")
        outlines[char] = {
            "width": record.get("width"),
            "commands": record["commands"],
            "reference_box": (x0, y0, x1, y1),
            "scale": scale,
            "baseline": record["baseline"],
        }
    return outlines


def source_window(char: str, record: dict[str, Any], image_size: tuple[int, int]) -> str:
    """Build a CSS-only view of the character's box in the source PNG."""

    image_width, image_height = image_size
    x0, y0, x1, y1 = record["reference_box"]
    scale = record["scale"]
    # reference_box is in the original PNG's pixel coordinate system.  The
    # traced commands are those pixels multiplied by ``scale``; keep the
    # source image at native pixels and use 1000/scale CSS px for the font so
    # both sides represent the same outline scale.
    box_width = x1 - x0
    box_height = y1 - y0
    image_css_width = float(image_width)
    image_css_height = float(image_height)
    left = -x0
    top = -y0
    baseline = html.escape(str(record["baseline"]), quote=True)
    title = html.escape(f"生成見本 {char}", quote=True)
    return (
        f'<div class="source-window" data-scale="{css_number(scale)}" '
        f'data-baseline="{baseline}" '
        f'style="--box-w:{css_number(box_width)}px;--box-h:{css_number(box_height)}px">'
        f'<img src="{IMAGE_SRC}" alt="{title}" draggable="false" '
        f'style="width:{css_number(image_css_width)}px;height:{css_number(image_css_height)}px;'
        f'left:{css_number(left)}px;top:{css_number(top)}px">'
        "</div>"
    )


def card(char: str, record: dict[str, Any], image_size: tuple[int, int]) -> str:
    """Build one source-versus-font comparison card."""

    escaped_char = html.escape(char)
    codepoint = f"U+{ord(char):04X}"
    x0, y0, x1, y1 = record["reference_box"]
    scale = record["scale"]
    box_height = (y1 - y0) / scale
    # The source crop is native PNG pixels.  The font uses the same
    # outline-unit-to-CSS-pixel relationship (1000 units per em).
    font_size = 1000.0 / scale
    baseline = html.escape(str(record["baseline"]), quote=True)
    width = html.escape(str(record["width"]), quote=True)
    return f"""
      <article class="card" data-char="{escaped_char}" data-codepoint="{codepoint}"
               data-scale="{css_number(scale)}" data-baseline="{baseline}">
        <header class="card-header">
          <strong>{escaped_char}</strong>
          <span>{codepoint}</span>
        </header>
        <div class="comparison">
          <section class="side">
            <div class="side-label">生成見本</div>
            <div class="stage source-stage">{source_window(char, record, image_size)}</div>
          </section>
          <section class="side">
            <div class="side-label">実フォント</div>
            <div class="stage font-stage" style="--font-size:{css_number(font_size)}px;--source-h:{css_number(box_height)}px">
              <span class="font-glyph">{escaped_char}</span>
            </div>
          </section>
        </div>
        <div class="record-meta">scale={css_number(scale)} · baseline originalY={baseline} · width={width}</div>
      </article>
    """


def base_style(digest: str) -> str:
    """Return common CSS with a digest-busted WOFF2 URL."""

    font_url = f"{FONT_SRC}?sha256={digest}"
    return f"""
      @font-face {{
        font-family: '{FONT_FAMILY}';
        src: url('{font_url}') format('woff2');
        font-display: block;
      }}
      :root {{
        --paper: #fff8eb;
        --ink: #342622;
        --muted: #806b60;
        --line: #ead7c7;
        --panel: #fffdf9;
        --accent: #f3decd;
      }}
      *, *::before, *::after {{ box-sizing: border-box; }}
      html, body {{ min-height: 100%; }}
      body {{
        margin: 0;
        padding: 18px 22px 14px;
        color: var(--ink);
        background: var(--paper);
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      }}
      h1 {{ margin: 0; font-size: 24px; line-height: 1.2; letter-spacing: .01em; }}
      .intro {{ margin: 4px 0 11px; color: var(--muted); font-size: 13px; line-height: 1.35; }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        grid-template-rows: repeat(2, minmax(0, 1fr));
        gap: 11px;
        height: 610px;
      }}
      .card {{
        min-width: 0;
        min-height: 0;
        overflow: hidden;
        padding: 10px 10px 8px;
        border: 1px solid var(--line);
        border-radius: 15px;
        background: #fff;
        box-shadow: 0 2px 6px rgb(97 64 40 / 7%);
      }}
      .card-header {{
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 5px;
        height: 28px;
        color: var(--muted);
        font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
        font-size: 11px;
      }}
      .card-header strong {{
        color: var(--ink);
        font-family: '{FONT_FAMILY}', sans-serif;
        font-size: 27px;
        line-height: 1;
      }}
      .comparison {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        gap: 8px;
        height: 235px;
      }}
      .side {{ min-width: 0; display: flex; flex-direction: column; }}
      .side-label {{
        height: 19px;
        color: var(--muted);
        font-size: 11px;
        line-height: 19px;
        text-align: center;
      }}
      .stage {{
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 0;
        height: 216px;
        overflow: hidden;
        border: 1px solid #f0e5dc;
        border-radius: 10px;
        background: var(--panel);
      }}
      .source-window {{
        position: relative;
        flex: 0 0 var(--box-w);
        width: var(--box-w);
        height: var(--box-h);
        overflow: hidden;
        background: #fff;
      }}
      .source-window img {{
        position: absolute;
        display: block;
        max-width: none;
        user-select: none;
      }}
      .font-stage {{ font-family: '{FONT_FAMILY}', sans-serif; }}
      .font-glyph {{
        display: block;
        color: #211916;
        font-size: var(--font-size);
        line-height: 1;
        white-space: nowrap;
      }}
      .record-meta {{
        overflow: hidden;
        height: 18px;
        margin-top: 7px;
        color: var(--muted);
        font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
        font-size: 9px;
        line-height: 18px;
        text-overflow: ellipsis;
        white-space: nowrap;
      }}
      .samples {{
        margin-top: 10px;
        padding: 7px 11px 6px;
        border-radius: 10px;
        background: var(--accent);
      }}
      .samples-label {{ color: var(--muted); font-size: 10px; line-height: 1.2; }}
      .sample-text {{
        margin-top: 2px;
        overflow: hidden;
        font-family: '{FONT_FAMILY}', sans-serif;
        font-size: 24px;
        line-height: 1.15;
        text-overflow: ellipsis;
        white-space: nowrap;
      }}
      footer {{
        margin-top: 7px;
        color: var(--muted);
        font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
        font-size: 10px;
        line-height: 1.2;
      }}
    """


def load_script(digest: str, check_size: int = 48) -> str:
    """Return the small browser-side font-loading status script."""

    return f"""
      <script>
        document.fonts.ready.then(() => {{
          const loaded = document.fonts.check('{check_size}px {FONT_FAMILY}');
          const status = document.getElementById('font-status');
          status.textContent = 'fontload=' + loaded + ' SHA256={digest}';
        }});
      </script>
    """


def page_html(
    page_number: int,
    chars: str,
    outlines: dict[str, dict[str, Any]],
    digest: str,
    image_size: tuple[int, int],
) -> str:
    """Build one 4-by-2 page of concept comparisons."""

    first, last = chars[0], chars[-1]
    cards = "".join(card(char, outlines[char], image_size) for char in chars)
    samples = (
        "CAT &amp; nap · cozy cat cafe · Black Cat",
        "JUMP OVER THE LAZY FOX · A-Z / a-z",
        "AaBb CcDd EeFf · tail and ear reading check",
        "quick brown fox jumps over the lazy cat",
    )[page_number % 4]
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>猫英字コンセプト比較 {page_number} — {first}–{last}</title>
  <style>{base_style(digest)}</style>
</head>
<body>
  <h1>猫英字コンセプト比較 0.105 / {page_number} — {first}–{last}</h1>
  <p class="intro">生成見本の該当範囲と、同じscaleで描画した配布用WOFF2を左右比較。各カードのboxは元PNGをCSSで表示しています。</p>
  <main class="grid">{cards}</main>
  <section class="samples">
    <div class="samples-label">小サイズ単語 / 実フォント</div>
    <div class="sample-text">{samples}</div>
  </section>
  <footer id="font-status">fontload=pending SHA256={digest}</footer>
  {load_script(digest)}
</body>
</html>
"""


def size_page_html(outlines: dict[str, dict[str, Any]], digest: str) -> str:
    """Build the extra fullwidth-53 and 16/24/32/48px identification page."""

    cells = []
    for char, fullwidth in zip(GLYPHS, FULLWIDTH_GLYPHS):
        codepoint = f"U+{ord(fullwidth):04X}"
        cells.append(
            f'<div class="full-cell"><span>{html.escape(fullwidth)}</span>'
            f'<code>{char} / {codepoint}</code></div>'
        )
    fullwidth_grid = "".join(cells)
    size_lines = []
    for size in (16, 24, 32, 48):
        size_lines.append(
            f'<div class="size-line"><strong>{size}px</strong>'
            f'<span style="font-size:{size}px">{html.escape(FULLWIDTH_GLYPHS)}</span></div>'
        )
    style = f"""
      {base_style(digest)}
      .fullwidth-grid {{
        display: grid;
        grid-template-columns: repeat(13, minmax(0, 1fr));
        gap: 5px;
        margin-top: 10px;
      }}
      .full-cell {{
        display: flex;
        min-width: 0;
        height: 69px;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--line);
        border-radius: 9px;
        background: #fff;
      }}
      .full-cell span {{
        font-family: '{FONT_FAMILY}', sans-serif;
        font-size: 34px;
        line-height: 1;
      }}
      .full-cell code {{
        margin-top: 4px;
        color: var(--muted);
        font: 8px/1 ui-monospace, SFMono-Regular, Consolas, monospace;
      }}
      .sizes {{
        display: grid;
        gap: 5px;
        margin-top: 10px;
        padding: 8px 11px;
        border-radius: 10px;
        background: var(--accent);
      }}
      .size-line {{
        display: grid;
        grid-template-columns: 52px minmax(0, 1fr);
        align-items: baseline;
        gap: 9px;
        min-width: 0;
        font-family: '{FONT_FAMILY}', sans-serif;
        line-height: 1.1;
      }}
      .size-line strong {{
        color: var(--muted);
        font: 10px/1.1 ui-monospace, SFMono-Regular, Consolas, monospace;
      }}
      .size-line span {{ overflow-wrap: anywhere; word-break: break-all; }}
      .note {{ margin: 5px 0 0; color: var(--muted); font-size: 11px; }}
    """
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>猫英字コンセプト比較 0.105 — 全角53字とサイズ識別</title>
  <style>{style}</style>
</head>
<body>
  <h1>猫英字コンセプト比較 0.105 — 全角53字 / サイズ識別</h1>
  <p class="intro">実フォントの全角派生（A–Z・a–z・&amp;）を一覧表示し、16px・24px・32px・48pxで字形の識別性を確認します。</p>
  <main class="fullwidth-grid">{fullwidth_grid}</main>
  <section class="sizes">
    <div class="samples-label">全角53字のサイズ比較 / 実フォント</div>
    {''.join(size_lines)}
  </section>
  <p class="note">元字形との対応は各セルのASCIIラベルとUnicode codepointで確認できます。</p>
  <footer id="font-status">fontload=pending SHA256={digest}</footer>
  {load_script(digest)}
</body>
</html>
"""


def generate() -> None:
    """Validate inputs and write pages 1–7 plus the extra size page."""

    if not CONCEPT_IMAGE.is_file():
        raise FileNotFoundError(f"Missing concept image: {CONCEPT_IMAGE}")
    if not FONT_FILE.is_file():
        raise FileNotFoundError(f"Missing WOFF2 font: {FONT_FILE}")
    outlines = load_outlines()
    image_size = png_size(CONCEPT_IMAGE)
    digest = sha256(FONT_FILE)
    OUT.mkdir(parents=True, exist_ok=True)

    for page_number, start in enumerate(range(0, len(GLYPHS), 8), start=1):
        chars = GLYPHS[start : start + 8]
        (OUT / f"page-{page_number}.html").write_text(
            page_html(page_number, chars, outlines, digest, image_size),
            encoding="utf-8",
            newline="\n",
        )
    (OUT / "page-8.html").write_text(
        size_page_html(outlines, digest), encoding="utf-8", newline="\n"
    )
    print(f"Created 8 concept review pages ({len(GLYPHS)} glyphs including &), SHA256={digest}")


if __name__ == "__main__":
    generate()
