"""Render the built TTF with FreeType (Pillow); no fallback fonts in specimen text."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import json, hashlib, unicodedata
from artifact_io import save_png
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'
FONT=OUT/'NikukyuMaru-Regular.ttf'
INK='#342622'; CREAM='#FFF8EB'; PINK='#EF927F'; MUTED='#806B60'

def make_proofs():
    ft=TTFont(FONT); cmap=ft.getBestCmap()
    alt=TTFont(FONT)
    for table in alt['cmap'].tables:
        if table.isUnicode():
            for cp in [0x3053,0x308b]:
                if cp in table.cmap: table.cmap[cp]=f'uni{cp:04X}.alt'
    alt_path=ROOT/'work/proof-alternates.ttf';alt_path.parent.mkdir(exist_ok=True);alt.save(alt_path)
    def face(size): return ImageFont.truetype(str(FONT),size)
    def ui(size): return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)
    def jp(size): return ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',size)
    def txt(d,xy,text,size,fill=INK):
        missing=[c for c in text if ord(c) not in cmap]
        assert not missing,repr(missing)
        chosen=ImageFont.truetype(str(alt_path),size) if text in ['にゃんこ','ネコとおひるね'] else face(size)
        d.text(xy,text,font=chosen,fill=fill,anchor='lt')
    im=Image.new('RGB',(1600,1860),CREAM); d=ImageDraw.Draw(im)
    d.rounded_rectangle((65,58,398,105),radius=23,fill=INK)
    d.text((87,70),'NIKUKYU MARU / '+json.loads((ROOT/'sources/design.json').read_text(encoding='utf-8'))['version'],font=ui(23),fill=CREAM)
    d.text((1210,73),'TYPE SPECIMEN 01',font=ui(22),fill=MUTED)
    txt(d,(102,187),'ねこのいる',252)
    txt(d,(93,478),'暮らし',280)
    txt(d,(1010,493),'\ue000',320,PINK)
    d.line((90,850,1510,850),fill='#D8C9B9',width=2)
    txt(d,(92,910),'にくきゅう丸',128)
    txt(d,(1070,953),'\ue001',150,PINK)
    txt(d,(97,1108),'にゃんこ',96)
    txt(d,(644,1108),'ネコとおひるね',96)
    d.rounded_rectangle((76,1301,1524,1706),radius=43,fill='#F4DECC')
    txt(d,(122,1375),'CAT & nap',146)
    txt(d,(127,1570),'0123456789',113)
    d.text((95,1775),'PLUSH LETTERS. LITTLE PAWS.',font=ui(23),fill=MUTED)
    d.text((1047,1775),f'{len(cmap)} CHARACTERS / TTF',font=ui(23),fill=MUTED)
    save_png(im,OUT/'specimen.png')
    groups=[('HIRAGANA',[u for u in cmap if 0x3041<=u<=0x3096]),
        ('KATAKANA',[u for u in cmap if 0x30a1<=u<=0x30fa]),
        ('LATIN + NUMBERS',[u for u in cmap if 33<=u<=126]),
        ('FULLWIDTH + KANJI',[u for u in cmap if 0xff10<=u<=0xff5a or 0x4e00<=u<=0x9fff]),
        ('SYMBOLS',[u for u in cmap if not (0x3041<=u<=0x3096 or 0x30a1<=u<=0x30fa or 33<=u<=126 or 0xff10<=u<=0xff5a or 0x4e00<=u<=0x9fff)])]
    groups = [(title + f' / {start//100+1}', sorted(codes)[start:start+100])
              for title,codes in groups for start in range(0,len(codes),100)]
    for idx,(title,codes) in enumerate(groups,1):
        codes=sorted(codes); rows=(len(codes)+9)//10
        im=Image.new('RGB',(1500,150+rows*150),CREAM);d=ImageDraw.Draw(im)
        d.text((50,42),f'{idx:02d} / {title}',font=ui(32),fill=INK)
        for i,u in enumerate(codes):
            x=40+(i%10)*143; y=130+(i//10)*150
            d.rounded_rectangle((x,y,x+132,y+138),radius=12,fill='white')
            d.text((x+11,y+7),f'{u:04X}',font=ui(15),fill=MUTED)
            d.text((x+66,y+80),chr(u),font=face(81),fill=INK,anchor='mm')
        save_png(im,OUT/f'charset-{idx:02d}.png')
    im=Image.new('RGB',(2100,1340),CREAM);d=ImageDraw.Draw(im)
    d.text((55,30),'SIZE + SPACING PROOF / REAL TTF',font=ui(28),fill=INK)
    text='にゃんこ ねこのいる暮らし。ぱぴぷぺぽ がぎぐげご'
    y=115
    for size in [16,24,32,48,72]:
        d.text((55,y),f'{size}px',font=ui(20),fill=MUTED)
        txt(d,(170,y),text,size);y+=size+64
    for sample in ['ぁあぃいぅうぇえぉおゃやゅゆょよっつ','ぱばだがざ パバダガザ ヴヷヸヹヺ','AVATAR Toffee WWW iii 0O 1Il & @ %','猫 肉 球 暮 丸 日 月 春 夏 秋 冬']:
        txt(d,(55,y),sample,52);y+=105
    save_png(im,OUT/'size-proof.png')
    # Quantitative checks include Windows clipping bounds and every character raster.
    errors=[]; bounds=[]
    for u,name in cmap.items():
        g=ft['glyf'][name];g.recalcBounds(ft['glyf']);w=ft['hmtx'][name][0]
        if g.numberOfContours:
            if g.yMax>ft['OS/2'].usWinAscent or g.yMin< -ft['OS/2'].usWinDescent:errors.append(f'vertical clipping U+{u:04X}')
            if g.xMin<0 or g.xMax>w:errors.append(f'horizontal overhang U+{u:04X}: {g.xMin}..{g.xMax}/{w}')
            if face(64).getmask(chr(u)).getbbox() is None:errors.append(f'empty raster U+{u:04X}')
            bounds.append([u,g.xMin,g.yMin,g.xMax,g.yMax])
    web=TTFont(OUT/'NikukyuMaru-Regular.woff2')
    assert web.getBestCmap()==cmap
    for name in ['uni3053.alt','uni308B.alt']:
        g=ft['glyf'][name];g.recalcBounds(ft['glyf'])
        assert g.numberOfContours>0 and g.xMin>=0 and g.xMax<=ft['hmtx'][name][0]
        assert g.yMin>=-350 and g.yMax<=1200
    assert any(f.FeatureTag=='ss01' for f in ft['GSUB'].table.FeatureList.FeatureRecord)
    report={'unicode_characters':len(cmap),'glyphs':len(ft.getGlyphOrder()),'errors':errors,
        'ttf_woff2_cmap_match':True,'ss01_alternates_bounds_checked':True,'all_supported_nonspace_characters_rasterized_at_px':64,
        'vertical_extrema':[min(b[2] for b in bounds),max(b[4] for b in bounds)],
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [FONT,OUT/'NikukyuMaru-Regular.woff2']},
        'limits':['Horizontal display font; vertical layout not implemented.','NFC precomposed kana; combining marks U+3099/309A not supported.','Manual app installation not performed.']}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if errors:
        raise RuntimeError('Font verification failed: ' + '; '.join(errors))

if __name__=='__main__':make_proofs()



