"""Build compact browser proofs using unchanged reference pixels and real WOFF2 text."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'concept-review'
OUT.mkdir(exist_ok=True)
data = json.loads((ROOT / 'sources/kanji-concept-outlines.json').read_text(encoding='utf-8'))
digest = hashlib.sha256((ROOT / 'outputs/NikukyuMaru-Regular.woff2').read_bytes()).hexdigest()
style = '''@font-face{font-family:Niku;src:url('../NikukyuMaru-Regular.woff2?v=DIGEST')}
*{box-sizing:border-box}body{margin:0;padding:24px;background:#fff8eb;color:#342622;font:16px sans-serif}
h1{font-size:24px;margin:0 0 8px}p{margin:8px 0 16px;color:#806b60}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
article{background:white;border-radius:16px;padding:16px}h2{font:16px sans-serif;margin:0 0 8px}.pair{display:flex;justify-content:space-around;align-items:center;height:170px}
.crop{position:relative;overflow:hidden;flex:none}.crop img{position:absolute;max-width:none}.glyph{font:150px/1.55 Niku;display:inline-block}
.labels{display:flex;justify-content:space-around;font-size:13px;color:#806b60}.sentence{font:64px/1.5 Niku;margin:16px 0;padding:18px;background:#f3decd;border-radius:16px}.small{font:32px/1.6 Niku}
footer{font:12px monospace;color:#806b60;margin-top:12px}'''.replace('DIGEST', digest)
sentences = ['今日のお店でひと休み', '名前・年月日・住所']
for page in range(2):
    chars = '名今日月年店休住'[page * 4:page * 4 + 4]
    parts = ['<!doctype html><html lang="ja"><meta charset="utf-8"><title>追加漢字の生成見本比較</title>',
             f'<style>{style}</style><h1>追加生成した漢字 / 最終フォント 0.103 — {page+1}</h1>',
             '<p>左は生成画像の該当セルをそのまま表示。右は配布用 WOFF2 の実テキスト。</p><div class="grid">']
    for ch in chars:
        x0,y0,x1,y1 = data[ch]['reference_box']
        scale = 145 / max(x1-x0,y1-y0)
        parts.append(f'<article><h2>{ch} / U+{ord(ch):04X}</h2><div class="labels"><span>生成見本</span><span>実フォント</span></div><div class="pair"><div class="crop" style="width:{(x1-x0)*scale}px;height:{(y1-y0)*scale}px"><img alt="{ch}の元画像" src="../../references/03-kanji-refined.png" style="width:{1254*scale}px;height:{1254*scale}px;left:{-x0*scale}px;top:{-y0*scale}px"></div><span class="glyph">{ch}</span></div></article>')
    parts.append(f'</div><div class="sentence">{sentences[page]}</div><div class="small">にくきゅう丸で、ふんわり暮らそう。<br>価格：￥1,980（税込）　営業時間 10:00〜18:00</div>')
    parts.append('<footer id="status">読込中</footer><script>document.fonts.ready.then(()=>{document.getElementById("status").textContent="WOFF2 loaded: "+document.fonts.check("64px Niku")+" / SHA256: '+digest+'"})</script></html>')
    (OUT/f'final-page-{page+1}.html').write_text(''.join(parts),encoding='utf-8')
print('Created 2 final concept comparison pages')
