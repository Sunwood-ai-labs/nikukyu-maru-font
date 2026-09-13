# にくきゅう丸 0.103（開発中）

0.103の日本語対応拡張版に関するリリースノート草稿です。生成物の数値検証と実シェーピング検証は完了しています。公開リリース、全文字の実Chromeスクリーンショット監査、最終目視レビューはrootで確認中のため、まだ完了扱いにしません。WindowsのOSへの常設インストールも行っていません。

## 収録範囲

- 生成TTF: 7,509 Unicode文字、7,540グリフ。
- JIS X 0208の漢字6,355字を収録し、CP932の実用拡張と追加記号を補完。
- 半角カナU+FF61〜U+FF9Fの63字を収録。
- U+3099/U+309Aの結合濁点・結合半濁点を零幅マークとして収録。
- 採用画像から輪郭化した主要38文字と装飾異体字2個を従来どおり保持。

## 組版対応

- `ccmp`でcanonicalな結合濁点・半濁点の58組を合成済み字形へ置換。
- `GPOS mark`でU+3099/U+309Aを零幅の基底字形へ配置。
- 半角カナの濁点・半濁点28組を`ccmp`で処理。
- 半角字形は500単位を基本幅とし、2文字の半角濁音・半濁音を合成しても2セル分の1,000単位を維持。
- 用途は太い横組み見出し。縦組み専用の回転・縦用メトリクスは実装していない。

## 出典とライセンス

- 基本文字と大部分の輪郭は[Mochiy Pop One（Google Fonts）](https://github.com/google/fonts/tree/main/ofl/mochiypopone)を使用。
- 不足文字の補完には[Zen Maru Gothic Black（Google Fonts）](https://github.com/googlefonts/zen-marugothic)を使用。
- 両出典の著作権表示とSIL Open Font License 1.1を`OFL.txt`、`outputs/OFL.txt`、`vendor/`内のライセンスファイルに保持。
- 画像由来の38+2輪郭はプロジェクトのデザイン資産として`sources/reference-outlines.json`に記録。

## 実施した検証

- `verify_kana_shaping.py` と固定した`uharfbuzz`で、独立fixtureおよび本番TTFをcanonical58組・半角28組について実シェーピング検証。
- `japanese_validation.py`、`proof.py`で収録文字、輪郭範囲、64px描画、TTF/WOFF2の対応文字一致を検査。
- `verify_windows_font.py`でWindows GDIへprivate fontとして一時読み込みし、名前・住所・価格・営業時間などのBMP文字を確認。確認後にフォントを解除。

主な再現コマンド:

```powershell
.\.venv\Scripts\python.exe -X utf8 build.py --regenerate
.\.venv\Scripts\python.exe -m pip install -r requirements-validation.txt
.\.venv\Scripts\python.exe -X utf8 verify_kana_shaping.py --font outputs\NikukyuMaru-Regular.ttf --report work\kana-shaping-verification.json
.\.venv\Scripts\python.exe -X utf8 japanese_validation.py
.\.venv\Scripts\python.exe -X utf8 proof.py
.\.venv\Scripts\python.exe -X utf8 verify_windows_font.py
```

## 公開前の残作業

- [ ] 全収録文字の実Chromeスクリーンショットを撮影し、ページごとの目視監査を完了する。
- [ ] rootによる全字形レビューを完了する。
- [ ] 0.103を公開リリースとして確定する。

上記が完了するまでは、0.103を公開済みまたは全文字確認済みとは扱いません。
