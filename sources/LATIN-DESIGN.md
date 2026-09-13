# 0.104 猫アルファベット

A–Z / a–z の52字すべてに猫耳を持たせ、37字には巻きしっぽを組み合わせる。全角の52字も同じマスターから派生させる。

`latin-base-outlines.json` は0.103の位置・高さ調整済み英字52字を保存した編集可能な輪郭。元の生成見本に由来する A の猫耳と a の肉球入り輪郭を含む。0.103 TTF の SHA-256 は `52db75a3948c40e5cc9ec2436de187c0268a18efeb73602fa7c825af520bd8ba`。

`latin_cats.py` はこの固定マスターから毎回生成するため、実行を繰り返しても耳や尾が重複しない。耳は実際のインク上端に結合し、J/L と細い小文字は上部のステム、i/j は点、W/w は外側のピークに配置する。巻きしっぽは右側のインクに重ねて結合し、必要な字幅を確保する。全角字形は横方向のみ必要に応じて縮小し、1,000単位のセルに収める。

更新手順:

```powershell
.\.venv\Scripts\python.exe -X utf8 latin_cats.py
.\.venv\Scripts\python.exe -X utf8 build.py
.\.venv\Scripts\python.exe -X utf8 latin_review.py
```

`build.py --regenerate` でも `harmonize.py` から同じ猫英字生成処理を呼ぶ。輪郭調整後のブラウザースクリーンショットは自動更新されないため、新しいWOFF2の読み込みとSHAを確認して撮り直す。

最終候補のASCII・全角104字は `outputs/latin-review/page-1.png`〜`page-8.png` で確認した。`comparison.png` は元の生成見本と配布フォントの実テキストを並べた比較で、元画像にない英字へ猫モチーフを展開したことを示す。小サイズでは細い耳や尾の見え方が弱くなるため、用途は従来どおり太い見出し。
