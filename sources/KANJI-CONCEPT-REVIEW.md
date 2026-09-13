# 漢字のコンセプト再検討

2026-09-13、ユーザーの「コンセプトに合っているか」の指摘を受けて追加画像を生成。
対応文字の増加は、デザイン統一の完了を意味しない。Mochiy由来の追加漢字には角ばったゴシックの印象が残っている。

## 画像

- `references/02-kanji-concept.png`: 初回16字の追加コンセプト。ぷっくりした輪郭は元見本に近いが、複雑な字に詰まりがある。
- `references/03-kanji-refined.png`: 正しい字形構造の比較画像を補助入力として、内部空間を広げた再生成。まだフォントへの採用確定ではない。

並び: 名 前 今 日 / 月 年 時 間 / 店 営 業 休 / 価 格 住 所。
初回の独立目視レビューでは「前・時・間・営・業・価・格・所」を要修正とした。
生成画像のかわいらしさだけで採用せず、構造、字間、小サイズの実描画を確認する。

## 最終生成プロンプト（built-in image_gen）

Use case: style-transfer, Japanese typeface glyph master refinement. Image 1 is the desired plush cat-paw FONT STYLE. Image 2 is the authoritative CORRECT STROKE STRUCTURE for the same 16 characters. Produce a revised version of image 1: keep its 4x4 layout, expressive rounded cushion-like contours, integrated cat ears on 日 and 店 only, solid black on pure white, clean flat vector-like silhouette. Exact rows: 名 前 今 日 / 月 年 時 間 / 店 営 業 休 / 価 格 住 所. Improve legibility by opening internal white spaces and separating strokes approximately 25 percent more, especially 前 時 間 営 業 価 格. Use image 2 to ensure every radical, short stroke, counter and dot is correct and identifiable. Specifically retain 寺's short diagonal dot in 時; preserve the top stroke and lower 木 structure of 業; preserve the distinct 木 radical and 各 component in 格; ensure 夕 in 名 is recognizable. Do not simply reproduce image 2's normal typeface: preserve the charming plump swelling and soft organic proportions from image 1, while giving complex glyphs enough breathing room. All sixteen remain exactly one correct kanji per equal square cell. No text labels, grid lines, grey antialiasing except edge pixels, gradients, shadows, or additional drawings. High-resolution square master sheet suitable for vector tracing.
