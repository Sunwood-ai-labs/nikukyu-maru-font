"""Trace the eight selected and visually approved kanji concept outlines."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
IMAGE=ROOT/'references/03-kanji-refined.png'
CHARS='名前今日月年時間店営業休価格住所'
SELECTED=set('名今日月年店休住')

def trace():
    gray=np.asarray(Image.open(IMAGE).convert('L'))
    xs=[30,330,627,919,1230];ys=[45,350,635,917,1220]
    out={}
    for index,ch in enumerate(CHARS):
        if ch not in SELECTED:continue
        col,row=index%4,index//4
        box=[xs[col],ys[row],xs[col+1],ys[row+1]]
        x0,y0,x1,y1=box
        mask=(gray[y0:y1,x0:x1]<128).astype('uint8')
        mask=(cv2.GaussianBlur(mask.astype(float),(5,5),.7)>.5).astype('uint8')
        contours,_=cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        points=[cv2.approxPolyDP(c,.7,True)[:,0,:].astype(float) for c in contours if abs(cv2.contourArea(c))>=3]
        points=[p for p in points if len(p)>=3]
        all_points=np.concatenate(points)
        xmin,ymin=all_points.min(axis=0);xmax,ymax=all_points.max(axis=0)
        scale=min(900/(xmax-xmin),880/(ymax-ymin))
        dx=(1000-(xmax-xmin)*scale)/2
        commands=[]
        for q in points:
            q=np.array([[(x-xmin)*scale+dx,(ymax-y)*scale] for x,y in q])
            commands.append(['moveTo',*q[0].tolist()])
            for i,p in enumerate(q):
                prev=q[(i-1)%len(q)];n=q[(i+1)%len(q)];n2=q[(i+2)%len(q)]
                a=p+(n-prev)/6;z=n-(n2-p)/6
                commands.append(['cubicTo',*a.tolist(),*z.tolist(),*n.tolist()])
            commands.append(['close'])
        out[ch]={'width':1000,'commands':commands,'reference_box':box,'scale':scale,
                 'reference':'references/03-kanji-refined.png','status':'selected-after-font-render-review'}
    path=ROOT/'sources/kanji-concept-outlines.json'
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Traced',len(out),'reviewed kanji; build.py uses the use_kanji_concept configuration')

if __name__=='__main__':trace()
