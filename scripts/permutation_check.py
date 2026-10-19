"""[6단계 · 1차 검정] 회귀분석 전에, 가정이 적은 순열검정으로 기후 효과를 먼저 훑어본다.

방법: 소비를 '같은 지역·월·요일 평균 대비 비율(지수)'로 바꾼 뒤,
'호우일 평균 지수 - 나머지 날 평균 지수'가 날짜를 무작위로 섞었을 때보다 극단적인지 본다.
한계: 날짜 간 자기상관·여러 검정 동시 수행을 반영 못 함 → industry_analysis.py의
회귀(HAC + FDR)로 대체됨. 1차 탐색 기록으로 보존.

입력: data/processed/merged_daily.csv
출력: eda_output/permutation_check.txt
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m_all = pd.read_csv(BASE + r"\data\processed\merged_daily.csv", encoding="utf-8-sig", parse_dates=["date"])
m_all = m_all.dropna(subset=["temp_mean"]).copy()  # 기상 데이터가 없는 12/31 제외

# 공휴일/연휴: 광복절 8/15, 추석 연휴 10/3~10/9, 크리스마스 12/25
# (작성 당시엔 기억 기준이었고, 이후 검색으로 확인해 build_merged_daily.py의 is_holiday와 동일함)
HOLIDAYS = pd.to_datetime(["2025-08-15", "2025-12-25"] + [d.strftime("%Y-%m-%d") for d in pd.date_range("2025-10-03", "2025-10-09")])

SERIES = ["s2c_amt", "s2c_local_amt", "s2c_visitor_amt"]
FLAGS = ["heavy_rain_day", "rain_day", "heat_day", "tropical_night"]
N = 10000
rng = np.random.default_rng(42)


def run(m):
    m = m.copy()
    for col in SERIES:
        # 같은 (지역, 월, 요일) 평균 대비 당일 비율
        m[col + "_idx"] = m[col] / m.groupby(["region", "month", "weekday"])[col].transform("mean")
    rows = []
    for region, g in m.groupby("region"):
        for flag in FLAGS:
            f = g[flag].astype(bool).to_numpy()
            k = int(f.sum())
            if k < 5:
                continue
            for col in SERIES:
                x = g[col + "_idx"].to_numpy()
                obs = x[f].mean() - x[~f].mean()  # 실제 관측된 차이
                # 날짜를 무작위로 섞어 k일을 '가짜 호우일'로 뽑았을 때의 차이를 N번 만든다
                # → 실제 차이보다 극단적인 경우의 비율 = p값
                perm = np.empty(N)
                for i in range(N):
                    ix = rng.permutation(len(x))
                    perm[i] = x[ix[:k]].mean() - x[ix[k:]].mean()
                rows.append((region, flag, col, k, round(obs, 3), round((np.abs(perm) >= abs(obs)).mean(), 4)))
    return pd.DataFrame(rows, columns=["region", "flag", "series", "n_flag_days", "diff_in_index", "p_value"])


with open(BASE + r"\eda_output\permutation_check.txt", "w", encoding="utf-8") as out:
    out.write("핵심 소비(세금공과금·ZZ_나머지 제외) 기준. 차이 = (플래그일 평균 지수) - (그 외 날 평균 지수).\n")
    out.write("무작위로 날짜를 섞는 순열검정(10,000회), 양측 p값. 검정을 여러 개 돌렸으므로 p<0.05 하나하나를 그대로 믿으면 안 됨\n")
    out.write("\n[A] 전체 날짜\n" + run(m_all).to_string(index=False))
    out.write("\n\n[B] 공휴일/연휴 제외 (8/15, 10/3~10/9, 12/25)\n" + run(m_all[~m_all["date"].isin(HOLIDAYS)]).to_string(index=False))
print("done")
