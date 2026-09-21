import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

path = r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터1.txt"
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
out_png = r"C:\Users\user\Downloads\SH\bigcontest\figures\ts_at_distribution.png"
plt.savefig(out_png, dpi=110)
print('saved to', out_png)
