"""Create compact browser proofs for all ASCII and fullwidth cat letters."""
from pathlib import Path
import hashlib,json,string
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/latin-review';OUT.mkdir(exist_ok=True)
digest=hashlib.sha256((ROOT/'outputs/NikukyuMaru-Regular.woff2').read_bytes()).hexdigest()
words=['BLACK CAT & COFFEE','JUMP OVER THE LAZY FOX','cozy morning cat cafe','quick brown fox jumps']
alphabet=string.ascii_uppercase+string.ascii_lowercase
for n in range(8):
    chars=alphabet[(n%4)*13:(n%4)*13+13]
    word=words[n%4]
    if n>=4:
        chars=''.join(chr(ord(ch)+0xfee0) for ch in chars)
        word=''.join(chr(ord(ch)+0xfee0) if ch.isascii() and ch.isalpha() else ch for ch in word)
    html='''<!doctype html><html lang="ja"><meta charset="utf-8"><style>
@font-face{font-family:Niku;src:url('../NikukyuMaru-Regular.woff2?v=DIGEST')}
*{box-sizing:border-box}body{margin:0;padding:22px;background:#fff8eb;color:#342622;font:15px sans-serif}h1{font-size:24px;margin:0 0 8px}p{color:#806b60;margin:8px 0 14px}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:12px}article{background:white;border-radius:14px;padding:12px;height:205px;overflow:hidden}label{display:block;font:14px sans-serif;color:#806b60}.glyph{font:112px/1.55 Niku;display:flex;justify-content:center}.words{font:45px/1.6 Niku;background:#f3decd;padding:14px 20px;margin-top:16px;border-radius:14px}.small{font:26px/1.6 Niku;margin-top:10px}footer{font:11px monospace;color:#806b60;margin-top:12px}</style>'''.replace('DIGEST',digest)
    html+=f'<h1>猫アルファベット 0.104 / {n+1} — {chars[0]}–{chars[-1]}</h1><p>配布用WOFF2の実テキスト。耳・巻きしっぽと、文字の読み分けを確認。</p><div class="grid">'
    for ch in chars:html+=f'<article><label>{ch} / U+{ord(ch):04X}</label><span class="glyph">{ch}</span></article>'
    html+=f'</div><div class="words" style="font-size:{36 if n>=4 else 45}px">{word}</div><div class="small">Il1 ij ji rn m / CGOQ bd pq / Hello, にくきゅう丸！ / 0123456789</div><footer id="status">読込中</footer>'
    html+='<script>document.fonts.ready.then(()=>{document.getElementById("status").textContent="WOFF2 loaded: "+document.fonts.check("112px Niku")+" / SHA256: '+digest+'"})</script></html>'
    (OUT/f'page-{n+1}.html').write_text(html,encoding='utf-8',newline='\n')
print('Created 8 alphabet proof pages',digest)

overview='''<!doctype html><html lang="ja"><meta charset="utf-8"><style>
@font-face{font-family:Niku;src:url('../NikukyuMaru-Regular.woff2?v=DIGEST')}
*{box-sizing:border-box}body{margin:0;padding:26px;background:#fff8eb;color:#342622;font:16px sans-serif}h1{font-size:27px;margin:0 0 10px}p{color:#806b60}.layout{display:grid;grid-template-columns:500px 1fr;gap:24px}.reference{background:white;border-radius:20px;padding:16px}.reference img{width:100%;height:505px;object-fit:contain}.reference p{margin:0 0 8px}.new{padding:18px 22px;border-radius:20px;background:#f3decd}.row{display:flex;justify-content:space-between;font:48px/1.6 Niku}.sample{font:44px/1.4 Niku;margin-top:12px}.small{font:24px/1.5 Niku}footer{font:11px monospace;margin-top:16px;color:#806b60}</style>
<h1>にくきゅう丸 0.104 — 全アルファベットに猫耳を。</h1><p>生成したコンセプト見本の丸い骨格・猫耳・肉球を引き継ぎ、大小52字へ展開。37字には巻きしっぽ。</p><div class="layout"><div class="reference"><p>元の生成見本</p><img src="../../references/01-nikukyu.png"></div><div class="new"><p>実際の配布用 WOFF2 / A–Z・a–z</p>'''.replace('DIGEST',digest)
for n in range(4):
    overview+='<div class="row">'+''.join(f'<span>{ch}</span>' for ch in alphabet[n*13:n*13+13])+'</div>'
overview+='''<div class="sample">CAT &amp; map<br>cozy cat cafe</div><div class="small">ねこのいる暮らし<br>Hello, にくきゅう丸！</div></div></div><footer id="status">読込中</footer>'''
overview+='<script>document.fonts.ready.then(()=>{document.getElementById("status").textContent="WOFF2 loaded: "+document.fonts.check("48px Niku")+" / SHA256: '+digest+'"})</script></html>'
(OUT/'comparison.html').write_text(overview,encoding='utf-8',newline='\n')
