"""Trace all 52 Latin letters from the generated concept into editable curves."""
from pathlib import Path
import hashlib, json, string
import cv2
import numpy as np
from PIL import Image
import pathops

ROOT=Path(__file__).resolve().parent
IMAGE=ROOT/'references/04-latin-cat-concept.png'
# Row bounds and shared baselines were checked against the original pixels.
ROWS=[(95,270,243),(280,447,414),(455,635,592),(644,811,766)]
LETTERS=string.ascii_uppercase+string.ascii_lowercase
SCALE=6.0

def smooth_contours(gray_crop):
    # Resolve the antialiased edge at subpixel precision before fitting curves.
    # Binary native-pixel contours otherwise preserve visible one-pixel steps.
    up=cv2.resize(gray_crop,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
    mask=(up<100).astype('uint8')
    contours,_=cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if abs(cv2.contourArea(contour))<32:continue
        q=cv2.approxPolyDP(contour,2.6,True)[:,0,:].astype(float)
        yield (q+.5)/4-.5

def trace():
    gray=cv2.cvtColor(np.asarray(Image.open(IMAGE).convert('RGB')),cv2.COLOR_RGB2GRAY)
    result={}
    for row,(top,bottom,baseline) in enumerate(ROWS):
        ink=(gray[top:bottom]<100).astype('uint8')
        # Horizontal occupied intervals keep i/j dots grouped with their stems.
        occupied=np.any(ink,axis=0)
        transitions=np.diff(np.r_[False,occupied,False].astype(int))
        starts=np.where(transitions==1)[0];ends=np.where(transitions==-1)[0]
        spans=[(int(a),int(b)) for a,b in zip(starts,ends) if b-a>10]
        assert len(spans)==13,(row,spans)
        for ch,(left,right) in zip(LETTERS[row*13:row*13+13],spans):
            ys=np.where(np.any(ink[:,left:right],axis=1))[0]
            y0=top+int(ys.min());y1=top+int(ys.max())+1
            # Use a generous crop so no contour meets its boundary.
            box=[left-3,y0-3,right+3,y1+3];x0,y0,x1,y1=box
            p=pathops.Path()
            for q in smooth_contours(gray[y0:y1,x0:x1]):
                q=np.array([[(x+x0-left)*SCALE+45,(baseline-y-y0)*SCALE] for x,y in q])
                if len(q)<3:continue
                p.moveTo(*q[0])
                for i in range(len(q)):
                    prev,point,nxt,after=q[(i-1)%len(q)],q[i],q[(i+1)%len(q)],q[(i+2)%len(q)]
                    a=point+(nxt-prev)/6;b=nxt-(after-point)/6
                    p.cubicTo(*a,*b,*nxt)
                p.close()
            p=pathops.simplify(p);p.convertConicsToQuads(.25)
            from fontTools.pens.recordingPen import RecordingPen
            rec=RecordingPen();p.draw(rec)
            result[ch]={'width':round(p.bounds[2]+45),'commands':rec.value,
                        'reference_box':box,'scale':SCALE,'baseline':baseline,
                        'reference':'references/04-latin-cat-concept.png',
                        'bounds':list(p.bounds)}
    assert set(result)==set(LETTERS)
    # The word sample has a matching cat-eared ampersand absent from alphabet rows.
    box=[328,849,424,952];x0,y0,x1,y1=box;baseline=949;scale=6.4
    p=pathops.Path()
    for q in smooth_contours(gray[y0:y1,x0:x1]):
        q=np.array([[(x+x0-331)*scale+45,(baseline-y-y0)*scale] for x,y in q])
        p.moveTo(*q[0])
        for i in range(len(q)):
            prev,point,nxt,after=q[(i-1)%len(q)],q[i],q[(i+1)%len(q)],q[(i+2)%len(q)]
            a=point+(nxt-prev)/6;b=nxt-(after-point)/6
            p.cubicTo(*a,*b,*nxt)
        p.close()
    p=pathops.simplify(p);p.convertConicsToQuads(.25)
    rec=RecordingPen();p.draw(rec)
    result['&']={'width':round(p.bounds[2]+45),'commands':rec.value,'reference_box':box,
                 'scale':scale,'baseline':baseline,'reference':'references/04-latin-cat-concept.png','bounds':list(p.bounds)}
    out=ROOT/'sources/latin-concept-outlines.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Traced',len(result),'letters from',hashlib.sha256(IMAGE.read_bytes()).hexdigest())

if __name__=='__main__':trace()
