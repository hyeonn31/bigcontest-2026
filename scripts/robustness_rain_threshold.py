"""강건성 점검: '호우'의 강수량 기준을 여러 값으로 바꿔가며, 춘천에서
'동일 시도 거주자 vs 타 시도 거주자'의 반응 차이가 일관되게 나오는지 확인한다.

지금까지는 호우 = 일 강수량 30mm 이상 하나로만 결론을 냈음. 이 스크립트는
15/20/25/30/35/40mm 여섯 기준 각각에 대해 같은 회귀를 다시 돌려서,
기준을 바꿔도 "방문객이 더 크게 준다"는 패턴(과 대략적인 크기)이 유지되는지 본다.

방법은 이전과 동일: log(y) ~ 월+요일+공휴일+약한비(1~t)+호우(t+), HAC(3일).
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib

BASE = r"C:\SH_Antigravity\bigcontest"
OUT_FIG = os.path.join(BASE, "figures", "robustness_rain_threshold.png")
OUT_TXT = os.path.join(BASE, "eda_output", "robustness_rain_threshold.txt")

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"),
                 encoding="utf-8-sig", parse_dates=["date"])
m["is_holiday"] = m["is_holiday"].astype(float)

THRESHOLDS = [15, 20, 25, 30, 35, 40]
CUSTOMER_COLS = {"동일 시도 거주자": "s2c_local_amt", "타 시도 거주자": "s2c_visitor_amt"}
REGION = "강원 춘천시"

g = m[m["region"] == REGION].set_index("date").sort_index()

out = open(OUT_TXT, "w", encoding="utf-8")


def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n")
    print(line)


p(f"강건성 점검: {REGION}, 호우 기준(mm)을 바꿔가며 재검정")
p("기준(mm) | n(호우일) | 동일시도 효과% (p) | 타시도 효과% (p) | 차이%p")

results = {c: {"pct": [], "lo": [], "hi": []} for c in CUSTOMER_COLS}
n_days_list = []

for t in THRESHOLDS:
    rain_heavy = (g["precip_sum"] >= t).astype(float)
    rain_mid = ((g["precip_sum"] >= 1) & (g["precip_sum"] < t)).astype(float)
    n_heavy = int(rain_heavy.sum())
    n_days_list.append(n_heavy)

    X = pd.get_dummies(g[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
    X["is_holiday"] = g["is_holiday"]
    X["rain_mid"] = rain_mid
    X["rain_heavy"] = rain_heavy
    X = sm.add_constant(X)

    row = [f"{t:>3d}mm", f"n={n_heavy:2d}"]
    pcts = {}
    for cust, col in CUSTOMER_COLS.items():
        y = np.log(g[col])
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        coef, se, pv = res.params["rain_heavy"], res.bse["rain_heavy"], res.pvalues["rain_heavy"]
        pct = (np.exp(coef) - 1) * 100
        lo = (np.exp(coef - 1.96 * se) - 1) * 100
        hi = (np.exp(coef + 1.96 * se) - 1) * 100
        results[cust]["pct"].append(pct)
        results[cust]["lo"].append(lo)
        results[cust]["hi"].append(hi)
        pcts[cust] = pct
        row.append(f"{cust}={pct:6.1f}%(p={pv:.3f})")
    row.append(f"차이={pcts['타 시도 거주자']-pcts['동일 시도 거주자']:6.1f}%p")
    p(" | ".join(row))

# ---- 그래프 ----
fig, ax = plt.subplots(figsize=(8, 5))
colors = {"동일 시도 거주자": "#4C72B0", "타 시도 거주자": "#C44E52"}
for cust in CUSTOMER_COLS:
    pct = np.array(results[cust]["pct"])
    lo = np.array(results[cust]["lo"])
    hi = np.array(results[cust]["hi"])
    ax.plot(THRESHOLDS, pct, "o-", color=colors[cust], label=cust)
    ax.fill_between(THRESHOLDS, lo, hi, color=colors[cust], alpha=0.15)

ax.axhline(0, color="black", linewidth=0.8)
ax.set_xlabel("'호우'로 정의하는 강수량 기준 (mm)")
ax.set_ylabel("평범한 날 대비 소비 변화 (%)")
ax.set_title(f"{REGION}: 호우 기준을 바꿔도 방문객이 더 크게 주는가 (음영=95% CI)")
for i, t in enumerate(THRESHOLDS):
    ax.annotate(f"n={n_days_list[i]}", (t, ax.get_ylim()[0] + 1), fontsize=7, color="gray", ha="center")
ax.legend(loc="lower left")
plt.tight_layout()
plt.savefig(OUT_FIG, dpi=150)
p(f"\nsaved: {OUT_FIG}")
p("n=호우일로 분류된 날짜 수. 기준을 높일수록 n이 줄어 신뢰구간이 넓어지는 것은 자연스러운 현상.")
out.close()
