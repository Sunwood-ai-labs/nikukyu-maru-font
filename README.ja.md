<div align="center">
  <h1>🐾 にくきゅう丸</h1>
  <p><strong>日本語と英字の見出しに使える、ぽってりした猫モチーフの表示フォント。</strong></p>
  <p>丸い線、幅広い猫耳、肉球の細部、文字ごとに終筆へつながるしっぽを、実際に使えるフォントへまとめました。</p>
  <p>
    <a href="https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/tag/v0.105"><img src="https://img.shields.io/github/v/release/Sunwood-ai-labs/nikukyu-maru-font?display_name=tag&label=release" alt="最新リリース"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-OFL--1.1-2f855a.svg" alt="SIL Open Font License 1.1"></a>
  </p>
  <p><a href="README.md">English README</a> · <a href="https://sunwood-ai-labs.github.io/nikukyu-maru-font/">日本語ショーケース</a> · <a href="https://sunwood-ai-labs.github.io/nikukyu-maru-font/en/">英語ショーケース</a></p>
  <img src="outputs/latin-concept-review/comparison.png" width="960" alt="生成した猫英字の見本と、にくきゅう丸0.105の比較">
  <p><em>0.105の英字コンセプト見本と、配布用WOFF2を左右に比較。</em></p>
</div>

## 🐾 これは何か

にくきゅう丸は、ポスター、タイトル、サムネイルなどの横組み文字に向く、太く親しみやすい表示フォントです。0.105では、生成した猫英字の方向性を実用フォントへ反映しました。A–Z、a–z、「&amp;」と、その全角53字に、文字ごとの丸い輪郭、幅広い猫耳、終筆に沿うしっぽを採用しています。

英字53字は、[04-latin-cat-concept.png](references/04-latin-cat-concept.png)からトレースしました。この画像は組み込みの画像生成ツールで作ったコンセプト見本です。[生成プロンプト](references/04-latin-cat-concept-prompt.md)も保存しています。PNGをそのままフォントにしたのではなく、参照画像の形を編集可能な曲線へ抽出し、字幅とベースラインを設定してからTTF/WOFF2で確認しています。

かなと漢字も、やわらかく丸い方向性を保っています。基準フォントの出典と組み合わせ方は[SUPPLEMENTAL-SOURCES.md](sources/SUPPLEMENTAL-SOURCES.md)に記録しています。

## 📦 ダウンロード

v0.105のリリースには、デスクトップ用フォント、Web用フォント、ソース一式が含まれます。

- デスクトップアプリ用の[TTFをダウンロード](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/download/v0.105/NikukyuMaru-Regular.ttf)。
- Web用の[WOFF2をダウンロード](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/download/v0.105/NikukyuMaru-Regular.woff2)。
- 編集用UFO、参照画像、スクリプト、検証記録を含む[v0.105ソースZIPをダウンロード](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/download/v0.105/NikukyuMaru-0.105.zip)。
- SHA-256とリリースノートは[リリースページ](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/tag/v0.105)で確認できます。

リポジトリ内にも[TTF](outputs/NikukyuMaru-Regular.ttf)と[WOFF2](outputs/NikukyuMaru-Regular.woff2)を収録しています。

### Webで使う

~~~css
@font-face {
  font-family: "Nikukyu Maru";
  src: url("NikukyuMaru-Regular.woff2") format("woff2");
  font-weight: 800;
  font-style: normal;
  font-display: swap;
}

.cat-headline {
  font-family: "Nikukyu Maru", sans-serif;
  font-weight: 800;
  line-height: 1.55;
}
~~~

WOFF2をダウンロードして自分のサイトへ配置し、CSSから同一オリジンのファイルを指定してください。GitHub ReleaseのCORSやブラウザーごとの配布挙動に依存せずに配信できます。デスクトップアプリでは、通常のOSのフォントインストーラーからTTFをインストールしてください。

## 🧪 試す

