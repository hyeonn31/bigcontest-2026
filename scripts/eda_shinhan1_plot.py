"""[2단계 · 탐색] 데이터1 결제금액(TS_AT) 분포를 원본 스케일과 log10 스케일로 나란히 그린다.

원본 스케일에서는 소수의 거액 결제 때문에 대부분의 값이 0 근처에 몰려 보이지 않는다.
log를 취하면 분포가 종 모양에 가까워짐 → 이후 회귀에서 log(금액)을 종속변수로 쓰는 근거.

입력: data/shinhan_card/신한카드_빅콘테스트2026_데이터1.txt
출력: figures/ts_at_distribution.png
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

path = BASE + r"\data\shinhan_card\신한카드_빅콘테스트2026_데이터1.txt"
df = pd.read_csv(path, sep='\t', encoding='utf-8-sig')

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(df['TS_AT'], bins=50, color='#4C72B0')
axes[0].set_title('TS_AT 원본 분포 (선형 스케일)')
axes[0].set_xlabel('결제금액 합계')
axes[0].set_ylabel('빈도')

axes[1].hist(np.log10(df['TS_AT']), bins=50, color='#55A868')
axes[1].set_title('TS_AT 분포 (log10 스케일)')
axes[1].set_xlabel('log10(결제금액 합계)')
axes[1].set_ylabel('빈도')

plt.tight_layout()
out_png = BASE + r"\figures\ts_at_distribution.png"
plt.savefig(out_png, dpi=110)
print('saved to', out_png)
