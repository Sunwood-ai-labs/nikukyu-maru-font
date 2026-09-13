"""Create a browser comparison without modifying the reference image pixels."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
rows=[('ねこのいる',(98,188,1065,216)),('暮らし',(295,415,680,239)),('にゃんこ',(389,686,482,126)),('ネコとおひるね',(202,814,854,133)),('CAT & nap',(360,995,563,99)),('0123456789',(253,1096,780,101))]
out=ROOT/'outputs'/'comparison';out.mkdir(exist_ok=True)
for page in range(3):
    parts=['''<!doctype html><html lang="ja"><meta charset="utf-8"><title>生成見本と実フォント比較</title><style>
@font-face{font-family:Nikukyu;src:url('../NikukyuMaru-Regular.woff2');font-weight:800}
*{box-sizing:border-box}body{margin:0;padding:20px;background:#f6f1e9;color:#27211e;font:15px Arial,sans-serif}h1{font:22px sans-serif;margin:0 0 12px}section{background:white;padding:12px;margin:12px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.stage{height:220px;display:flex;align-items:center;justify-content:center;background:#fff8eb;overflow:hidden}.crop{position:relative;overflow:hidden;flex:none}.crop img{position:absolute;max-width:none}.actual{font-family:Nikukyu;font-weight:800;white-space:nowrap;line-height:1.55}.label{margin:6px 0;color:#75685e}nav a{margin-right:24px;color:inherit}footer{font-size:13px}</style><h1>生成見本 / 現行フォント — '''+str(page+1)+'''</h1><nav><a href="page-1.html">1: 大見出し</a><a href="page-2.html">2: かな</a><a href="page-3.html">3: 英数字</a></nav><p>左: 採用画像の該当部分（元画像をCSSで表示）　右: WOFF2の実テキスト。縦横比を維持し、見える高さを合わせます。</p>''']
    for text,(x,y,w,h) in rows[page*2:page*2+2]:
        scale=min(510/w,190/h)
        parts.append(f'<section><b>{text}</b><div class="pair"><div><p class="label">生成見本</p><div class="stage"><div class="crop" style="width:{w*scale}px;height:{h*scale}px"><img src="../../references/01-nikukyu.png" style="width:{1254*scale}px;height:{1254*scale}px;left:{-x*scale}px;top:{-y*scale}px"></div></div></div><div><p class="label">現行フォント</p><div class="stage"><span class="actual" data-height="{h*scale}">{text}</span></div></div></div></section>')
    parts.append('''<footer id="status">読込中</footer><script>document.fonts.ready.then(()=>{const c=document.createElement('canvas'),ctx=c.getContext('2d');for(const el of document.querySelectorAll('.actual')){ctx.font='800 100px Nikukyu';const m=ctx.measureText(el.textContent);const height=m.actualBoundingBoxAscent+m.actualBoundingBoxDescent;const sz=Math.min(Number(el.dataset.height)*100/height,(el.parentElement.clientWidth-20)*100/m.width);el.style.fontSize=sz+'px'}document.getElementById('status').textContent='フォント読込: '+document.fonts.check('800 100px Nikukyu')+' / 自動調整完了'})</script></html>''')
    html=''.join(parts)
    if page==1: html=html.replace('.actual{','.actual{font-feature-settings:"ss01" 1;')
    (out/f'page-{page+1}.html').write_text(html,encoding='utf-8')
print('Created 3 comparison pages')

