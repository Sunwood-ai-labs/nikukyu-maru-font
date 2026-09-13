"""Offline deterministic font build. --regenerate rebuilds editable UFO from design.json."""
from pathlib import Path
import argparse, json, hashlib, unicodedata, shutil
import pathops
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from ufoLib2 import Font

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
CONFIG = json.loads((ROOT/'sources/design.json').read_text(encoding='utf-8'))
UFO = ROOT/'sources/NikukyuMaru-Regular.ufo'
COPYRIGHT = 'Copyright 2020 The Mochiypop Project Authors (https://github.com/fontdasu/Mochiypop). Modified 2026 for the Nikukyu Maru project.'

def boolean(a, b, mode=pathops.PathOp.UNION):
    return pathops.op(a, b, mode)

def stroke(p, width):
    q = pathops.Path(p)
    q.stroke(width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    q.convertConicsToQuads(.25)
    return pathops.simplify(q)

def soften(p, radius, weight):
    if not len(p): return p
    # Morphological opening rounds convex corners, then expands for plush weight.
    inner = boolean(p, stroke(p, radius*2), pathops.PathOp.DIFFERENCE)
    if not len(inner): inner = p
    result = boolean(inner, stroke(inner, (radius+weight)*2))
    for contour in pathops.simplify(p).contours:
        if not contour.clockwise and contour.area < 45000:
            result = boolean(result, contour)
    # Retain original counters, especially the small ring in handakuten.
    for contour in pathops.simplify(p).contours:
        if contour.clockwise:
            result = boolean(result, contour, pathops.PathOp.DIFFERENCE)
    return result

def ellipse(x, y, rx, ry):
    p = pathops.Path(); k = .55228474983
    p.moveTo(x+rx,y)
    p.cubicTo(x+rx,y+k*ry,x+k*rx,y+ry,x,y+ry)
    p.cubicTo(x-k*rx,y+ry,x-rx,y+k*ry,x-rx,y)
    p.cubicTo(x-rx,y-k*ry,x-k*rx,y-ry,x,y-ry)
    p.cubicTo(x+k*rx,y-ry,x+rx,y-k*ry,x+rx,y); p.close()
    return p

def ear(x,y,width,height):
    p=pathops.Path(); w=width/2
    p.moveTo(x-w,y-22)
    p.cubicTo(x-w,y+height*.24,x-w*.8,y+height*.92,x-w*.35,y+height)
    p.cubicTo(x+w*.03,y+height*1.10,x+w*.6,y+height*.30,x+w,y-22)
    p.close(); return p

def paw():
    p=pathops.Path(); p.moveTo(333,166)
    p.cubicTo(200,154,213,287,300,341)
    p.cubicTo(360,375,346,480,458,480)
    p.cubicTo(563,483,552,388,625,338)
    p.cubicTo(734,255,698,150,603,166)
    p.cubicTo(496,193,444,196,333,166); p.close()
    for x,y,rx,ry in [(233,485,68,88),(372,608,70,94),(541,608,70,94),(687,478,68,88)]:
        p=boolean(p,ellipse(x,y,rx,ry))
    return p

def cat():
    p=ellipse(490,390,325,265)
    p=boolean(p,ear(265,552,175,196)); p=boolean(p,ear(715,552,175,196))
    for x in [375,605]: p=boolean(p,ellipse(x,423,26,40),pathops.PathOp.DIFFERENCE)
    p=boolean(p,ellipse(490,330,35,26),pathops.PathOp.DIFFERENCE)
    return p

def character_set():
    chars=set(chr(x) for x in range(32,127))
    chars.update(chr(x) for x in range(0x3041,0x3097))
    chars.update(chr(x) for x in range(0x30a1,0x30fb))
    for a,b in [(0xff10,0xff19),(0xff21,0xff3a),(0xff41,0xff5a)]:
        chars.update(chr(x) for x in range(a,b+1))
    chars.update(CONFIG['extra_symbols']+CONFIG['kanji'])
    chars.update('\u00a0\ue000\ue001\U0001f43e')
    return sorted(chars,key=ord)

def generate_sources():
    base=TTFont(ROOT/'vendor/MochiyPopOne-Regular.ttf')
    gs=base.getGlyphSet(); cmap=base.getBestCmap()
    font=Font(); font.info.familyName=CONFIG['family']; font.info.styleName='Regular'
    font.info.unitsPerEm=1000; font.info.ascender=1200; font.info.descender=-350
    font.info.versionMajor=0; font.info.versionMinor=101; font.info.copyright=COPYRIGHT
    font.info.openTypeNameLicense='SIL Open Font License, Version 1.1'
    font.info.openTypeNameLicenseURL='https://openfontlicense.org'
    order=[]; missing=[]; mods={}
    nd=font.newGlyph('.notdef'); nd.width=1000
    pen=nd.getPen(); pen.moveTo((140,0));pen.lineTo((140,780));pen.lineTo((860,780));pen.lineTo((860,0));pen.closePath()
    pen.moveTo((215,75));pen.lineTo((785,75));pen.lineTo((785,705));pen.lineTo((215,705));pen.closePath()
    order.append('.notdef')
    for ch in character_set():
        cp=ord(ch); name=f'uni{cp:04X}' if cp<=0xffff else f'u{cp:05X}'
        if cp in [0xe000,0xe001,0x1f43e]:
            p=cat() if cp==0xe001 else paw(); width=1000
            if cp==0x1f43e:
                p=boolean(p.transform(.57,0,0,.57,15,315),p.transform(.57,0,0,.57,400,5))
        else:
            src_cp=32 if cp==0xa0 else cp
            if src_cp not in cmap: missing.append(ch); continue
            g=gs[cmap[src_cp]]; p=pathops.Path(); rec=DecomposingRecordingPen(gs); g.draw(rec); rec.replay(p.getPen()); width=g.width
            if len(p):
                is_kanji=ch in CONFIG['kanji']
                # Keep cramped diacritics and dense CJK counters open.
                radius=CONFIG['kanji_rounding_radius'] if is_kanji else CONFIG['rounding_radius']
                weight=CONFIG['kanji_weight_expansion'] if is_kanji else CONFIG['weight_expansion']
                if ch in '゛゜ゝゞヽヾ': radius,weight=12,8
                if ch not in '「」『』':
                    p=soften(p,radius,weight)
                mods[ch]=['rounded','weight']
                if ch in CONFIG['ears']:
                    basepath=pathops.Path(p)
                    for x in CONFIG['ears'][ch]:
                        ys=[y for y in range(1000,-201,-2) if basepath.contains((x,y))]
                        if not ys: raise ValueError(f'ear has no anchor: {ch} {x}')
                        p=boolean(p,ear(x,ys[0]-10,CONFIG['ear_width'],CONFIG['ear_height']))
                    mods[ch].append('ears')
                if ch in CONFIG['paws']:
                    x,y=CONFIG['paws'][ch]
                    for dx,dy in [(-45,82),(17,102),(72,62)]:
                        p=boolean(p,ellipse(x+dx,y+dy,23,29))
                    mods[ch].append('toe-pads')
                # Optical sidebearings: fixed CJK cell, proportional Latin widths.
                if cp<0x100:
                    b=p.bounds; dx=45-b[0]; width=round(b[2]-b[0]+90)
                    p=p.transform(1,0,0,1,dx,0)
                else:
                    p=p.transform(.90,0,0,.92,50,0)
        glyph=font.newGlyph(name); glyph.width=width; glyph.unicodes=[cp]
        p=pathops.simplify(p); p.convertConicsToQuads(.25)
        p.draw(glyph.getPen()); order.append(name)
    reference_file=ROOT/'sources/reference-outlines.json'
    if reference_file.exists():
        for ch, data in json.loads(reference_file.read_text(encoding='utf-8')).items():
            letter=ch.split('.')[0]
            name=f'uni{ord(letter):04X}'+('.alt' if ch.endswith('.alt') else '')
            p=pathops.Path()
            for op,*coords in data['commands']:
                getattr(p,op)(*coords)
            p=pathops.simplify(p)
            if name not in font:
                font.newGlyph(name);order.append(name)
            glyph=font[name];glyph.clearContours();glyph.width=data['width']
            p.draw(glyph.getPen());mods[ch]=['approved-reference-vector-outline']
    font.glyphOrder=order
    font.save(UFO,overwrite=True)
    (ROOT/'sources/modifications.json').write_text(json.dumps(mods,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'sources/omitted-requested.txt').write_text(''.join(missing),encoding='utf-8')
    print('Created UFO:',len(order),'glyphs. Omitted:',repr(''.join(missing)))

def compile_font():
    font=Font.open(UFO); order=font.glyphOrder; cmap={}; glyphs={}; metrics={}
    for name in order:
        g=font[name]; pen=TTGlyphPen(None); g.draw(Cu2QuPen(pen,max_err=.5,reverse_direction=True))
        glyphs[name]=pen.glyph()
        bp=BoundsPen(None);g.draw(bp); lsb=round(bp.bounds[0]) if bp.bounds else 0
        metrics[name]=(round(g.width),lsb)
        for u in g.unicodes: cmap[u]=name
    fb=FontBuilder(1000,isTTF=True); fb.setupGlyphOrder(order);fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1200,descent=-350,lineGap=0)
    fb.setupNameTable({'familyName':'Nikukyu Maru','styleName':'Regular',
        'uniqueFontIdentifier':'NikukyuMaru-Regular-0.101','fullName':'Nikukyu Maru Regular',
        'psName':'NikukyuMaru-Regular','version':'Version 0.101',
        'copyright':COPYRIGHT,'manufacturer':'Nikukyu Maru project',
        'description':'Plush rounded display typeface with cat-ear and paw accents. Modified from Mochiy Pop One.',
        'licenseDescription':'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
        'licenseInfoURL':'https://openfontlicense.org'})
    fb.font['name'].setName('にくきゅう丸',1,3,1,0x411)
    fb.font['name'].setName('にくきゅう丸 Regular',4,3,1,0x411)
    fb.setupOS2(version=4,sTypoAscender=1200,sTypoDescender=-350,sTypoLineGap=0,usWinAscent=1200,usWinDescent=350,
        usWeightClass=800,usWidthClass=5,fsType=0,fsSelection=0xC0,sxHeight=550,sCapHeight=810)
    fb.setupPost();fb.setupMaxp()
    if 'uni3053.alt' in glyphs:
        addOpenTypeFeaturesFromString(fb.font,'feature ss01 { sub uni3053 by uni3053.alt; sub uni308B by uni308B.alt; } ss01;')
    fb.font['head'].created=fb.font['head'].modified=3872188800
    fb.font.recalcTimestamp=False
    OUT.mkdir(exist_ok=True)
    fb.save(OUT/'NikukyuMaru-Regular.ttf')
    fb.font.flavor='woff2';fb.save(OUT/'NikukyuMaru-Regular.woff2')
    chars=''.join(chr(u) for u in sorted(cmap))
    (OUT/'characters.txt').write_text(chars+'\n',encoding='utf-8')
    lines=['# 対応文字一覧 — にくきゅう丸 0.101','',f'{len(cmap)} Unicode文字。空白・私用領域を含みます。','',
        '|文字|コードポイント|Unicode名|','|---|---|---|']
    for u in sorted(cmap):
        ch=chr(u); display=ch.replace('|','&#124;')
        if ch.isspace(): display='（空白）'
        lines.append(f'|{display}|U+{u:04X}|{unicodedata.name(ch,"PRIVATE USE")}|')
    (OUT/'CHARACTERS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'OFL.txt').write_text((ROOT/'vendor/OFL.txt').read_text(encoding='utf-8'),encoding='utf-8')
    # SVG paths are editable, and require no installed font for display.
    svgdir=OUT/'glyph-svg';svgdir.mkdir(exist_ok=True)
    for u,name in sorted(cmap.items()):
        sp=SVGPathPen(None);font[name].draw(sp)
        (svgdir/f'U+{u:04X}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {font[name].width} 1550"><g transform="translate(0 1200) scale(1 -1)"><path d="{sp.getCommands()}"/></g></svg>',encoding='utf-8')
    print('Compiled',len(cmap),'Unicode characters;',len(order),'glyphs')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--regenerate',action='store_true');args=parser.parse_args()
    if args.regenerate or not UFO.exists(): generate_sources()
    compile_font()
    from proof import make_proofs
    make_proofs()

