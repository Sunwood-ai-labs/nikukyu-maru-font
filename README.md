# にくきゅう丸 — 0.105

**生成した猫アルファベットの見本を、実際に使えるフォントへ。** A–Z / a–z の52字と「&」を、ぽってりした骨格・幅広い猫耳・自然なしっぽのある輪郭として採用しました。全角53字にも反映しています。

![生成見本と配布フォントの比較](outputs/latin-concept-review/comparison.png)

[TTF](outputs/NikukyuMaru-Regular.ttf) · [WOFF2](outputs/NikukyuMaru-Regular.woff2) · [0.105リリース](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/tag/v0.105) · [全収録文字](outputs/CHARACTERS.md) · [1文字ずつ左右比較](outputs/latin-concept-review/) · [生成画像](references/04-latin-cat-concept.png)

元の画像から各文字を曲線として抽出し、文字ごとの形を保ちながら字幅・ベースラインを設定しています。0.104で使った一律の細い耳・小さな巻き尾は、この53字では使っていません。かな・漢字・数字などの字形は0.104を維持しています。

収録数は **7,516 Unicode文字 / 7,547グリフ**。猫らしさを活かす太い横組み見出し向けです。小サイズでは耳や肉球、小さい内孔の細部が見えにくくなります。

## 使う

Web用は`outputs/NikukyuMaru-Regular.woff2`です。

```css
@font-face {
  font-family: "Nikukyu Maru";
  src: url("NikukyuMaru-Regular.woff2") format("woff2");
  font-weight: 800;
  font-style: normal;
}
.headline {
  font-family: "Nikukyu Maru", sans-serif;
  font-weight: 800;
  line-height: 1.55;
}
```

WindowsではTTFをダブルクリックしてプレビューを開き、「インストール」から使用できます。本リポジトリの確認では`verify_windows_font.py`からWindows GDIのprivate fontとして読み込み、確認後に解除しました。OSへの常設インストールは行っていません。

## 0.103で確定した収録範囲と組版

0.105の生成TTFはcmap 7,516 Unicode文字、glyphOrder 7,547グリフです。ひらがな・カタカナ・ASCII・全角英数字・基本記号、JIS X 0208の漢字6,355字、CP932の実用拡張、追加記号を収録しています。半角カナはU+FF61〜U+FF9Fの63字です。

- U+3099（結合濁点）とU+309A（結合半濁点）は零幅のマークです。
- NFCの「が」「ぱ」などと、NFDの「か」+U+3099、「は」+U+309Aなどは、OpenTypeの`ccmp`で既存の合成済み字形へ置換します。canonicalな組み合わせは58組です。
- 半角の「ｶﾞ」「ﾊﾟ」など28組も`ccmp`で処理します。通常の半角字形は500単位、合成後の濁音・半濁音は2セル分の1,000単位を保ちます。
- 「こ」「る」は`ss01`で肉球付きの異体字に切り替えられます。Webでは`font-feature-settings: "ss01" 1`を指定してください。
- U+E000は肉球、U+E001は猫顔、U+1F43Eは足跡です。絵文字を優先するアプリではU+1F43Eが別書体になる場合があるため、肉球単体にはU+E000を使います。

用途は太い横組み見出しです。縦組み専用の回転・縦用メトリクス、カーニング、ヒンティングは実装していません。小サイズでは肉球や半濁点などの細部が見えにくい場合があります。

## 編集と再ビルド

通常ビルドは編集用UFOから生成します。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 build.py
```

画像に基づく英字の再抽出には`requirements-trace.txt`が必要です。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-trace.txt
.\.venv\Scripts\python.exe -X utf8 trace_latin_concept.py
.\.venv\Scripts\python.exe -X utf8 latin_cats.py
.\.venv\Scripts\python.exe -X utf8 build.py
.\.venv\Scripts\python.exe -X utf8 concept_latin_review.py
.\.venv\Scripts\python.exe -X utf8 concept_latin_overview.py
```

[生成プロンプト](references/04-latin-cat-concept-prompt.md)、[抽出輪郭](sources/latin-concept-outlines.json)、[設計記録](sources/LATIN-DESIGN.md)を同梱しています。`build.py --regenerate`は元フォントからUFOを再生成し、同じ画像由来の英字を適用します。UFOへの手編集は上書きされます。比較HTMLを再生成した後は実ブラウザーでフォント読み込みを確認し、スクリーンショットを撮り直してください。

## 検証記録

- [機械検証](outputs/verification.json): 現行TTF/WOFF2の収録範囲、全非空白文字の64px描画、輪郭範囲、SHA-256。
- [画像との形状比較](outputs/latin-concept-review/reference-fidelity.json): 実TTFの各字を元画像と照合し、輪郭の重なり・縦横比・内孔数を検査。
- [回帰と再現性](outputs/latin-concept-review/regression.json): 旧版との全字形比較、変更対象106字の限定、Unicode/glyphOrder/GSUBの一致、隔離したUFOからの通常コンパイル・画像輪郭の再適用。
- [スクリーンショット](outputs/latin-concept-review/): 生成見本と実WOFF2の1字ずつの左右比較、全角・サイズ別表示、全体比較。

0.104の英字レビューは[旧レビュー](outputs/latin-review/)に保存し、HTML用の0.104 WOFF2も固定しています。0.103の[全字158ページ監査](outputs/FINAL-REVIEW.md)、[実用31ケース](outputs/practical-review/)、[全再生成](outputs/reproducibility-verification.json)、[ZIP再ビルド](outputs/package-verification.json)はそれぞれ旧版の証跡です。

旧TTFを用意して回帰検証する場合は、`verify_latin_regression.py --baseline <旧TTF> --current <新TTF> --include-ampersand`を使用します。0.105は英字に加えて半角・全角の「&」も変更しています。

## 出典とライセンス

| 用途 | 出典 | ライセンス表示 |
|---|---|---|
| 一般漢字の基準輪郭 | [Zen Maru Gothic Black](https://github.com/googlefonts/zen-marugothic) | `vendor/ZenMaruGothic-OFL.txt` |
| かな・英字、Zenにない漢字の補完 | [Mochiy Pop One / Google Fonts](https://github.com/google/fonts/tree/main/ofl/mochiypopone) | `vendor/OFL.txt` |
| Mochiyにない記号の構成 | Zen Maru Gothic Blackの輪郭 + 既存字形 | `vendor/ZenMaruGothic-OFL.txt` / `vendor/OFL.txt` |

Mochiyの著作者はThe Mochiypop Project Authors、Zenの著作者はThe Zen Maru Gothic Project Authorsです。Mochiyの元TTFのSHA-256は`9e009430e1316c271a5f34759c6b65fc343c4e806f193042528887e7235a92c6`です。Zen Maru Gothic Blackは`vendor/ZenMaruGothic-Black.ttf`として同梱し、取得元と固定コミットは`supplemental.py`に記録しています。

同梱の`OFL.txt`、`outputs/OFL.txt`、`vendor/`内のライセンスファイルにSIL Open Font License 1.1の表示を保持しています。本派生フォントもSIL Open Font License 1.1で配布します。再配布時は著作権表示とライセンスを同梱してください。
