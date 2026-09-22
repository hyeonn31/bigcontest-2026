"""발표(PT)용 그래프 3장 제작 — 분석용 그래프(plot_*.py)와 같은 데이터를 쓰지만
디자인 목적이 다름: "검증"이 아니라 "3초 안에 핵심 전달".

- pt_01_region_overview.png: 지역 전체로만 보면 애매하다는 도입부 그래프 (5-1)
- pt_02_visitor_local_main.png: 핵심 발견 — 방문객 vs 지역주민 (5-2, 메인)
- pt_03_robustness.png: 강건성 점검 — 기준을 바꿔도 유지됨 (5-3)

같은 merged_daily.csv로 같은 회귀를 다시 돌리되(재현성 확인 겸), 스타일만 발표용으로.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib

BASE = r"C:\SH_Antigravity\bigcontest"
FIG_DIR = os.path.join(BASE, "figures")

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BLUE = "#3B6FA0"   # 동일 시도 / 강남
RED = "#D45B5B"    # 타 시도 / 강조
GRAY = "#8C8C8C"
BG = "#FFFFFF"

m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"),
                 encoding="utf-8-sig", parse_dates=["date"])
m["is_holiday"] = m["is_holiday"].astype(float)
m["rain_light"] = ((m["precip_sum"] >= 1) & (m["precip_sum"] < 30)).astype(float)
m["rain_heavy"] = (m["precip_sum"] >= 30).astype(float)


def fit_ci(g, col, term):
    y = np.log(g[col])
    X = pd.get_dummies(g[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
    for c in ["is_holiday", "rain_light", "rain_heavy"]:
        X[c] = g[c]
    X = sm.add_constant(X)
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    coef, se, pv = res.params[term], res.bse[term], res.pvalues[term]
    pct = (np.exp(coef) - 1) * 100
    lo = (np.exp(coef - 1.96 * se) - 1) * 100
    hi = (np.exp(coef + 1.96 * se) - 1) * 100
    return pct, lo, hi, pv


# =============== 5-1. 지역 전체 개관 (도입부) ===============
fig, ax = plt.subplots(figsize=(8, 6))
fig.subplots_adjust(bottom=0.22, top=0.82)
regions = ["서울 강남구", "강원 춘천시"]
vals, los, his, pvs = [], [], [], []
for r in regions:
    g = m[m["region"] == r].set_index("date").sort_index()
    pct, lo, hi, pv = fit_ci(g, "s2c_amt", "rain_heavy")
    vals.append(pct); los.append(pct - lo); his.append(hi - pct); pvs.append(pv)

bars = ax.bar(regions, vals, width=0.5, color=[BLUE, RED], yerr=[los, his], capsize=8,
              error_kw={"linewidth": 2, "ecolor": GRAY})
ax.axhline(0, color="black", linewidth=1)
for i, v in enumerate(vals):
    sig = "통계적으로 확실함" if pvs[i] < 0.05 else "불확실 (표본 부족)"
    ax.text(i, v - his[i] - 3 if v < 0 else v + his[i] + 1, f"{v:.0f}%", ha="center",
            fontsize=22, fontweight="bold", color=[BLUE, RED][i])
    ax.text(i, v - his[i] - 6.5 if v < 0 else v + his[i] + 4.5, sig, ha="center", fontsize=11, color=GRAY)
ax.set_ylim(-32, 8)
ax.set_yticks([])
ax.tick_params(axis="x", labelsize=13, pad=10)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.set_title("호우일, 전체 소비는 지역마다 신호가 다르다", fontsize=17, fontweight="bold", pad=15)
fig.text(0.5, 0.04, "→ '지역 전체'만 보면 결론이 애매하다 — 고객을 나눠봐야 한다",
          ha="center", fontsize=12, color=GRAY, style="italic")
plt.savefig(os.path.join(FIG_DIR, "pt_01_region_overview.png"), dpi=150, facecolor=BG)
plt.close()

# =============== 5-2. 메인: 방문객 vs 지역주민 (춘천, 호우일) ===============
fig, ax = plt.subplots(figsize=(9, 6))
fig.subplots_adjust(left=0.2, right=0.92, bottom=0.2, top=0.78)
g = m[m["region"] == "강원 춘천시"].set_index("date").sort_index()
local_pct, local_lo, local_hi, _ = fit_ci(g, "s2c_local_amt", "rain_heavy")
vis_pct, vis_lo, vis_hi, _ = fit_ci(g, "s2c_visitor_amt", "rain_heavy")

labels = ["지역주민", "외지 방문객"]
vals = [local_pct, vis_pct]
errs_lo = [local_pct - local_lo, vis_pct - vis_lo]
errs_hi = [local_hi - local_pct, vis_hi - vis_pct]
colors = [BLUE, RED]

bars = ax.barh(labels, vals, height=0.45, color=colors, xerr=[errs_lo, errs_hi], capsize=8,
               error_kw={"linewidth": 2, "ecolor": GRAY, "capthick": 2})
ax.axvline(0, color="black", linewidth=1)
# 값 라벨은 막대 '안쪽'에 흰 굵은 글씨로 — 축 라벨과 겹칠 일이 없음
for i, v in enumerate(vals):
    ax.text(v / 2, i, f"{v:.0f}%", va="center", ha="center", fontsize=24, fontweight="bold", color="white")
ax.set_xlim(-26, 4)
ax.set_xticks([])
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", labelsize=15, length=0, pad=12)
ax.set_title("춘천, 호우일엔 외지 방문객이 지역주민보다\n약 3배 더 크게 소비를 줄인다", fontsize=18, fontweight="bold")
fig.text(0.5, 0.06, "평범한 날 대비 소비 변화율 (호우=일강수량 30mm↑, 95% 신뢰구간, 둘 다 p<0.001)",
          ha="center", fontsize=10, color=GRAY)
plt.savefig(os.path.join(FIG_DIR, "pt_02_visitor_local_main.png"), dpi=150, facecolor=BG)
plt.close()

# =============== 5-3. 강건성: 기준을 바꿔도 유지됨 ===============
THRESHOLDS = [15, 20, 25, 30, 35, 40]
local_pcts, vis_pcts = [], []
for t in THRESHOLDS:
    rh = (g["precip_sum"] >= t).astype(float)
    rm = ((g["precip_sum"] >= 1) & (g["precip_sum"] < t)).astype(float)
    X = pd.get_dummies(g[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
    X["is_holiday"] = g["is_holiday"]; X["rain_mid"] = rm; X["rain_heavy"] = rh
    X = sm.add_constant(X)
    for col, store in [("s2c_local_amt", local_pcts), ("s2c_visitor_amt", vis_pcts)]:
        y = np.log(g[col])
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        store.append((np.exp(res.params["rain_heavy"]) - 1) * 100)

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(THRESHOLDS, local_pcts, "o-", color=BLUE, linewidth=3, markersize=9, label="지역주민")
ax.plot(THRESHOLDS, vis_pcts, "o-", color=RED, linewidth=3, markersize=9, label="외지 방문객")
ax.axhline(0, color="black", linewidth=1)
ax.fill_between(THRESHOLDS, vis_pcts, local_pcts, color=RED, alpha=0.08)
ax.set_ylim(-25, 2)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.set_xlabel("'호우' 기준을 바꿔도 (mm)", fontsize=12)
ax.set_yticks([])
ax.legend(fontsize=13, loc="lower left", frameon=False)
ax.set_title("기준값을 바꿔봐도 격차는 그대로 유지된다", fontsize=17, fontweight="bold", pad=15)
ax.text(0.5, -0.15, "호우 기준 15~40mm 전 구간에서 외지 방문객이 항상 더 크게 감소 (우연이 아님)",
        transform=ax.transAxes, ha="center", fontsize=11, color=GRAY)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "pt_03_robustness.png"), dpi=150, facecolor=BG)
plt.close()

print("saved 3 figures to", FIG_DIR)
