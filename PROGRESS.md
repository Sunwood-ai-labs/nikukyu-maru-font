# にくきゅう丸 0.105 進捗

- [x] 生成画像04から全52英字と「&」を曲線として抽出。
- [x] 全角53字へ派生し、計106字を更新。
- [x] 比較画面の縮尺を修正し、曲線に残る画素の段差を平滑化。
- [x] 53字の1字ずつの左右比較7枚、全角とサイズ別1枚、全体比較1枚を実Chromeで確認。
- [x] LUNA MAXの独立目視レビューでも追加修正指摘なし。
- [x] 実TTFと元画像の53字のシルエット・縦横比・内孔数を照合。
- [x] 全7,547グリフ比較で変更106字、対象外7,441字形は不変。
- [x] 7,516 Unicode文字、cmap、glyphOrder、GSUBを維持。
- [x] 隔離コンパイルTTF/WOFF2と53+53字の再適用が一致。

証跡: [最終レビュー](outputs/latin-concept-review/REVIEW.md)、[回帰・再現性](outputs/latin-concept-review/regression.json)、[画像照合](outputs/latin-concept-review/reference-fidelity.json)、[スクショSHA](outputs/latin-concept-review/visual-verification.json)。

0.103/0.104の検証は各旧版の履歴として保持。0.104の英字比較HTMLは0.104のWOFF2を固定して参照する。
