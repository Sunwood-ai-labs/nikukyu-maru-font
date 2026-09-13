"""Load the font privately in Windows GDI and check native BMP glyph mapping."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import json,hashlib

ROOT=Path(__file__).resolve().parent

def verify():
    gdi=C.WinDLL('gdi32',use_last_error=True)
    gdi.AddFontResourceExW.argtypes=[W.LPCWSTR,W.DWORD,C.c_void_p]
    gdi.RemoveFontResourceExW.argtypes=[W.LPCWSTR,W.DWORD,C.c_void_p]
    gdi.CreateCompatibleDC.argtypes=[W.HDC];gdi.CreateCompatibleDC.restype=W.HDC
    gdi.CreateFontW.argtypes=[C.c_int]*5+[W.DWORD]*8+[W.LPCWSTR]
    gdi.CreateFontW.restype=W.HFONT
    gdi.SelectObject.argtypes=[W.HDC,W.HGDIOBJ];gdi.SelectObject.restype=W.HGDIOBJ
    gdi.GetTextFaceW.argtypes=[W.HDC,C.c_int,W.LPWSTR]
    gdi.GetGlyphIndicesW.argtypes=[W.HDC,W.LPCWSTR,C.c_int,C.POINTER(W.WORD),W.DWORD]
    gdi.GetGlyphIndicesW.restype=W.DWORD
    gdi.DeleteObject.argtypes=[W.HGDIOBJ];gdi.DeleteDC.argtypes=[W.HDC]
    path=str(ROOT/'outputs/NikukyuMaru-Regular.ttf')
    loaded=gdi.AddFontResourceExW(path,0x10,None)
    if not loaded:raise RuntimeError('Windows rejected private font load')
    dc=font=old=None
    try:
        dc=gdi.CreateCompatibleDC(None)
        font=gdi.CreateFontW(-64,0,0,0,800,0,0,0,1,0,0,4,0,'Nikukyu Maru')
        old=gdi.SelectObject(dc,font)
        family=C.create_unicode_buffer(128);gdi.GetTextFaceW(dc,128,family)
        sample='名前住所価格今日営業時間東京都大阪府髙﨑①㈱〒￥★☆㋿がぱガパｶﾞﾊﾟ'
        indices=(W.WORD*len(sample))()
        count=gdi.GetGlyphIndicesW(dc,sample,len(sample),indices,1)
        missing=[ch for ch,index in zip(sample,indices) if index==0xffff]
        report={'private_font_load_count':loaded,'selected_family':family.value,
                'bmp_sample':sample,'native_glyph_count':count,'missing':missing,
                'permanent_installation':False,'ttf_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
        assert family.value in ('Nikukyu Maru','にくきゅう丸'),report
        assert count==len(sample) and not missing,report
        return report
    finally:
        if old:gdi.SelectObject(dc,old)
        if font:gdi.DeleteObject(font)
        if dc:gdi.DeleteDC(dc)
        gdi.RemoveFontResourceExW(path,0x10,None)

if __name__=='__main__':
    report=verify()
    (ROOT/'outputs/windows-font-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
