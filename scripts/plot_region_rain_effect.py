"""[8단계 · 시각화] 강남 vs 춘천의 호우일 효과(%)를 오차범위(95% 신뢰구간)와 함께 막대그래프로 그린다.

목적: region_interaction_test.py의 숫자 결과(계수, p값)만으로는 "왜 유의하지 않은지"가
직관적으로 안 와닿음. 오차범위를 그려보면 두 지역의 막대가 얼마나 겹치는지 눈으로 바로 보임
(오차범위가 많이 겹치면 = 두 값이 통계적으로 "다르다"고 말하기 어렵다는 뜻).

같은 회귀 모형을 다시 적합하되, 이번엔 계수의 표준오차(SE)까지 뽑아서
95% 신뢰구간 = 계수 ± 1.96*SE 를 계산한다.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from common import BASE, load_merged, fit_hac, pct_ci

OUT_FIG = os.path.join(BASE, "figures", "region_rain_effect_ci.png")

# 한글 폰트 설정 (윈도우 기본 맑은 고딕)
matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

m = load_merged()

results = {}
for region, g in m.groupby("region"):
    g = g.set_index("date").sort_index()
    res = fit_hac(g, np.log(g["s2c_amt"]), ["is_holiday", "rain_light", "rain_heavy", "heat_day"])
    for term in ["rain_light", "rain_heavy"]:
        results[(region, term)] = pct_ci(res, term)

# ---- 그래프 ----
fig, ax = plt.subplots(figsize=(7, 5))
regions = ["서울 강남구", "강원 춘천시"]
terms = ["rain_light", "rain_heavy"]
term_labels = ["약한 비\n(1~30mm)", "호우\n(30mm 이상)"]
colors = {"서울 강남구": "#4C72B0", "강원 춘천시": "#DD8452"}

x = np.arange(len(terms))
width = 0.35
for i, region in enumerate(regions):
    pcts = [results[(region, t)][0] for t in terms]
    los = [results[(region, t)][0] - results[(region, t)][1] for t in terms]
    his = [results[(region, t)][2] - results[(region, t)][0] for t in terms]
    offset = (i - 0.5) * width
    bars = ax.bar(x + offset, pcts, width, yerr=[los, his], capsize=5,
                   label=region, color=colors[region], alpha=0.85)
    for j, t in enumerate(terms):
        pv = results[(region, t)][3]
        star = "**" if pv < 0.01 else ("*" if pv < 0.05 else "n.s.")
        ax.text(x[j] + offset, pcts[j] + (his[j] if pcts[j] >= 0 else -los[j]) + 1,
                f"{pcts[j]:.1f}%\n({star})", ha="center", va="bottom" if pcts[j] >= 0 else "top", fontsize=9)

ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(term_labels)
ax.set_ylabel("평범한 날 대비 소비 변화 (%)")
ax.set_title("비가 오면 핵심 소비가 얼마나 줄어드는가 (지역별, 95% 신뢰구간)")
ax.legend()
ax.text(0.5, -0.25, "세로 막대 = 오차범위(95% 신뢰구간). 두 지역 막대의 세로선이 많이 겹칠수록\n\"두 지역이 통계적으로 다르게 반응한다\"고 말하기 어렵다는 뜻 (n.s. = 유의하지 않음)",
        transform=ax.transAxes, ha="center", fontsize=8, color="gray")
plt.tight_layout()
plt.savefig(OUT_FIG, dpi=150)
print("saved:", OUT_FIG)
for k, v in results.items():
    print(k, "pct=%.2f lo=%.2f hi=%.2f p=%.4f" % v)
