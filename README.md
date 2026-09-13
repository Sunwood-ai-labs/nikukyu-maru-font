# にくきゅう丸 — 0.103 開発中

> 日本語対応拡張版を生成中です。現行の検証用生成物は **7,509 Unicode文字 / 7,540グリフ**。JIS X 0208 の漢字6,355字をすべて収録し、CP932の実用拡張、追加記号、半角カナ、結合濁点を含みます。数値検証と実シェーピング検証は完了していますが、公開リリースと全文字スクリーンショット監査は最終確認中で、まだ完了していません。配布済み安定版は[0.102](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/tag/v0.102)です。

![にくきゅう丸の文字見本](outputs/specimen.png)

[TTFをダウンロード](outputs/NikukyuMaru-Regular.ttf) · [WOFF2](outputs/NikukyuMaru-Regular.woff2) · [全収録文字](outputs/CHARACTERS.md) · [日本語機械検証](outputs/japanese-validation.json) · [Windows一時読み込み検証](outputs/windows-font-verification.json) · [監査対象manifest](outputs/audit/manifest.json)

0.103では、JIS X 0208の漢字6,355字を含む日本語の実用範囲、CP932拡張、追加記号、半角カナを補完しました。結合濁点・半濁点はOpenTypeの`ccmp`と`GPOS mark`で処理します。38文字の採用画像由来輪郭と装飾異体字2個は、これまでのデザイン資産として維持しています。

猫耳と肉球を添えた、太く柔らかい横組み見出し用フォントです。主要38文字と装飾異体字2個には採用画像由来の輪郭を使い、その他はMochiy Pop Oneを基礎に、足りない文字はZen Maru Gothic Blackから補完して文字ごとに丸めて調整しています。本文用の小サイズや縦組み専用の処理は対象にしていません。

## 使う

`outputs/NikukyuMaru-Regular.ttf` をダブルクリックし、Windows のフォントプレビューから「インストール」を選びます。アプリのフォント一覧では「にくきゅう丸」または「Nikukyu Maru」を選択してください。本リポジトリの確認では `verify_windows_font.py` から Windows GDI の private font として一時的に読み込み、確認後に解除しました。OSへの常設インストールは行っていません。

Web 用は `outputs/NikukyuMaru-Regular.woff2` です。

```css
@font-face {
  font-family: "Nikukyu Maru";
  src: url("NikukyuMaru-Regular.woff2") format("woff2");
  font-weight: 800;
  font-style: normal;
}
.headline { font-family: "Nikukyu Maru", sans-serif; font-weight: 800; line-height: 1.55; }
```

## 収録範囲と組版

0.103の生成TTFは7,509 Unicode文字（空白・私用領域を含む）、7,540グリフです。ひらがな・カタカナ・ASCII・全角英数字・基本記号に加え、JIS X 0208の漢字6,355字、CP932の実用拡張、追加記号を収録しています。半角カナはU+FF61〜U+FF9Fの63字を収録し、半角の濁点・半濁点を含む28組を処理します。

- U+3099（結合濁点）とU+309A（結合半濁点）は零幅のマークです。
- NFCの「が」「ぱ」などの合成済み文字と、NFDの「か」+ U+3099、「は」+ U+309Aなどを`ccmp`で既存の合成済み字形へ置換します。canonicalな組み合わせは58組です。
- 半角の「ｶﾞ」「ﾊﾟ」など28組も`ccmp`で処理します。通常の半角字形は500単位、2文字の合成後も2セル分の1,000単位を保ちます。
- U+E000は肉球、U+E001は猫顔、U+1F43Eは足跡です。絵文字を優先するアプリではU+1F43Eが別書体になる場合があるため、肉球単体にはU+E000を使います。

完全な一覧は `outputs/CHARACTERS.md` と `outputs/characters.txt` です。横組みの太い見出しを用途とし、縦組み専用の回転・縦用メトリクス、カーニング、ヒンティングは実装していません。小サイズでは肉球や半濁点などの細部が見えにくいため、大きな見出し向けです。

## 編集と再ビルド

0.102から引き続き、「こ・る」はOpenTypeのスタイルセット1（`ss01`）で肉球付きに切り替えます。Webでは `font-feature-settings: "ss01" 1` を指定してください。「a・8」は標準で肉球の抜き模様を含みます。

