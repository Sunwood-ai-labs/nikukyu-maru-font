"""Compare every rendered Latin glyph with its own generated-image reference."""
from pathlib import Path
import hashlib,json
import cv2
import numpy as np
from PIL import Image,ImageFont,ImageDraw

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/latin-concept-review'

def crop(mask):
    ys,xs=np.where(mask)
    return mask[ys.min():ys.max()+1,xs.min():xs.max()+1]

def holes(mask):
    contours,hierarchy=cv2.findContours(mask.astype('uint8'),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    return sum(1 for i,c in enumerate(contours) if hierarchy[0][i][3]>=0 and cv2.contourArea(c)>3)

def verify():
    data=json.loads((ROOT/'sources/latin-concept-outlines.json').read_text(encoding='utf-8'))
    image=ROOT/'references/04-latin-cat-concept.png';ttf=ROOT/'outputs/NikukyuMaru-Regular.ttf'
    gray=np.asarray(Image.open(image).convert('L'));font=ImageFont.truetype(str(ttf),250)
    records=[]
    for ch,d in data.items():
        x0,y0,x1,y1=d['reference_box'];ref=crop(gray[y0:y1,x0:x1]<100)
        im=Image.new('L',(450,450));ImageDraw.Draw(im).text((30,300),ch,font=font,fill=255,anchor='ls')
        actual=crop(np.asarray(im)>127)
        target=cv2.resize(ref.astype('uint8'),(actual.shape[1],actual.shape[0]),interpolation=cv2.INTER_NEAREST).astype(bool)
        iou=float(np.logical_and(target,actual).sum()/np.logical_or(target,actual).sum())
        aspect_ref=ref.shape[1]/ref.shape[0];aspect_actual=actual.shape[1]/actual.shape[0]
        aspect_error=abs(aspect_actual/aspect_ref-1)
        record={'character':ch,'codepoint':f'U+{ord(ch):04X}','reference_box':d['reference_box'],
                'bbox_normalized_iou':round(iou,5),'aspect_ratio_error':round(aspect_error,5),
                'reference_holes':holes(ref),'font_holes':holes(actual)}
        record['pass']=iou>=.90 and aspect_error<=.04 and record['reference_holes']==record['font_holes']
        records.append(record)
    report={'version':'0.105','method':'Actual TTF raster at 250px vs individual reference crop; bounding-box-normalized silhouette IoU plus aspect ratio and hole count. Does not replace screenshot review.',
            'reference_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'ttf_sha256':hashlib.sha256(ttf.read_bytes()).hexdigest(),
            'glyphs_checked':len(records),'min_iou':min(r['bbox_normalized_iou'] for r in records),
            'pass':all(r['pass'] for r in records),'glyphs':records}
    OUT.mkdir(exist_ok=True);(OUT/'reference-fidelity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k!='glyphs'},ensure_ascii=False,indent=2))
    print('Failures:',[r for r in records if not r['pass']])
    assert report['pass']

if __name__=='__main__':verify()
