"""Extract editable vector outlines from the approved reference; never alter it."""
from pathlib import Path
import cv2, numpy as np, json
from PIL import Image

ROOT=Path(__file__).resolve().parent
# Bounds observed in original 1254px reference. Scale is shared within a row.
spec={
 'こ':([332,220,516,403],4.05), 'る':([955,211,1150,408],4.05),
 'く':([553,107,587,155],20), 'き':([586,105,627,155],20),
 'ゅ':([627,115,665,155],20), 'う':([665,106,700,155],20),
 '丸':([700,105,748,155],20),
 'ね':([105,195,325,405],4.05), 'の':([522,205,735,403],4.05),
 'い':([738,230,949,403],4.05), '暮':([298,416,544,647],4.05),
 'ら':([551,447,741,646],4.05), 'し':([757,451,958,648],4.05),
 'に':([398,696,517,809],7.25), 'ゃ':([518,722,619,812],7.25),
 'ん':([618,690,746,810],7.25), 'こ.alt':([750,701,861,812],7.25),
 'ネ':([204,818,329,948],7.25), 'コ':([331,840,438,943],7.25),
 'と':([444,837,540,944],7.25), 'お':([544,826,673,947],7.0),
 'ひ':([674,838,800,945],7.25), 'る.alt':([799,831,913,947],7.25),
 'C':([365,1008,436,1088],9.6), 'A':([435,999,512,1088],9.6),
 'T':([506,1009,580,1088],9.6), '&':([597,1007,677,1087],9.6),
 'n':([697,1021,761,1087],9.6), 'a':([761,1017,819,1087],9.6),
 'p':([819,1021,889,1100],9.6),
 '0':([261,1099,334,1191],9.6), '1':([341,1107,387,1190],9.6),
 '2':([399,1107,468,1190],9.6), '3':([474,1107,541,1190],9.6),
 '4':([547,1107,622,1190],9.6), '5':([626,1108,693,1190],9.6),
 '6':([699,1106,770,1191],9.6), '7':([775,1108,845,1190],9.6),
 '8':([847,1106,919,1192],9.6), '9':([921,1107,993,1190],9.6),
}
alpha=np.array(Image.open(ROOT/'references/01-nikukyu.png'))[:,:,3]
out={}
for ch,(box,scale) in spec.items():
    x0,y0,x1,y1=box
    mask=(alpha[y0:y1,x0:x1]>128).astype('uint8')
    # Reject neighboring letters clipped by the extraction rectangle.
    count,labels,stats,_=cv2.connectedComponentsWithStats(mask)
    for j in range(1,count):
        xx,yy,ww,hh,area=stats[j]
        if xx==0 or yy==0 or xx+ww==mask.shape[1] or yy+hh==mask.shape[0]:
            mask[labels==j]=0
    mask=(cv2.GaussianBlur(mask.astype(float),(5,5),.75)>.5).astype('uint8')
    contours,hierarchy=cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    points=[]; bounds=[]
    for c in contours:
        if abs(cv2.contourArea(c))<2: continue
        # Subpixel curves through simplified points remove the pixel staircase.
        q=cv2.approxPolyDP(c,.85,True)[:,0,:].astype(float)
        if len(q)<3: continue
        points.append(q);bounds.extend(q.tolist())
    b=np.array(bounds);xmin,ymin=b.min(axis=0);xmax,ymax=b.max(axis=0)
    # Common baseline; p descender retained, small ya stays small.
    baseline=1083-y0 if ch in 'CAT&nap' else ymax
    commands=[]
    for q in points:
        q=np.array([[(x-xmin)*scale+45,(baseline-y)*scale] for x,y in q])
        commands.append(['moveTo',*q[0].tolist()])
        for i in range(len(q)):
            prev=q[(i-1)%len(q)];p=q[i];n=q[(i+1)%len(q)];n2=q[(i+2)%len(q)]
            a=p+(n-prev)/6;z=n-(n2-p)/6
            commands.append(['cubicTo',*a.tolist(),*z.tolist(),*n.tolist()])
        commands.append(['close'])
    out[ch]={'width':round((xmax-xmin)*scale+90),'commands':commands,'reference_box':box,'scale':scale}
(ROOT/'sources/reference-outlines.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Traced',len(out),'approved reference glyphs')

