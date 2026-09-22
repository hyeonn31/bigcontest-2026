"""강건성 점검 (2/3): 전일 강수의 지연 효과.

그날 비뿐 아니라 '어제' 호우가 있었는지도 변수로 추가해서, 춘천의
동일시도/타시도 반응에 전날 효과가 남아있는지 확인한다.

방법: log(y) ~ 월+요일+공휴일+당일 약한비+당일 호우+전일 호우, HAC(3일).
'전일 호우'의 계수가 유의하면 "비의 영향이 다음날까지 이어진다"는 뜻이고,
유의하지 않으면 "당일에만 영향이 있고 다음날은 회복된다"는 뜻.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE = r"C:\SH_Antigravity\bigcontest"
OUT_TXT = os.path.join(BASE, "eda_output", "robustness_lag_effect.txt")

m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"),
                 encoding="utf-8-sig", parse_dates=["date"])
m["is_holiday"] = m["is_holiday"].astype(float)

CUSTOMER_COLS = {"동일 시도 거주자": "s2c_local_amt", "타 시도 거주자": "s2c_visitor_amt",
                 "전체(핵심소비)": "s2c_amt"}
REGION = "강원 춘천시"

g = m[m["region"] == REGION].set_index("date").sort_index()
g["rain_light"] = ((g["precip_sum"] >= 1) & (g["precip_sum"] < 30)).astype(float)
g["rain_heavy"] = (g["precip_sum"] >= 30).astype(float)
# 전일 호우 = 어제 날짜의 rain_heavy를 오늘 행으로 shift
g["rain_heavy_lag1"] = g["rain_heavy"].shift(1)

# 날짜가 연속이 아닐 수 있으니(빠진 날 없는지) 확인 후 진행
full_range = pd.date_range(g.index.min(), g.index.max(), freq="D")
missing = full_range.difference(g.index)

out = open(OUT_TXT, "w", encoding="utf-8")


def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n")
    print(line)


p(f"강건성 점검(2/3): {REGION}, 전일 호우의 지연 효과")
p(f"날짜 연속성 확인: 184일 중 빠진 날 {len(missing)}개 (0이어야 정상)")
p("모형: log(y) ~ 월+요일+공휴일+당일약한비+당일호우+전일호우, HAC(3일)\n")

gg = g.dropna(subset=["rain_heavy_lag1"]).copy()  # 첫날은 전일 데이터 없어서 제외

X = pd.get_dummies(gg[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
X["is_holiday"] = gg["is_holiday"]
X["rain_light"] = gg["rain_light"]
X["rain_heavy"] = gg["rain_heavy"]
X["rain_heavy_lag1"] = gg["rain_heavy_lag1"]
X = sm.add_constant(X)

for cust, col in CUSTOMER_COLS.items():
    y = np.log(gg[col])
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    p(f"--- {cust} ---")
    for term, label in [("rain_heavy", "당일 호우"), ("rain_heavy_lag1", "전일 호우(지연효과)")]:
        coef, se, pv = res.params[term], res.bse[term], res.pvalues[term]
        pct = (np.exp(coef) - 1) * 100
        lo = (np.exp(coef - 1.96 * se) - 1) * 100
        hi = (np.exp(coef + 1.96 * se) - 1) * 100
        p(f"  {label:16s} {pct:7.2f}%  (95% CI {lo:6.1f}%~{hi:5.1f}%, p={pv:.4f})")
    p("")

p("해석: '전일 호우'가 유의하지 않으면(p>0.05) 비의 영향은 당일에 그치고 다음날로 안 넘어간다는 뜻.")
p("당일 호우 계수가 지연효과 변수를 추가하기 전(이전 분석)과 비슷하게 유지되면, 그 결과도 강건하다는 뜻.")
out.close()