- [日本語ショーケースを開く](https://sunwood-ai-labs.github.io/nikukyu-maru-font/)。日本語を中心にフォントの雰囲気を確認できます。
- [英語ショーケースを開く](https://sunwood-ai-labs.github.io/nikukyu-maru-font/en/)。英語で概要と使い方を確認できます。
- [0.105の英字を1字ずつ比較する](outputs/latin-concept-review/)。全角字形と16/24/32/48pxのサンプルも含みます。
- [0.105の全体比較画像](outputs/latin-concept-review/comparison.png)と[生成見本](references/04-latin-cat-concept.png)を見る。

## 🗺️ 収録範囲

[verification.json](outputs/verification.json)の現行ビルド検証では、**Unicode 7,516文字、グリフ7,547個**を収録しています。異体字、結合マーク、内部グリフを含むため、Unicode文字数とグリフ数は一致しません。

- ひらがな、カタカナ、全角形、基本的な句読点・記号、ギリシャ文字、キリル文字、ラテン文字を収録しています。
- 日本語用にはJIS X 0208の漢字6,355字、実用的なCP932追加文字、半角カナU+FF61–U+FF9Fの63字があります。
- U+3099とU+309Aは零幅の結合マークです。OpenTypeのccmpで、記録済みの合成済み濁音・半濁音と半角の組み合わせを処理します。
- ss01で「こ」「る」を肉球付きの異体字へ切り替えられます。U+E000はプロジェクトの肉球、U+E001は猫顔、U+1F43Eは足跡です。
- 0.105で変更したUnicodeコードポイントは106個です。画像由来のASCII53字と、その全角53字にあたります。それ以外の収録範囲は構造回帰検証で保持を確認しています。

横組み用の表示フォントです。縦組み用メトリクス、縦用異体字、カーニング、ヒンティングは実装していません。小サイズでは耳、肉球、小さなふところが見えにくくなるため、細部を見せたい場合は太めの見出しサイズで使ってください。

## 🛠️ 編集と再ビルド

編集の基準は編集可能なUFOとsources/の設計データです。固定した依存関係をローカルの仮想環境へ入れて使います。[uv](https://docs.astral.sh/uv/)を推奨します。

~~~powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
uv run --active python -X utf8 build.py
~~~

0.105の英字コンセプトを再抽出する場合は、トレース用依存関係を入れてから画像から曲線を作り、通常ビルドを行います。

~~~powershell
uv pip install -r requirements-trace.txt
uv run --active python -X utf8 trace_latin_concept.py
uv run --active python -X utf8 latin_cats.py
uv run --active python -X utf8 build.py
uv run --active python -X utf8 concept_latin_review.py
uv run --active python -X utf8 concept_latin_overview.py
~~~

検証用依存関係は同じ環境へ追加します。

~~~powershell
uv pip install -r requirements-validation.txt
uv run --active python -X utf8 verify_latin_concept.py
uv run --active python -X utf8 japanese_validation.py
~~~

build.py --regenerateは設計データからUFOを再生成するため、手作業で編集したUFOを上書きする場合があります。実験には作業コピーやブランチを使ってください。画像トレースの[latin-concept-outlines.json](sources/latin-concept-outlines.json)には、元画像の矩形、倍率、ベースラインを記録しています。出典を別の画像へ黙って置き換えないでください。

ドキュメントサイトをローカルで確認するときは、Nodeの依存関係を入れてから次を実行します。

~~~powershell
npm ci
npm run docs:dev
npm run docs:build
npm run docs:preview
npm run site:check
~~~

## ✅ QAと検証記録

[ショーケースの検証記録と公開スクショ](verification/site-showcase.md)に、実操作・レスポンシブ確認・公開結果・開発依存の監査警告をまとめています。

現行0.105の証跡は目的ごとに分けています。

- [機械検証](outputs/verification.json): 収録範囲、TTF/WOFF2のcmap一致、空白以外のラスタライズ、bounds、SHA-256を記録しています。
- [参照画像との形状比較](outputs/latin-concept-review/reference-fidelity.json): 英字53字を元画像の各boxと照合し、シルエットの重なり、縦横比、内孔数を確認しています。構造を示す検査であり、目視確認の代わりではありません。
- [回帰と再現性](outputs/latin-concept-review/regression.json): 変更106字、変更されていない字形、cmap/GSUB、隔離コンパイル、輪郭再適用を記録しています。
- [目視検証](outputs/latin-concept-review/visual-verification.json): 最終スクリーンショット、対象文字、フォントSHAを対応づけています。判断の詳細は[REVIEW.md](outputs/latin-concept-review/REVIEW.md)にあります。
- [対応文字一覧](outputs/CHARACTERS.md): Unicode文字と名前をすべて一覧できます。

0.103の158ページ日本語監査と実用ケース、0.104の英字ページは、[FINAL-REVIEW.md](outputs/FINAL-REVIEW.md)、[practical-review](outputs/practical-review/)、[latin-review](outputs/latin-review/)に旧版の証跡として残しています。各ファイルは対象リリースを記録しており、現行0.105の検証結果とは分けて扱います。

## 📚 出典とライセンス

| 用途 | 出典 | 表示 |
| --- | --- | --- |
| 一般漢字の基準と補完記号 | [Zen Maru Gothic Black](https://github.com/googlefonts/zen-marugothic) | [vendor/ZenMaruGothic-OFL.txt](vendor/ZenMaruGothic-OFL.txt) |
| かな、英字、その他の漢字以外の基準輪郭 | [Mochiy Pop One](https://github.com/google/fonts/tree/main/ofl/mochiypopone) | [vendor/OFL.txt](vendor/OFL.txt) |
| 0.105英字コンセプトの参照 | [04-latin-cat-concept.png](references/04-latin-cat-concept.png)、組み込みの画像生成ツールで生成 | [プロンプトとトレース記録](references/04-latin-cat-concept-prompt.md) |

上流の著作権表示とSIL Open Font License 1.1の本文はvendor/に保持しています。トップレベルの[LICENSE](LICENSE)は、[OFL.txt](OFL.txt)と同じプロジェクト表示およびOFL本文のコピーです。OFLの条件に従い、フォントは利用、改変、埋め込み、ソフトウェアへの同梱と再配布ができます。フォント単体の販売はできず、改変したフォントソフトウェアもOFLで配布します。再配布時は表示とライセンスを残してください。

## 🗂️ リポジトリ構成

- outputs/NikukyuMaru-Regular.ttf — デスクトップ用フォント。
- outputs/NikukyuMaru-Regular.woff2 — Web用フォント。
- sources/NikukyuMaru-Regular.ufo/ — 編集可能なUFOソース。
- sources/design.json — ビルド設定とリリースバージョン。
- references/ — コンセプト画像とプロンプト。
- build.py、trace_latin_concept.py、latin_cats.py — ビルドと0.105英字トレースのツール。
- outputs/latin-concept-review/ — 現行の比較画像、検証記録、スクリーンショット。
- docs/ — VitePressショーケースのソース。上記の日本語・英語URLで公開しています。

## 🤝 貢献とサポート

輪郭、ビルドデータ、検証コードを変更する前に[CONTRIBUTING.md](CONTRIBUTING.md)を読んでください。使い方の質問と再現可能な不具合情報は[SUPPORT.md](SUPPORT.md)へ。Issueフォームでは、フォントのバージョン、コードポイント、表示環境、証跡をまとめて報告できます。
