"""[1단계 · 준비] 신한카드 원본 TXT의 인코딩을 CP949 → UTF-8로 변환한다.

대회 원본은 윈도우 한글 인코딩(CP949)이라 pandas 기본 설정으로 읽으면 한글이 깨진다.
이후 모든 스크립트가 encoding="utf-8-sig"로 읽을 수 있도록 원본 파일을 제자리에서 덮어쓴다.
※ 한 번만 실행. 이미 변환된 파일에 다시 돌리면 CP949로 해석하다 에러가 난다.

입력/출력: data/shinhan_card/신한카드_빅콘테스트2026_데이터1.txt, 데이터2_수정.txt (덮어쓰기)
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    BASE + r"\data\shinhan_card\신한카드_빅콘테스트2026_데이터1.txt",
    BASE + r"\data\shinhan_card\신한카드_빅콘테스트2026_데이터2_수정.txt",
]

for path in FILES:
    # 임시 파일에 다 쓴 뒤 원본과 바꿔치기 → 도중에 에러가 나도 원본이 반쯤 망가지지 않음
    tmp_path = path + '.utf8tmp'
    with io.open(path, encoding='cp949') as fin, io.open(tmp_path, 'w', encoding='utf-8-sig', newline='') as fout:
        for line in fin:
            fout.write(line)
    os.replace(tmp_path, path)
    print('converted:', path)
