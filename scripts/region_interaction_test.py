"""강남 vs 춘천의 기후 반응 차이가 통계적으로 유의한지 formal하게 검정한다.

compare_candidates.py까지는 지역별로 따로 회귀를 돌려서 "춘천은 유의, 강남은
약함"이라고 따로 읽었을 뿐, "두 지역 계수의 차이 자체"를 검정하지는 않았음.
이 스크립트는 region × 기후이벤트 상호작용항으로 그 차이를 직접 검정한다.

배경 가설: 강남은 지하철·지하상가로 실내 동선이 촘촘히 연결된 상권이라 우천의
충격을 흡수하고, 춘천은 실외 이동·관광 의존도가 높아 충격이 그대로 소비에
전달된다 (구조적 취약성 = 인프라 요인 × 방문객 의존도 프레임의 앞부분).

모형: log(s2c_amt) ~ 월 + 요일 + 공휴일 + region
                    + rain_light + rain_heavy + heat_day
                    + region_cc:rain_light + region_cc:rain_heavy + region_cc:heat_day
  (region_cc = 1이면 춘천, 0이면 강남 → 강남이 baseline)
HAC(maxlags=3)로 적합.

한계: HAC은 (region, date)로 정렬한 하나의 시계열로 취급하므로 강남→춘천 경계
부근(맨 앞뒤 3행 정도)에서만 근사 오차가 생김. 368행 중 3행이라 무시 가능한
수준으로 보고 진행. 정식으로는 지역별 클러스터 패널(예: linearmodels의
PanelOLS + Driscoll-Kraay)이 더 정확하나, 이 프로젝트는 지금까지 전부
statsmodels HAC 방식으로 일관되게 검정해 왔으므로 같은 방법을 유지한다.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE = r"C:\SH_Antigravity\bigcontest"
OUT_TXT = os.path.join(BASE, "eda_output", "region_interaction_test.txt")

m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"),
                 encoding="utf-8-sig", parse_dates=["date"])
m["rain_light"] = ((m["precip_sum"] >= 1) & (m["precip_sum"] < 30)).astype(float)
m["rain_heavy"] = (m["precip_sum"] >= 30).astype(float)
m["heat_day"] = m["heat_day"].astype(float)
m["is_holiday"] = m["is_holiday"].astype(float)
m = m.sort_values(["region", "date"]).reset_index(drop=True)

y = np.log(m["s2c_amt"])

X = pd.get_dummies(m[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
X["is_holiday"] = m["is_holiday"]
X["region_cc"] = (m["region"] == "강원 춘천시").astype(float)  # baseline = 강남
for t in ["rain_light", "rain_heavy", "heat_day"]:
    X[t] = m[t]
    X[f"region_cc_x_{t}"] = X["region_cc"] * m[t]
X = sm.add_constant(X)

res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})

out = open(OUT_TXT, "w", encoding="utf-8")


def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n")
    print(line)


p("강남 vs 춘천 기후 반응 차이 — 상호작용항 검정 (baseline=강남, region_cc=1이면 춘천)")
p("효과(%) = (exp(계수)-1)*100. region_cc_x_* 의 부호/유의성이 '춘천이 강남보다")
p("얼마나 더(-) / 덜(+) 영향받는지'에 대한 직접 검정.\n")

terms = ["rain_light", "rain_heavy", "heat_day", "region_cc",
          "region_cc_x_rain_light", "region_cc_x_rain_heavy", "region_cc_x_heat_day"]
for t in terms:
    pct = (np.exp(res.params[t]) - 1) * 100
    p(f"{t:28s} {pct:8.2f}%   p={res.pvalues[t]:.4f}")

# 춘천의 총 효과 = 강남 효과 + 상호작용 (선형결합 검정)
p("\n춘천 총 효과 (강남 계수 + 상호작용, 선형결합 검정):")
for t in ["rain_light", "rain_heavy", "heat_day"]:
    combo = f"{t} + region_cc_x_{t} = 0"
    tt = res.t_test(combo)
    pct = (np.exp(float(np.ravel(tt.effect)[0])) - 1) * 100
    pv = float(np.ravel(tt.pvalue)[0])
    p(f"  춘천 {t:20s} {pct:8.2f}%   p={pv:.4f}")

p("\n※ compare_candidates.py처럼 지역별로 따로 돌린 회귀 결과와 부호·크기가 일치하는지 대조할 것")
p("※ 유의한 region_cc_x_rain_heavy(p<0.05)가 나오면 '강남/춘천 비대칭이 우연이 아니다'를 뒷받침하는 근거가 됨")
out.close()
