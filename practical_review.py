"""Paginate the existing corpus for complete browser screenshot inspection."""
from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'practical-review'
OUT.mkdir(exist_ok=True)
r = json.loads((ROOT / 'outputs/japanese-validation.json').read_text(encoding='utf-8'))
digest = r['artifacts']['woff2']['sha256']
style = '''@font-face{font-family:Niku;src:url('../NikukyuMaru-Regular.woff2?v=DIGEST')}
*{box-sizing:border-box}body{background:#fff8eb;color:#342622;padding:22px;margin:0;font:15px sans-serif}h1{font-size:25px;margin:0 0 12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}article{background:white;border:1px solid #e8dacd;border-radius:12px;padding:15px}
h2{font-size:16px;margin:0 0 6px}p{font-size:12px;color:#806b60;margin:8px 0}.text{font:34px/1.6 Niku;overflow-wrap:anywhere;background:#fffaf3;padding:8px;border-radius:8px}.nfc{background:#f1f6ee}.status{color:#277559}footer{font:11px monospace;margin-top:14px}'''.replace('DIGEST',digest)
for cat in r['category_summary']:
    if cat['id'] not in r['cases']:
        continue
    parts = ['<!doctype html><html lang="ja"><meta charset="utf-8">',f'<title>{cat["title"]}の実表示検証</title><style>{style}</style><h1>{cat["title"]} / 最終フォント 0.103</h1><div class="grid">']
    for case in r['cases'][cat['id']]:
        parts.append(f'<article><h2>{escape(case["title"])}</h2><p>{escape(case["note"])}</p><div class="text">{escape(case["text"])}</div>')
        if case['nfc_changed']:
            parts.append(f'<p>NFC 正規化後</p><div class="text nfc">{escape(case["nfc_text"])}</div>')
        parts.append(f'<p class="status">TTF 未収録: {len(case["missing_codepoints"])} / {len(case["codepoints"])}文字</p></article>')
    parts.append('</div><footer id="status">読込中</footer><script>document.fonts.ready.then(()=>{document.getElementById("status").textContent="WOFF2 loaded: "+document.fonts.check("34px Niku")+" / SHA256: '+digest+'"})</script></html>')
    (OUT/f'{cat["id"]}.html').write_text(''.join(parts),encoding='utf-8')
print('Created',len(r['cases']),'corpus proof pages')
