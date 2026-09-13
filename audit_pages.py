"""Paginated actual webfont proof covering every Unicode mapping and alternate."""
from pathlib import Path
from fontTools.ttLib import TTFont
import html,json,hashlib
ROOT=Path(__file__).resolve().parent
out=ROOT/'outputs/audit';out.mkdir(exist_ok=True)
font=TTFont(ROOT/'outputs/NikukyuMaru-Regular.ttf')
digest=hashlib.sha256((ROOT/'outputs/NikukyuMaru-Regular.woff2').read_bytes()).hexdigest()
entries=[{'code':u,'glyph':g,'feature':''} for u,g in sorted(font.getBestCmap().items())]
entries += [{'code':0x3053,'glyph':'uni3053.alt','feature':'ss01'}, {'code':0x308b,'glyph':'uni308B.alt','feature':'ss01'}]
pages=[]
for start in range(0,len(entries),48):
    chunk=entries[start:start+48];i=len(pages)+1
    page=f'page-{i:02d}.html';pages.append({'page':page,'entries':chunk})
    body=''.join(f'<article><label>U+{e["code"]:04X} {e["feature"]}</label><div class="glyph" style="font-feature-settings:\'ss01\' {1 if e["feature"] else 0}">{html.escape(chr(e["code"]))}</div></article>' for e in chunk)
    (out/page).write_text('''<!doctype html><html lang="ja"><meta charset="utf-8"><title>にくきゅう丸 全文字監査</title><style>@font-face{font-family:Niku;src:url('../NikukyuMaru-Regular.woff2');font-weight:800}*{box-sizing:border-box}body{margin:0;padding:20px;background:#fff8eb;color:#342622;font:16px sans-serif}h1{font-size:22px;margin:0 0 12px}.grid{display:grid;grid-template-columns:repeat(8,1fr);gap:10px;max-width:1300px}article{height:104px;background:white;border-radius:10px;padding:5px 10px}label{font:12px Arial;color:#806b60}.glyph{font:800 62px/1.1 Niku;text-align:center;white-space:pre}footer{font-size:12px;margin-top:12px}</style>'''+f'<h1>全収録文字 / {i:02d} / {start+1}–{start+len(chunk)}</h1><div class="grid">'+body+'</div><footer id="status">読込中</footer><script>document.fonts.ready.then(()=>document.getElementById("status").textContent="Webフォント読込: "+document.fonts.check("800 62px Niku"))</script></html>',encoding='utf-8')
(out/'manifest.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
for page in pages:
    path=out/page['page']
    path.write_text(path.read_text(encoding='utf-8').replace("Regular.woff2'",f"Regular.woff2?v={digest}'"),encoding='utf-8')
(out/'font-hash.json').write_text(json.dumps({'woff2_sha256':digest,'page_count':len(pages),'unicode_count':len(font.getBestCmap())},indent=2),encoding='utf-8')
assert len(entries)==len(font.getBestCmap())+2
assert len({e['code'] for e in entries})==len(font.getBestCmap())
print(len(pages),'pages;',len(entries),'mapped glyph instances')
