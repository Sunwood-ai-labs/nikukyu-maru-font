# 漢字のコンセプト再検討

2026-09-13、漢字にも猫耳・肉球のある太く丸い印象をそろえたいという指摘を受け、追加の画像生成見本と輪郭比較を行った。0.103では、一般漢字の基準にZen Maru Gothic Blackを採用し、かな・英字などにはMochiy Pop Oneを使う方針を確定した。Zenにない漢字はMochiyで、Mochiyにない記号はZenや既存字形の組み合わせで補完する。

## 画像生成見本

- [02-kanji-concept.png](../references/02-kanji-concept.png): 初回16字の追加コンセプト。ぷっくりした輪郭は元見本に近いが、複雑な字に詰まりがあった。
- [03-kanji-refined.png](../references/03-kanji-refined.png): 正しい字形構造を補助入力にして内部空間を広げた再生成。0.103の8字を選ぶ基準画像として採用した。
- 並びは、名 前 今 日 / 月 年 時 間 / 店 営 業 休 / 価 格 住 所。

## 0.103で採用した8字

画像生成見本03から、輪郭の丸みと字形の読みやすさを両立できた次の8字を採用した。

名・今・日・月・年・店・休・住

採用輪郭は [kanji-concept-outlines.json](kanji-concept-outlines.json) に保存し、ビルド時にUnicode字形へ適用する。生成元を再現するスクリプトは [trace_kanji_concept.py](../trace_kanji_concept.py) である。残りの8字（前・時・間・営・業・価・格・所）は追加画像輪郭にはせず、0.103では読みやすさを優先してZen由来の字形を採用した。文字自体は収録済みであり、今回の未実装を意味しない。

## 輪郭と実描画の確認

採用8字について、実TTFの輪郭範囲、構造、180px描画、かなと並べた16・24・32・48px描画を確認した。

- [kanji8-final-verification.json](../outputs/concept-review/kanji8-final-verification.json): passed=true、errors=[]。
- [kanji8-final-render.png](../outputs/concept-review/kanji8-final-render.png): 採用8字とかなの実フォント描画。
- [kanji8-final-sizes.png](../outputs/concept-review/kanji8-final-sizes.png): 小サイズ比較。
- [final-page-1.png](../outputs/concept-review/final-page-1.png) / [final-page-2.png](../outputs/concept-review/final-page-2.png): 実フォントと追加見本の比較。
- [kanji-base-comparison.md](../outputs/concept-review/kanji-base-comparison.md): Zen基準と複雑漢字の比較方針。

構造・表示上の失敗は確認しなかった。住は入力輪郭とコンパイル後で輪郭分解数が2対3になったが、形状の消失ではなくアウトライン分解の差である。日と月はかなの中央値よりインク密度が高く見えるが、16・24・32・48pxでも内部空間を確認できた。

## 参照輪郭との関係

元の [reference-outlines.json](reference-outlines.json) は実データで40キーだった。内訳はUnicode文字38キーと、ss01用のこ.alt・る.alt 2キーである。うち小書きゃ・ゅの2字は、読みやすいサイズ調整のためharmonizeで通常かなから派生する。したがって直接適用される元参照はUnicode36字形 + .alt 2字形で、採用8字を加えた直接適用の画像由来輪郭はUnicode44字形 + .alt 2字形になる。抽出データ40キーはそのまま保持し、元の38 Unicode字形と2つの装飾異体字を既存の肉球・猫耳デザイン資産として記録する。

## 生成プロンプト（built-in image_gen）

Use case: style-transfer, Japanese typeface glyph master refinement. Image 1 is the desired plush cat-paw FONT STYLE. Image 2 is the authoritative CORRECT STROKE STRUCTURE for the same 16 characters. Produce a revised version of image 1: keep its 4x4 layout, expressive rounded cushion-like contours, integrated cat ears on 日 and 店 only, solid black on pure white, clean flat vector-like silhouette. Exact rows: 名 前 今 日 / 月 年 時 間 / 店 営 業 休 / 価 格 住 所. Improve legibility by opening internal white spaces and separating strokes approximately 25 percent more, especially 前 時 間 営 業 価 格. Use image 2 to ensure every radical, short stroke, counter and dot is correct and identifiable. Specifically retain 寺's short diagonal dot in 時; preserve the top stroke and lower 木 structure of 業; preserve the distinct 木 radical and 各 component in 格; ensure 夕 in 名 is recognizable. Do not simply reproduce image 2's normal typeface: preserve the charming plump swelling and soft organic proportions from image 1, while giving complex glyphs enough breathing room. All sixteen remain exactly one correct kanji per equal square cell. No text labels, grid lines, grey antialiasing except edge pixels, gradients, shadows, or additional drawings. High-resolution square master sheet suitable for vector tracing.

生成画像のかわいらしさだけで16字すべてを同じ画像輪郭にせず、正しい字形構造、輪郭の連結、字間、小サイズの実描画を採用判断に使った。残り8字は読みやすさを優先してZen由来の字形を採用し、全16字を収録している。
