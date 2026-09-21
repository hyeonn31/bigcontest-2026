import io
import os

FILES = [
    r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터1.txt",
    r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터2_수정.txt",
]

for path in FILES:
    tmp_path = path + '.utf8tmp'
    with io.open(path, encoding='cp949') as fin, io.open(tmp_path, 'w', encoding='utf-8-sig', newline='') as fout:
        for line in fin:
            fout.write(line)
    os.replace(tmp_path, path)
    print('converted:', path)
