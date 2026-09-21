import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

BASE = r"C:\Users\user\Downloads\SH\bigcontest"
OUT_TXT = os.path.join(BASE, "eda_output", "industry_analysis.txt")
OUT_CSV = os.path.join(BASE, "data", "processed", "industry_rain_effects.csv")
EXCL = ["세금공과금", "ZZ_나머지"]
MIN_COVERAGE = 0.95    # 업종의 일별 데이터가 184일 중 95% 이상 있어야 분석 (마스킹으로 빠진 날이 많으면 제외)
MIN_MEAN_CNT = 30      # 하루 평균 결제건수 30건 이상
Q_THRESH = 0.10        # FDR 기준

# ---------- 공통: 날짜 특징 + 회귀 ----------
m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"), encoding="utf-8-sig", parse_dates=["date"])
m["rain_light"] = (m["precip_sum"] >= 1) & (m["precip_sum"] < 30)
m["rain_heavy"] = m["precip_sum"] >= 30
m["heat_day"] = m["heat_day"].astype(bool)
m["is_holiday"] = m["is_holiday"].astype(bool)

DESIGN = {}
for region, g in m.groupby("region"):
    g = g.set_index("date").sort_index()
    X = pd.get_dummies(g[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
    for c in ["is_holiday", "rain_light", "rain_heavy", "heat_day"]:
        X[c] = g[c].astype(float)
    DESIGN[region] = sm.add_constant(X)

TERMS = ["rain_light", "rain_heavy", "heat_day"]


def fit(region, y):
    """log(y) ~ 월+요일+공휴일+약한비+호우+폭염, HAC(3일) 표준오차. y는 날짜 인덱스 Series"""
    y = y.dropna()
    y = y[y > 0]
    X = DESIGN[region].loc[y.index]
    res = sm.OLS(np.log(y), X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out = {"n_days": len(y)}
    for t in TERMS:
        out[f"{t}_pct"] = (np.exp(res.params[t]) - 1) * 100
        out[f"{t}_p"] = res.pvalues[t]
    return out


out = open(OUT_TXT, "w", encoding="utf-8")


def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()


p("모형: log(금액) ~ 월 + 요일 + 공휴일 + 약한비(1~30mm) + 호우(30mm+) + 폭염(33℃+), HAC(3일) 표준오차")
p("효과(%) = 해당 조건일이 '비 안 온(1mm 미만) 평범한 날' 대비 몇 % 다른가\n")

# ---------- 1. 지역 전체 핵심 소비 (이전 순열검정의 회귀 버전) ----------
p("=" * 15, "1. 지역 전체 핵심 소비(세금공과금·ZZ_나머지 제외)", "=" * 15)
rows = []
for region, g in m.groupby("region"):
    g = g.set_index("date").sort_index()
    for label, col in [("전체", "s2c_amt"), ("동일시도 거주자", "s2c_local_amt"), ("타시도 거주자", "s2c_visitor_amt")]:
        r = fit(region, g[col])
        rows.append({"region": region, "series": label, **r})
p(pd.DataFrame(rows).round(3).to_string(index=False))

# ---------- 2. 시간대별 (데이터1, 법인 제외) ----------
p("\n" + "=" * 15, "2. 시간대별 (데이터1, 법인·세금공과금·ZZ_나머지 제외)", "=" * 15)
d1 = pd.read_csv(os.path.join(BASE, "data", "shinhan_card", "신한카드_빅콘테스트2026_데이터1.txt"), sep="\t", encoding="utf-8-sig")
d1 = d1[(d1["SEX_CCD"] != "법인") & (~d1["MCT_RY_CD"].isin(EXCL))].copy()
d1["date"] = pd.to_datetime(d1["TA_YMD"].astype(str), format="%Y%m%d")
tb = d1.groupby(["MCT_SGG_CD", "TIME_GB", "date"])["TS_AT"].sum().reset_index()
rows = []
for (region, tg), g in tb.groupby(["MCT_SGG_CD", "TIME_GB"]):
    r = fit(region, g.set_index("date")["TS_AT"])
    rows.append({"region": region, "time": tg, **r})
p(pd.DataFrame(rows).round(3).to_string(index=False))

# ---------- 3. 업종별 (데이터2) ----------
d2 = pd.read_csv(os.path.join(BASE, "data", "shinhan_card", "신한카드_빅콘테스트2026_데이터2_수정.txt"), sep="\t", encoding="utf-8-sig")
d2["date"] = pd.to_datetime(d2["TA_YMD"].astype(str), format="%Y%m%d")
core = d2[~d2["MCT_RY_CD"].isin(EXCL)].copy()
core["visitor"] = core["MCT_SGG_CD"].str.split(" ").str[0] != core["CLN_SGG_CD"]

p("\n" + "=" * 15, "3. 업종별", "=" * 15)
p("마스킹 진단: 결제건수 10건 미만 셀이 핵심 소비 금액에서 차지하는 비중 =",
  round(core.loc[core["USE_CNT"] < 10, "TS_AT"].sum() / core["TS_AT"].sum(), 4))

ind = core.groupby(["MCT_SGG_CD", "MCT_RY_CD", "date"])[["TS_AT", "USE_CNT"]].sum().reset_index()
vis = core.groupby(["MCT_SGG_CD", "MCT_RY_CD"]).apply(lambda g: g.loc[g["visitor"], "TS_AT"].sum() / g["TS_AT"].sum(), include_groups=False)
n_days = m["date"].nunique()

rows = []
skipped = {}
for (region, name), g in ind.groupby(["MCT_SGG_CD", "MCT_RY_CD"]):
    cov = g["date"].nunique() / n_days
    mean_cnt = g["USE_CNT"].mean()
    if cov < MIN_COVERAGE or mean_cnt < MIN_MEAN_CNT:
        skipped[region] = skipped.get(region, 0) + 1
        continue
    r = fit(region, g.set_index("date")["TS_AT"])
    rows.append({"region": region, "industry": name, "coverage": round(cov, 3), "mean_daily_cnt": round(mean_cnt, 1),
                 "visitor_share": round(vis[(region, name)], 3), **r})
res = pd.DataFrame(rows)
p("분석 포함 업종 수:", res.groupby("region").size().to_dict(), "/ 제외(커버리지·건수 부족):", skipped)

for t in TERMS:
    res[f"{t}_q"] = np.nan
    for region, idx in res.groupby("region").groups.items():
        res.loc[idx, f"{t}_q"] = multipletests(res.loc[idx, f"{t}_p"], method="fdr_bh")[1]
res.round(4).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

for t, label in [("rain_light", "약한 비(1~30mm)"), ("rain_heavy", "호우(30mm+)"), ("heat_day", "폭염(33℃+)")]:
    p(f"\n--- {label}: FDR q<{Q_THRESH} 통과 업종 ---")
    for region, g in res.groupby("region"):
        sig = g[g[f"{t}_q"] < Q_THRESH].sort_values(f"{t}_pct")
        p(f"[{region}] 검정 {len(g)}개 중 통과 {len(sig)}개")
        if len(sig):
            p(sig[["industry", "visitor_share", "mean_daily_cnt", f"{t}_pct", f"{t}_p", f"{t}_q"]].round(3).to_string(index=False))

# 가설: 타 시도 방문객 비중이 높은 업종일수록 비에 취약한가
p("\n--- 방문객 비중과 약한 비 효과의 상관 (스피어만) ---")
for region, g in res.groupby("region"):
    rho, pv = spearmanr(g["visitor_share"], g["rain_light_pct"])
    rho2, pv2 = spearmanr(g["visitor_share"], g["rain_heavy_pct"])
    p(f"[{region}] 업종 {len(g)}개: 약한비 rho={rho:.3f} (p={pv:.3f}), 호우 rho={rho2:.3f} (p={pv2:.3f})")

# 통과 업종의 방문객/거주자 분해
p("\n--- 약한 비에서 q<0.1 통과한 업종의 동일시도/타시도 분해 ---")
key = res[res["rain_light_q"] < Q_THRESH][["region", "industry"]]
vt = core.groupby(["MCT_SGG_CD", "MCT_RY_CD", "visitor", "date"])["TS_AT"].sum().reset_index()
rows = []
for r in key.itertuples():
    for flag, label in [(False, "동일시도"), (True, "타시도")]:
        s = vt[(vt["MCT_SGG_CD"] == r.region) & (vt["MCT_RY_CD"] == r.industry) & (vt["visitor"] == flag)].set_index("date")["TS_AT"]
        if s.notna().sum() >= n_days * 0.9:
            rr = fit(r.region, s)
            rows.append({"region": r.region, "industry": r.industry, "who": label, "n_days": rr["n_days"],
                         "rain_light_pct": rr["rain_light_pct"], "p": rr["rain_light_p"]})
p(pd.DataFrame(rows).round(3).to_string(index=False) if rows else "(없음)")
out.close()
print("done")
