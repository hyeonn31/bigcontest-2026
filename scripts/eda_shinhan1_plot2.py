import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

path = r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터1.txt"
df = pd.read_csv(path, sep='\t', encoding='utf-8-sig')

p99 = df['TS_AT'].quantile(0.99)
below_p99 = df[df['TS_AT'] <= p99]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(df['TS_AT'], bins=50, color='#4C72B0')
axes[0].set_title(f'TS_AT 원본 스케일 (0 ~ 최댓값 {df["TS_AT"].max():,.0f})')
axes[0].set_xlabel('결제금액 합계')
axes[0].set_ylabel('빈도')
axes[0].ticklabel_format(style='plain', axis='x')

axes[1].hist(below_p99['TS_AT'], bins=50, color='#DD8452')
axes[1].set_title(f'TS_AT 원본 스케일, 상위 1% 제외 (0 ~ {p99:,.0f}까지만 확대)')
axes[1].set_xlabel('결제금액 합계')
axes[1].set_ylabel('빈도')
axes[1].ticklabel_format(style='plain', axis='x')

plt.tight_layout()
out_png = r"C:\Users\user\Downloads\SH\bigcontest\figures\ts_at_zoom.png"
plt.savefig(out_png, dpi=110)
print('p99 =', p99)
print('saved to', out_png)
