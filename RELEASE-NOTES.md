# にくきゅう丸 0.103

0.103は日本語対応の拡張版です。現行生成物はcmap **7,516 Unicode文字 / glyphOrder 7,547グリフ**です。機械検証、実シェーピング検証、158枚の全収録文字スクリーンショット監査、実用8カテゴリ31ケースの表示レビューを記録済みです。全再生成とZIPからの再ビルドでTTF/WOFF2のバイト一致を確認しています。Windows OSへの常設インストールも行っていません。

## 収録範囲

- JIS X 0208の漢字6,355字、CP932の実用文字、追加記号を収録。
- 半角カナU+FF61〜U+FF9Fの63字を収録。
- U+3099/U+309Aの結合濁点・結合半濁点を零幅マークとして収録。
- glyphOrderの内訳には.notdef、ss01の異体字2個、ccmpの半角カナ用補助グリフ28個を含む。
- 既存の画像由来輪郭は、sources/reference-outlines.jsonのUnicode文字38キーと.alt 2キー（こ.alt・る.alt）。小書きゃ・ゅの2字は読みやすさを優先してharmonizeで通常かなから派生するため、最終的に直接適用される元参照はUnicode36字形と.alt 2字形。0.103で採用した画像生成由来の8字（名・今・日・月・年・店・休・住）を加えると、直接適用の画像由来輪郭はUnicode44字形と.alt 2字形。

## 字形方針

一般漢字の基準輪郭はZen Maru Gothic Blackです。かな・英字・記号・既存デザイン資産はMochiy Pop Oneを基礎とし、Zenにない漢字はMochiyで、Mochiyにない記号はZenや既存字形の組み合わせで補完します。画像生成見本references/03-kanji-refined.pngから選んだ8字は、sources/kanji-concept-outlines.jsonのベクター輪郭として採用済みです。画像生成見本の残り8字（前・時・間・営・業・価・格・所）は追加画像輪郭にはせず、0.103では読みやすさを優先してZen由来の字形を採用しています。

## 組版対応

- ccmpでcanonicalな結合濁点・半濁点58組を合成済み字形へ置換。
- GPOS markでU+3099/U+309Aを零幅の基底字形へ配置。
- 半角カナの濁点・半濁点28組をccmpで処理。
- 通常の半角字形は500単位、合成後の濁音・半濁音は2文字分の1,000単位を維持。
- 用途は太い横組み見出し。縦組み専用の回転・縦用メトリクスは実装していない。

## 出典とライセンス

- 一般漢字の基準と不足記号の補完: [Zen Maru Gothic Black（Google Fonts）](https://github.com/googlefonts/zen-marugothic)。
- かな・英字などとZenにない漢字の補完: [Mochiy Pop One（Google Fonts）](https://github.com/google/fonts/tree/main/ofl/mochiypopone)。
- 両出典の著作権表示とSIL Open Font License 1.1をOFL.txt、outputs/OFL.txt、vendor/内のライセンスファイルに保持。
- 画像由来の輪郭記録: [sources/reference-outlines.json](sources/reference-outlines.json)、[sources/kanji-concept-outlines.json](sources/kanji-concept-outlines.json)、[コンセプトレビュー](sources/KANJI-CONCEPT-REVIEW.md)。

## 実施した検証

- [outputs/verification.json](outputs/verification.json): 7,516 Unicode文字 / 7,547グリフ、TTF/WOFF2対応文字一致、64px描画、輪郭範囲、SHA-256。
- [outputs/japanese-validation.json](outputs/japanese-validation.json): JIS/CP932、実用文章、結合濁点、半角カナを検査。
- [outputs/kana-shaping-verification.json](outputs/kana-shaping-verification.json): 本番TTFのcanonical58組・半角28組をuharfbuzzで検査。
- [outputs/concept-review/kanji8-final-verification.json](outputs/concept-review/kanji8-final-verification.json): 採用8字の構造、輪郭、180pxと16・24・32・48pxの実描画を検査。
- [outputs/windows-font-verification.json](outputs/windows-font-verification.json): Windows GDIへのprivate font一時読み込みを検査し、確認後に解除。
- [outputs/audit/font-hash.json](outputs/audit/font-hash.json)と[outputs/audit/manifest.json](outputs/audit/manifest.json): 158ページの対象とフォントを記録。具体的なFAILはなく、分担結果は[review-41-80.md](outputs/audit/review-41-80.md)に記録。
- 実用文章8カテゴリ31ケースのHTMLとPNGは[outputs/practical-review/](outputs/practical-review/)に生成済みで、表示確認を完了しました。全体の確認結果は[FINAL-REVIEW.md](outputs/FINAL-REVIEW.md)、コンセプト比較の画像証跡は[final-page-1.png](outputs/concept-review/final-page-1.png)、[final-page-2.png](outputs/concept-review/final-page-2.png)です。

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

requirements-validation.txtはrequirements-trace.txtを参照する検証専用依存で、uharfbuzz・OpenCV・NumPyを導入します。通常ビルドのrequirements.txtにはuharfbuzzを追加していません。

## 最終確認

- [x] 158枚の全収録文字スクリーンショット監査とmanifest/font-hash記録。
- [x] 具体的な未描画・線の欠け・セル外への切れの指摘がないことを確認。
- [x] 実用文章8カテゴリ31ケースの最終スクリーンショット確認。
- [x] rootによる全体表示レビューを完了。`outputs/FINAL-REVIEW.md`に記録。
- [x] ZIPを展開して通常ビルドし、TTF/WOFF2のバイト一致を確認。


配布先: [0.103リリース](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/tag/v0.103)。再現記録: [全再生成](outputs/reproducibility-verification.json) / [ZIP再ビルド](outputs/package-verification.json)。
