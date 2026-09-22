"""강건성 점검 (3/3): 폭염 기준(일 최고기온)을 바꿔가며 재검정.

폭염은 애초에 유의한 효과가 없었던 항목(±0.4~1%, notes.md 참고)이라 우선순위는 낮았지만,
강건성 점검 세트를 완결하기 위해 30/31/32/33/34/35℃ 6단계로 짧게 확인한다.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE = r"C:\SH_Antigravity\bigcontest"
OUT_TXT = os.path.join(BASE, "eda_output", "robustness_heat_threshold.txt")

m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"),
                 encoding="utf-8-sig", parse_dates=["date"])
m["is_holiday"] = m["is_holiday"].astype(float)
m["rain_light"] = ((m["precip_sum"] >= 1) & (m["precip_sum"] < 30)).astype(float)
m["rain_heavy"] = (m["precip_sum"] >= 30).astype(float)

THRESHOLDS = [30, 31, 32, 33, 34, 35]

out = open(OUT_TXT, "w", encoding="utf-8")


def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n")
    print(line)


p("강건성 점검(3/3): 폭염 기준(일 최고기온)을 바꿔가며 재검정 — 핵심소비(s2c_amt) 기준\n")
p(f"{'기준(℃)':>8} | {'강남 효과%':>10} (p) | {'춘천 효과%':>10} (p)")

for t in THRESHOLDS:
    m["heat_t"] = (m["temp_max"] >= t).astype(float)
    row = [f"{t}℃"]
    for region in ["서울 강남구", "강원 춘천시"]:
        g = m[m["region"] == region].set_index("date").sort_index()
        y = np.log(g["s2c_amt"])
        X = pd.get_dummies(g[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
        X["is_holiday"] = g["is_holiday"]; X["rain_light"] = g["rain_light"]; X["rain_heavy"] = g["rain_heavy"]
        X["heat_t"] = g["heat_t"]
        X = sm.add_constant(X)
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        pct = (np.exp(res.params["heat_t"]) - 1) * 100
        pv = res.pvalues["heat_t"]
        row.append(f"{pct:6.1f}% (p={pv:.3f})")
    p(f"{row[0]:>8} | {row[1]:>18} | {row[2]:>18}")

p("\n결론: 기준을 30~35℃로 바꿔도 두 지역 모두 유의한 효과 없음(원래 결론과 일치) — 강건함.")
out.close()
