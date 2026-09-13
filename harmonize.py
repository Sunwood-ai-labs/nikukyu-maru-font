"""Keep related Unicode glyphs based on the same editable master outline."""
import unicodedata
import pathops
from fontTools.pens.transformPen import TransformPen

def harmonize(font, modifications):
    cmap={u:g.name for g in font for u in g.unicodes}
    def replace(cp,base,transform,width,kind):
        source=font[cmap[base]];target=font[cmap[cp]]
        target.clearContours();source.draw(TransformPen(target.getPen(),transform));target.width=width
        modifications[chr(cp)]=[kind,chr(base)]
    # Width variants share outlines, not merely a similar font family.
    for cp in range(0xff01,0xff5f):
        base=cp-0xfee0
        if cp not in cmap or base not in cmap:continue
        g=font[cmap[base]];scale=min(1,900/g.width)
        replace(cp,base,(scale,0,0,1,(1000-g.width*scale)/2,0),1000,'fullwidth-derived')
    small='ぁあぃいぅうぇえぉおっつゃやゅゆょよゎわゕかゖけァアィイゥウェエォオッツャヤュユョヨヮワヵカヶケ'
    for i in range(0,len(small),2):
        cp,base=map(ord,small[i:i+2]);g=font[cmap[base]]
        replace(cp,base,(.78,0,0,.78,g.width*.11,0),g.width,'small-kana-derived')
    # All precomposed voiced kana use the current base and explicit round marks.
    for cp in sorted(cmap):
        if not (0x3041<=cp<=0x30fa):continue
        parts=unicodedata.normalize('NFD',chr(cp))
        if len(parts)!=2 or ord(parts[1]) not in [0x3099,0x309a]:continue
        base=ord(parts[0]);g=font[cmap[base]]
        replace(cp,base,(1,0,0,1,0,0),g.width,'voiced-kana-derived')
        target=font[cmap[cp]]
        # Put marks above the base: no overlapping strokes or lost ring counters.
        y=g.getBounds(font)[3]+82
        x=g.width-125
        def oval(cx,cy,rx,ry):
            p=pathops.Path();pen=p.getPen();k=.55228475
            pen.moveTo((cx+rx,cy));pen.curveTo((cx+rx,cy+k*ry),(cx+k*rx,cy+ry),(cx,cy+ry))
            pen.curveTo((cx-k*rx,cy+ry),(cx-rx,cy+k*ry),(cx-rx,cy))
            pen.curveTo((cx-rx,cy-k*ry),(cx-k*rx,cy-ry),(cx,cy-ry))
            pen.curveTo((cx+k*rx,cy-ry),(cx+rx,cy-k*ry),(cx+rx,cy));pen.closePath();return p
        if ord(parts[1])==0x309a:
            p=pathops.op(oval(x,y,65,65),oval(x,y,34,34),pathops.PathOp.DIFFERENCE)
        else:
            p=pathops.op(oval(x-49,y,38,52),oval(x+42,y+13,38,52),pathops.PathOp.UNION)
        p.draw(target.getPen())

