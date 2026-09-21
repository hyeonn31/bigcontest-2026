import numpy as np
import pandas as pd

BASE = r"C:\Users\user\Downloads\SH\bigcontest"
m_all = pd.read_csv(BASE + r"\data\processed\merged_daily.csv", encoding="utf-8-sig", parse_dates=["date"])
m_all = m_all.dropna(subset=["temp_mean"]).copy()  # 기상 데이터가 없는 12/31 제외

# 공휴일/연휴(기억 기준, 검증 필요): 광복절 8/15, 추석 연휴 10/3~10/9, 크리스마스 12/25
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
                obs = x[f].mean() - x[~f].mean()
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
