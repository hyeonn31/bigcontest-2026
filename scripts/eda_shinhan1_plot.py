"""[2단계 · 탐색] 데이터1 결제금액(TS_AT) 분포를 두 장의 그림으로 본다.

1. ts_at_distribution.png: 원본 스케일 vs log10 스케일
   원본에서는 소수의 거액 결제 때문에 대부분이 0 근처에 몰려 보이지 않고, log를 취하면 종 모양에 가까워짐
   → 이후 회귀에서 log(금액)을 종속변수로 쓰는 근거
2. ts_at_zoom.png: 원본 전체 vs 상위 1% 제외 확대
   log 없이 원본 단위로 보되, 극단값을 빼면 나머지 99%가 어떤 모양인지 확인

입력: data/shinhan_card/신한카드_빅콘테스트2026_데이터1.txt
출력: figures/ts_at_distribution.png, figures/ts_at_zoom.png
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
p99 = df['TS_AT'].quantile(0.99)

# (출력 파일, [(값, 색, 제목, x축 라벨, 숫자 그대로 표기 여부)] 왼쪽·오른쪽 패널)
FIGURES = [
    ("ts_at_distribution.png", [
        (df['TS_AT'], '#4C72B0', 'TS_AT 원본 분포 (선형 스케일)', '결제금액 합계', False),
        (np.log10(df['TS_AT']), '#55A868', 'TS_AT 분포 (log10 스케일)', 'log10(결제금액 합계)', False),
    ]),
    ("ts_at_zoom.png", [
        (df['TS_AT'], '#4C72B0', f'TS_AT 원본 스케일 (0 ~ 최댓값 {df["TS_AT"].max():,.0f})', '결제금액 합계', True),
        (df.loc[df['TS_AT'] <= p99, 'TS_AT'], '#DD8452', f'TS_AT 원본 스케일, 상위 1% 제외 (0 ~ {p99:,.0f}까지만 확대)', '결제금액 합계', True),
    ]),
]

for out_name, panels in FIGURES:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, (values, color, title, xlabel, plain) in zip(axes, panels):
        ax.hist(values, bins=50, color=color)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('빈도')
        if plain:
            ax.ticklabel_format(style='plain', axis='x')  # 1e9 같은 지수 표기 대신 숫자 그대로
    plt.tight_layout()
    out_png = BASE + "\\figures\\" + out_name
    plt.savefig(out_png, dpi=110)
    plt.close()
    print('saved to', out_png)
print('p99 =', p99)
