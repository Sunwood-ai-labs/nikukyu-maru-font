"""Package the exact reviewed source and binaries, excluding local environments."""
from pathlib import Path
import zipfile,json,hashlib
ROOT=Path(__file__).resolve().parent
version=json.loads((ROOT/'sources/design.json').read_text(encoding='utf-8-sig'))['version']
files=['.gitattributes','README.md','OFL.txt','BRIEF.md','PROGRESS.md','RELEASE-NOTES.md',
       'build.py','proof.py','harmonize.py','artifact_io.py','trace_reference.py',
       'trace_kanji_concept.py','concept_review.py','compare.py','audit_pages.py','package.py',
       'supplemental.py','requirements.txt','requirements-trace.txt',
       'coverage.py','kana_features.py','japanese_validation.py','practical_review.py',
       'verify_kana_shaping.py','verify_kanji_concept.py','verify_windows_font.py',
       'requirements-validation.txt']
paths=[ROOT/f for f in files]
for folder in ['sources','vendor','references','outputs']:
    paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
with zipfile.ZipFile(ROOT/f'NikukyuMaru-{version}.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(paths):z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(ROOT/f'NikukyuMaru-{version}.zip') as z:
    assert z.testzip() is None
print('Packaged',len(paths),'files;',version)
