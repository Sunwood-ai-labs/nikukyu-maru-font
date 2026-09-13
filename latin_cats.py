"""Editable, deterministic cat-ear and curled-tail designs for all 52 Latin letters."""
from pathlib import Path
import json
import string
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parent
LETTERS = string.ascii_uppercase + string.ascii_lowercase
TAILS = set('BCDGJLOPQRSUbcdefghijklmnopqrstuvxyz')

def ear(x, y, width, height, lean):
    p = pathops.Path(); w = width / 2
    p.moveTo(x-w, y-27)
    p.cubicTo(x-w, y+height*.35, x-w*.58+lean, y+height*.92, x+lean, y+height)
    p.cubicTo(x+w*.42+lean, y+height*1.02, x+w*.7, y+height*.28, x+w, y-27)
    p.close()
    return p

def master_path(data):
    rec=RecordingPen()
    rec.value=[(op,tuple(tuple(v) for v in points)) for op,points in data['commands']]
    p=pathops.Path();rec.replay(p.getPen())
    return pathops.simplify(p)

def decorate(ch, data):
    p=master_path(data); x0,y0,x1,y1=p.bounds; span=x1-x0
    motifs=[]
    # Locate attachment points on actual ink, preserving each letter's skeleton.
    if ch != 'A':  # A already has the two approved ears.
        if ch in 'JLbdfhklijt':
            top=[x for x in range(round(x0),round(x1)+1,2) if p.contains((x,y1-35))]
            left,right=min(top),max(top)
            positions=[left+(right-left)*.23,left+(right-left)*.77]
        elif ch in 'Ww':
            positions=[x0+span*.10,x0+span*.90]
        else:
            positions=[x0+span*.24,x0+span*.76]
        width=min(115 if ch.isupper() else 100,(positions[1]-positions[0])*.85)
        width=max(38,width)
        height=min(116 if ch.isupper() else 95,width*1.18)
        for index,x in enumerate(positions):
            ys=[y for y in range(round(y1),round(y0)-1,-2) if p.contains((x,y))]
            if not ys:raise ValueError(f'No ear attachment for {ch}')
            top=ys[0]-10
            p=pathops.op(p,ear(x,top,width,height,(-1 if index==0 else 1)*width*.10),pathops.PathOp.UNION)
        motifs.append('paired-cat-ears')
    else:motifs.append('approved-paired-cat-ears')
    if ch in TAILS or ch=='A':
        y=y0+(y1-y0)*(.30 if ch in 'gjpqy' else .17)
        xs=[x for x in range(round(x0),round(x1)+1,2) if p.contains((x,y))]
        if not xs:raise ValueError(f'No tail attachment for {ch}')
        x=max(xs)-20; size=1 if ch.isupper() else .82
        tail=pathops.Path();tail.moveTo(x,y)
        tail.cubicTo(x+170*size,y-92*size,x+240*size,y+52*size,x+174*size,y+147*size)
        tail.cubicTo(x+152*size,y+178*size,x+116*size,y+168*size,x+117*size,y+137*size)
        tail.stroke(66*size,pathops.LineCap.ROUND_CAP,pathops.LineJoin.ROUND_JOIN,4)
        tail.convertConicsToQuads(.25)
        p=pathops.op(p,pathops.simplify(tail),pathops.PathOp.UNION)
        motifs.append('curled-cat-tail')
    p=pathops.simplify(p);p.convertConicsToQuads(.25)
    b=p.bounds
    if b[0]<40:p=p.transform(1,0,0,1,40-b[0],0)
    return p,round(p.bounds[2]+45),motifs

def apply_latin_cats(font, modifications):
    masters=json.loads((ROOT/'sources/latin-base-outlines.json').read_text(encoding='utf-8'))
    assert set(masters)==set(LETTERS)
    for ch in LETTERS:
        p,width,motifs=decorate(ch,masters[ch]);g=font[f'uni{ord(ch):04X}']
        g.clearContours();p.draw(g.getPen());g.width=width
        modifications[ch]=['cat-latin-design',*motifs]

def update_current_ufo():
    from ufoLib2 import Font
    font=Font.open(ROOT/'sources/NikukyuMaru-Regular.ufo')
    mods=json.loads((ROOT/'sources/modifications.json').read_text(encoding='utf-8'))
    apply_latin_cats(font,mods)
    for ch in LETTERS:
        cp=ord(ch);source=font[f'uni{cp:04X}'];target=font[f'uni{cp+0xfee0:04X}']
        scale=min(1,900/source.width)
        target.clearContours();source.draw(TransformPen(target.getPen(),(scale,0,0,1,(1000-source.width*scale)/2,0)));target.width=1000
        mods[chr(cp+0xfee0)]=['fullwidth-derived',ch]
    font.info.versionMinor=104
    from fontTools.ufoLib import UFOWriter
    with UFOWriter(ROOT/'sources/NikukyuMaru-Regular.ufo',formatVersion=3) as writer:
        glyphset=writer.getGlyphSet()
        for ch in LETTERS:
            for cp in (ord(ch),ord(ch)+0xfee0):
                g=font[f'uni{cp:04X}'];glyphset.writeGlyph(g.name,g,g.drawPoints)
        glyphset.writeContents();writer.writeInfo(font.info)
    (ROOT/'sources/modifications.json').write_text(json.dumps(mods,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Updated 52 ASCII and 52 fullwidth letters')

if __name__=='__main__':update_current_ufo()
