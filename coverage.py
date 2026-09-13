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


def requested_characters():
    return KANJI | SYMBOLS | {chr(cp) for cp in range(0xff61, 0xffa0)}
