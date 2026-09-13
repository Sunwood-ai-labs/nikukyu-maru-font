# にくきゅう丸 0.103 進捗

0.103は、日本語の太い横組み見出し用途へ対応範囲を広げる拡張版です。現行TTFはcmap **7,516 Unicode文字 / glyphOrder 7,547グリフ**です。JIS X 0208漢字6,355字、CP932実用文字、追加記号、半角カナ63字、結合濁点・半濁点を含みます。

## 現在の決定

- [x] 一般漢字の基準をZen Maru Gothic Blackに統一し、かな・英字などにMochiy Pop Oneを使用。Zenにない漢字はMochiyで、Mochiyにない記号はZenや既存字形の組み合わせで補完。
- [x] sources/reference-outlines.jsonの40キーを実データ確認。Unicode文字38キーと.alt 2キー（こ.alt・る.alt）。
- [x] 画像生成見本03から名・今・日・月・年・店・休・住の8字を採用し、sources/kanji-concept-outlines.jsonへベクター輪郭を保存。小書きゃ・ゅの2字はharmonizeで通常かなから派生するため、直接適用の画像由来輪郭はUnicode44字形と.alt 2字形。抽出データ40キーは保持。
- [x] U+3099/U+309Aの零幅マーク、canonical58組のccmp、GPOS mark、半角カナ28組のccmpを実装。半角通常字形は500単位、合成結果は2セル分の1,000単位を維持。
- [x] .notdef、ss01異体字2個、ccmp補助グリフ28個を含むglyphOrderを検証。
- [x] 出典のOFL表示、再現ビルド、TTF/WOFF2、Windows private font一時読み込みの記録を更新。

## 検証状況

- [x] outputs/verification.jsonでUnicode/glyph数、64px描画、輪郭範囲、TTF/WOFF2対応文字、SHA-256を検査。
- [x] outputs/japanese-validation.jsonで実用文章、JIS/CP932、結合濁点、半角カナを検査。
- [x] outputs/kana-shaping-verification.jsonで本番TTFのcanonical58組・半角28組をuharfbuzz検査。
- [x] outputs/concept-review/kanji8-final-verification.jsonで8字の構造、輪郭、180pxと16・24・32・48pxの実描画を検査。
- [x] outputs/audit/manifest.jsonとoutputs/audit/font-hash.jsonで158ページを固定。
- [x] 158枚の全収録文字スクリーンショットを目視監査し、具体的なFAILを確認しなかった。分担ページ41〜80の詳細は[review-41-80.md](outputs/audit/review-41-80.md)。
- [x] outputs/concept-review/final-page-1.pngとfinal-page-2.pngで、採用8字とかなを含む実フォント比較を保存。

## 最終確認

- [x] outputs/practical-review/の実用文章8カテゴリ31ケースをスクリーンショットで最終確認する。
- [x] rootによる全体表示レビューを完了し、outputs/FINAL-REVIEW.mdへ記録する。
- [x] ZIPを展開して通常ビルドし、TTF/WOFF2のバイト一致を確認。

配布先: [0.103リリース](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/tag/v0.103)。OSへの常設インストールは行っていない。

## 再現コマンド

```powershell
.\.venv\Scripts\python.exe -X utf8 build.py --regenerate
.\.venv\Scripts\python.exe -m pip install -r requirements-validation.txt
.\.venv\Scripts\python.exe -X utf8 verify_kana_shaping.py --font outputs\NikukyuMaru-Regular.ttf --report outputs\kana-shaping-verification.json
.\.venv\Scripts\python.exe -X utf8 verify_kanji_concept.py --font outputs\NikukyuMaru-Regular.ttf --report outputs\concept-review\kanji8-final-verification.json
.\.venv\Scripts\python.exe -X utf8 japanese_validation.py
.\.venv\Scripts\python.exe -X utf8 proof.py
.\.venv\Scripts\python.exe -X utf8 verify_windows_font.py
.\.venv\Scripts\python.exe -X utf8 audit_pages.py
.\.venv\Scripts\python.exe -X utf8 package.py
```

## 方針と制約

用途は太い横組み見出しです。縦組み専用の回転・縦用メトリクス、カーニング、ヒンティングは実装していません。画像生成見本の8字は直接輪郭として採用し、残りの前・時・間・営・業・価・格・所は読みやすさを優先してZen由来の字形を採用しています。
