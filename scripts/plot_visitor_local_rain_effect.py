"""핵심 생존 주장 검증: 호우일에 '동일 시도 거주자' vs '타 시도 거주자' 소비가
지역(강남/춘천)별로 얼마나 다르게 줄어드는지 오차범위(95% CI)와 함께 그린다.

compare_candidates.py는 log(타시도/동일시도) "비율"만 검정했음. 이 스크립트는
두 그룹 각각의 "평범한 날 대비 %"를 따로 추정해서, 어느 쪽이 얼마나 줄었는지를
직접 눈으로 비교할 수 있게 한다 (방법은 이전 스크립트들과 동일: 로그회귀 + HAC).
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib

BASE = r"C:\SH_Antigravity\bigcontest"
OUT_FIG = os.path.join(BASE, "figures", "visitor_local_rain_effect_ci.png")

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"),
                 encoding="utf-8-sig", parse_dates=["date"])
m["rain_light"] = ((m["precip_sum"] >= 1) & (m["precip_sum"] < 30)).astype(float)
m["rain_heavy"] = (m["precip_sum"] >= 30).astype(float)
m["heat_day"] = m["heat_day"].astype(float)
m["is_holiday"] = m["is_holiday"].astype(float)

CUSTOMER_COLS = {"동일 시도 거주자": "s2c_local_amt", "타 시도 거주자": "s2c_visitor_amt"}

results = {}  # (region, customer, term) -> (pct, lo, hi, p)
for region, g in m.groupby("region"):
    g = g.set_index("date").sort_index()
    X = pd.get_dummies(g[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
    for c in ["is_holiday", "rain_light", "rain_heavy", "heat_day"]:
        X[c] = g[c].astype(float)
    X = sm.add_constant(X)
    for cust, col in CUSTOMER_COLS.items():
        y = np.log(g[col])
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        for term in ["rain_light", "rain_heavy"]:
            coef, se = res.params[term], res.bse[term]
            pct = (np.exp(coef) - 1) * 100
            lo = (np.exp(coef - 1.96 * se) - 1) * 100
            hi = (np.exp(coef + 1.96 * se) - 1) * 100
            results[(region, cust, term)] = (pct, lo, hi, res.pvalues[term])

# ---- 그래프: 2개 패널(약한 비 / 호우), 각 패널에 지역x고객유형 4개 막대 ----
fig, axes = plt.subplots(1, 2, figsize=(11, 5.5), sharey=True)
regions = ["서울 강남구", "강원 춘천시"]
customers = list(CUSTOMER_COLS.keys())
colors = {"동일 시도 거주자": "#4C72B0", "타 시도 거주자": "#C44E52"}
term_titles = {"rain_light": "약한 비 (1~30mm)", "rain_heavy": "호우 (30mm 이상)"}

for ax, term in zip(axes, ["rain_light", "rain_heavy"]):
    x = np.arange(len(regions))
    width = 0.35
    for i, cust in enumerate(customers):
        pcts = [results[(r, cust, term)][0] for r in regions]
        los = [results[(r, cust, term)][0] - results[(r, cust, term)][1] for r in regions]
        his = [results[(r, cust, term)][2] - results[(r, cust, term)][0] for r in regions]
        offset = (i - 0.5) * width
        ax.bar(x + offset, pcts, width, yerr=[los, his], capsize=5,
               label=cust, color=colors[cust], alpha=0.85)
        for j, r in enumerate(regions):
            pv = results[(r, cust, term)][3]
            star = "**" if pv < 0.01 else ("*" if pv < 0.05 else "n.s.")
            ypos = pcts[j] + (his[j] if pcts[j] >= 0 else -los[j])
            ax.text(x[j] + offset, ypos + (1.5 if pcts[j] >= 0 else -1.5), f"{pcts[j]:.1f}%\n{star}",
                    ha="center", va="bottom" if pcts[j] >= 0 else "top", fontsize=8)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(regions)
    ax.set_title(term_titles[term])
    if term == "rain_light":
        ax.set_ylabel("평범한 날 대비 소비 변화 (%)")

axes[1].legend(loc="lower left")
fig.suptitle("호우일에 '지역주민'과 '외지 방문객' 중 누가 더 줄어드는가", fontsize=13)
fig.text(0.5, 0.01, "오차막대=95% 신뢰구간, n.s.=유의하지 않음, *=p<0.05, **=p<0.01", ha="center", fontsize=8, color="gray")
plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig(OUT_FIG, dpi=150)
print("saved:", OUT_FIG)
for k, v in results.items():
    print(k, "pct=%.2f lo=%.2f hi=%.2f p=%.4f" % v)
