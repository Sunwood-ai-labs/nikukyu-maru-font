# 補完字形の出典

にくきゅう丸の主たる派生元は Mochiy Pop One です。主フォントに存在しない
JIS X 0208 非漢字、半角カナ、および CP932 で日常的に使われる記号を補うため、
丸ゴシック系の `Zen Maru Gothic Black` の輪郭を補完元として同梱しています。
既存の Mochiy/にくきゅう丸字形から派生できる全角記号と半角カナは、補完元を
使わず既存の字形を縮尺変換します。

## 一次配布元

- プロジェクト: [googlefonts/zen-marugothic](https://github.com/googlefonts/zen-marugothic)
- 固定コミット: [`553c872b216d1290e2902a466edcdc9682f0df6a`](https://github.com/googlefonts/zen-marugothic/commit/553c872b216d1290e2902a466edcdc9682f0df6a)
- フォントの固定 URL: [`ZenMaruGothic-Black.ttf`](https://raw.githubusercontent.com/googlefonts/zen-marugothic/553c872b216d1290e2902a466edcdc9682f0df6a/fonts/ttf/ZenMaruGothic-Black.ttf)
- ライセンスの固定 URL: [`OFL.txt`](https://raw.githubusercontent.com/googlefonts/zen-marugothic/553c872b216d1290e2902a466edcdc9682f0df6a/OFL.txt)
- 取得日: 2026-09-13

同梱ファイルの完全性は以下の SHA-256 で確認できます。

| ファイル | サイズ | SHA-256 |
| --- | ---: | --- |
| `vendor/ZenMaruGothic-Black.ttf` | 3,710,324 bytes | `6bd74fe76cd39ee0ec18775c3661d845343fb3f6f8fa09a3076638417baf741f` |
| `vendor/ZenMaruGothic-OFL.txt` | 4,402 bytes | `2a20cf7ce1909d8ee1e949095d340f7d7656705f7c810a2d6faf56800ad0cb3d` |

フォントに埋め込まれた著作権表示と `OFL.txt` の表示は次のとおりです。

> Copyright 2021 The Zen Maru Gothic Project Authors (https://github.com/googlefonts/zen-marugothic)

## ライセンスと取り込み方針

Zen Maru Gothic Black は SIL Open Font License 1.1 で配布されています。
`vendor/ZenMaruGothic-OFL.txt` を元の表示のまま同梱し、派生フォントには
元の Mochiy Pop One の表示・ライセンスとこの補完元の表示・ライセンスを残します。
最終フォント名は `Nikukyu Maru` とし、Zen Maru Gothic の予約名を使用しません。
補完元単体の販売はせず、派生フォントは OFL 1.1 の条件に従って配布します。

## カバレッジと例外

固定版 Zen Maru Gothic Black は JIS 非漢字の不足分のうち 215 字を直接収録し、
半角カナ 63 字と CP932 の企業・単位記号も収録します。`Å` は同じ補完元の
`Å`、`＃`・`＊`・`￥` などの全角形は既存 Mochiy 字形から派生します。
固定版にない `∑` は丸いギリシャ大文字 `Σ`、`∥` は既存の縦棒 2 本、
`≤`・`≥` は既存の `<`・`>` と `_` から作り、`㋿` は `令` と `和` を
角丸の枠内に配置して作ります。`⑩`–`⑳` と
`㊤`–`㊨` は Zen Maru の元輪郭をそのまま使います。これらの例外は
`supplemental.py` の `outline_for` に明記し、補完元の別字形を黙って置換しません。

`supplemental.py` の `add_missing_glyphs` は既存 UFO を変更せずに不足文字だけを
追加するため、6,355 漢字の再生成を避け