採用画像由来の輪郭は `sources/reference-outlines.json` に保存しています。`--regenerate` は元書体の処理後、この輪郭を優先してUFOに適用します。画像からの抽出をやり直す場合のみ `requirements-trace.txt` を導入し、`trace_reference.py` を実行します。通常ビルドではOpenCVは不要です。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-trace.txt
.\.venv\Scripts\python.exe -X utf8 trace_reference.py
.\.venv\Scripts\python.exe -X utf8 build.py --regenerate
```

比較画面の再生成は `compare.py`。プロジェクト直下をHTTPサーバーで配信して `outputs/comparison/page-1.html` を開きます。見本画像は通常形とss01を使い分けています。WindowsのPillowにはOpenType機能の描画支援がないため、PNG見本の該当2行は同じTTF内の異体字にcmapを切り替えた一時ファイルで描画しています。実際のss01動作はChromeで確認します。

検証環境: Windows / Python 3.12。通常依存は `requirements.txt`、HarfBuzzを使う組版検証の追加依存は `requirements-validation.txt` に固定しています。通常ビルドの依存に`uharfbuzz`は追加していません。

```powershell
cd C:\Prj\nikukyu-maru-font
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 build.py
```

通常ビルドは `sources/NikukyuMaru-Regular.ufo` の編集内容から TTF・WOFF2・SVG・見本・検証記録を生成します。UFO対応フォントエディターで輪郭を編集できます。1文字ごとの編集可能なSVGは `outputs/glyph-svg/` にあります（SVG変更は自動でUFOには戻りません）。

猫耳の位置、太さ、追加文字などは `sources/design.json` で指定します。次のコマンドは元フォントからUFOを再生成し、**UFOへの手編集を上書き**します。手編集後は先にUFOを別名保存してください。

```powershell
.\.venv\Scripts\python.exe -X utf8 build.py --regenerate
```

元フォントは `vendor/` に同梱済みで、依存導入後のビルドはオフラインで実行できます。見本生成はWindowsのArialを見出しラベルに使います。フォント本文は生成TTFのみで描画し、代替フォントを使いません。

## 検証と成果物

`japanese_validation.py` は生成TTF/WOFF2を読み、実用文章、JIS/CP932範囲、結合濁点、半角カナ、輪郭範囲、TTF/WOFF2の対応文字一致を機械検査します。`verify_kana_shaping.py` は小さな独立fixtureを作ってHarfBuzzでcanonical58組・半角28組を検証し、`--font`を付けると同じ検査を本番TTFにも行います。fixtureとJSONは `work/` に出力し、`sources/` と `outputs/` の生成元を変更しません。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-validation.txt
.\.venv\Scripts\python.exe -X utf8 verify_kana_shaping.py --font outputs\NikukyuMaru-Regular.ttf --report work\kana-shaping-verification.json
.\.venv\Scripts\python.exe -X utf8 japanese_validation.py
.\.venv\Scripts\python.exe -X utf8 proof.py
```

Windowsのネイティブ読込は、OSへ登録せず一時読み込みする次の検証で確認します。実行後はフォントを解除し、結果を `outputs/windows-font-verification.json` に保存します。

```powershell
.\.venv\Scripts\python.exe -X utf8 verify_windows_font.py
```

`python -X utf8 audit_pages.py` で現行の全収録文字と2異体字のブラウザー確認ページ、`outputs/audit/manifest.json` を生成します。全文字の実Chromeスクリーンショットと目視監査は現在最終確認中で、公開リリースとともに未完了です。`python -X utf8 package.py` で環境ファイルを含まないZIPを作成します。`harmonize.py` と `artifact_io.py` もビルドに必要です。

- `outputs/specimen.png`: 実TTFで描画した使用見本。
- `outputs/charset-*.png`: 全収録文字の一覧画像。
- `outputs/size-proof.png`: 16・24・32・48・72pxの文字組み。
- `outputs/verification.json`: 非空白文字の64px描画、字幅・上下範囲、TTF/WOFF2の対応文字一致、SHA-256。
- `outputs/japanese-validation.json`: 日本語コーパスと収録範囲の機械可読レポート。
- `outputs/windows-font-verification.json`: Windows private font の一時読み込み結果。

数値検証や一時読み込みの成功は、公開前の全文字目視監査や全アプリでの互換性を意味しません。OSへの常設インストールは今回行っていません。

## 出典とライセンス

| 用途 | 出典 | ライセンス表示 |
|---|---|---|
| 基本書体と大部分の派生輪郭 | [Mochiy Pop One / Google Fonts](https://github.com/google/fonts/tree/main/ofl/mochiypopone) | `vendor/OFL.txt` |
| 不足文字の補完輪郭 | [Zen Maru Gothic Black](https://github.com/googlefonts/zen-marugothic) | `vendor/ZenMaruGothic-OFL.txt` |

元書体の著作者はThe Mochiypop Project Authors、補完元の著作者はThe Zen Maru Gothic Project Authorsです。元TTFのSHA-256は `9e009430e1316c271a5f34759c6b65fc343c4e806f193042528887e7235a92c6`。補完元はビルドに使用した版を `vendor/ZenMaruGothic-Black.ttf` として同梱し、取得元と固定コミットは `supplemental.py` に記録しています。

同梱の `OFL.txt` と `outputs/OFL.txt` にSIL Open Font License 1.1の原文と両出典の著作権表示があります。本派生フォントもSIL Open Font License 1.1で配布し、元の著作権表示を保持します。フォント単体販売は禁止され、再配布時は著作権表示とライセンスの同梱が必要です。新しい書体名を設定済みです。

## 公開前の状態

現在は0.103開発版です。公開リリース、全文字の実Chromeスクリーンショット監査、最終的な全字形の目視レビューは完了していません。リリース告知や完了宣言は、root担当の最終確認後に行います。
