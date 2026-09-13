"""Build the original concept / actual webfont side-by-side overview."""
from pathlib import Path
import hashlib,json,string
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/latin-concept-review';OUT.mkdir(exist_ok=True)
digest=hashlib.sha256((ROOT/'outputs/NikukyuMaru-Regular.woff2').read_bytes()).hexdigest()
version=json.loads((ROOT/'sources/design.json').read_text())['version']
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><style>
@font-face{font-family:Niku;src:url('../NikukyuMaru-Regular.woff2?v=DIGEST')}
*{box-sizing:border-box}body{margin:0;padding:24px;background:#faf4e9;color:#241b17;font:16px sans-serif}h1{font-size:27px;margin:0 0 8px}p{color:#76695f;margin:0 0 18px}.layout{display:grid;grid-template-columns:1fr 1fr;gap:20px}.panel{background:white;border:1px solid #e6d9c6;border-radius:18px;padding:20px;height:603px}h2{font-size:18px;margin:0 0 26px}.reference img{width:100%;height:505px;object-fit:contain}.row{display:flex;justify-content:space-between;font:68px/1.3 Niku;color:#16120f}.samples{font:40px/1.6 Niku;margin-top:16px;display:flex;justify-content:space-between}.jp{font:24px/1.6 Niku;margin-top:12px}footer{font:11px monospace;margin-top:16px;color:#76695f}</style>
<h1>にくきゅう丸 VERSION — 生成見本から、実際に使えるフォントへ。</h1><p>同じ52字を比較。ぽってりした骨格・幅広い猫耳・文字につながるしっぽを、編集できる輪郭として採用。</p><div class="layout"><section class="panel reference"><h2>生成したコンセプト画像</h2><img src="../../references/04-latin-cat-concept.png"></section><section class="panel"><h2>実際の配布用 WOFF2 / ブラウザーの文字表示</h2>'''.replace('DIGEST',digest).replace('VERSION',version)
alphabet=string.ascii_uppercase+string.ascii_lowercase
for n in range(4):html+='<div class="row">'+''.join(f'<span>{ch}</span>' for ch in alphabet[n*13:n*13+13])+'</div>'
html+='''<div class="samples"><span>CAT &amp; map</span><span>cozy cat cafe</span></div><div class="jp">ねこのいる暮らし / にくきゅう丸</div></section></div><footer id="status">読込中</footer>'''
html+='<script>document.fonts.ready.then(()=>{document.getElementById("status").textContent="WOFF2 loaded: "+document.fonts.check("60px Niku")+" / SHA256: '+digest+'"})</script></html>'
(OUT/'comparison.html').write_text(html,encoding='utf-8',newline='\n')
print(version,digest)
