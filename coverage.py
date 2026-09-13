"""Reproducible Japanese repertoire from Python's JIS X 0208 mapping."""
def jis_rows(first, last):
    chars = set()
    for row in range(first, last + 1):
        for cell in range(1, 95):
            try:
                chars.add(bytes([row + 160, cell + 160]).decode('euc_jp'))
            except UnicodeDecodeError:
                pass
    return chars


KANJI = jis_rows(16, 84)
SYMBOLS = jis_rows(1, 15)
assert len(KANJI) == 6355


def cp932_characters():
    chars = set()
    for lead in list(range(0x81, 0xa0)) + list(range(0xe0, 0xf0)) + list(range(0xfa, 0xfd)):
        for trail in range(0x40, 0xfd):
            try:
                chars.add(bytes([lead, trail]).decode('cp932'))
            except UnicodeDecodeError:
                pass
    return chars


def requested_characters():
    return KANJI | SYMBOLS | cp932_characters() | set('𠮟𠮷㋿㍿©®€™≤≥') | {chr(cp) for cp in range(0xff61, 0xffa0)}
