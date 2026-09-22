"""최종 분석 질문 후보 (a)(b)(c)를 같은 잣대로 비교한다.

(a) 레저·야외 업종 vs 생활 업종의 비 민감도 차이
(b) 타 시도 거주자 vs 동일 시도 거주자의 반응 차이
(c) 호우일 시간대별 충격 (하루 소비 중 시간대 비중 변화)

모형은 industry_analysis.py와 동일: log(y) ~ 월 + 요일 + 공휴일 + 약한비 + 호우 + 폭염, HAC(3일).
"차이"는 두 계열의 로그 비율을 종속변수로 놓고 직접 검정한다.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr

BASE = r"C:\Users\user\Downloads\SH\bigcontest"
OUT_TXT = os.path.join(BASE, "eda_output", "compare_candidates.txt")
EXCL = ["세금공과금", "ZZ_나머지"]
N_PERM = 10000
rng = np.random.default_rng(42)

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


def fit_log(region, ylog):
    """이미 로그를 취한 계열을 회귀. 계수는 (exp-1)*100 % 로 환산"""
    ylog = ylog.replace([np.inf, -np.inf], np.nan).dropna()
    X = DESIGN[region].loc[ylog.index]
    res = sm.OLS(ylog, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out = {"n_days": len(ylog)}
    for t in TERMS:
        out[f"{t}_pct"] = (np.exp(res.params[t]) - 1) * 100
        out[f"{t}_p"] = res.pvalues[t]
    return out


def fit(region, y):
    y = y.dropna()
    y = y[y > 0]
    return fit_log(region, np.log(y))


def perm_diff(a, b, n=N_PERM):
    """두 그룹 평균 차이의 순열검정 (업종 라벨을 섞음)"""
    a, b = np.asarray(a), np.asarray(b)
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b])
    cnt = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(pool[:len(a)].mean() - pool[len(a):].mean()) >= abs(obs):
            cnt += 1
    return obs, (cnt + 1) / (n + 1)


out = open(OUT_TXT, "w", encoding="utf-8")


def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()


p("후보 (a)(b)(c) 비교. 모형: log(y) ~ 월+요일+공휴일+약한비(1~30mm)+호우(30mm+)+폭염(33℃+), HAC(3일)")
p("효과(%) = '비 안 온 평범한 날' 대비. 차이 검정은 두 계열의 로그 비율을 종속변수로 회귀\n")

# ================= (b) 타 시도 vs 동일 시도 거주자 =================
p("=" * 15, "(b) 타 시도 거주자 vs 동일 시도 거주자 — 지역 전체", "=" * 15)
p("종속변수 = log(타시도 금액 / 동일시도 금액). 음수 = 비 온 날 타시도가 동일시도보다 '더' 줄어듦")
rows = []
for region, g in m.groupby("region"):
    g = g.set_index("date").sort_index()
    r = fit_log(region, np.log(g["s2c_visitor_amt"]) - np.log(g["s2c_local_amt"]))
    rows.append({"region": region, **r})
p(pd.DataFrame(rows).drop(columns=["heat_day_pct", "heat_day_p"]).round(3).to_string(index=False))

# ---- 데이터2 로드 (업종·방문객) ----
d2 = pd.read_csv(os.path.join(BASE, "data", "shinhan_card", "신한카드_빅콘테스트2026_데이터2_수정.txt"), sep="\t", encoding="utf-8-sig")
d2["date"] = pd.to_datetime(d2["TA_YMD"].astype(str), format="%Y%m%d")
core = d2[~d2["MCT_RY_CD"].isin(EXCL)].copy()
core["visitor"] = core["MCT_SGG_CD"].str.split(" ").str[0] != core["CLN_SGG_CD"]
n_days = m["date"].nunique()

eff = pd.read_csv(os.path.join(BASE, "data", "processed", "industry_rain_effects.csv"), encoding="utf-8-sig")
elig = eff[["region", "industry"]]

# ---- (b) 업종 단위: 타시도가 더 줄어드는 업종이 다수인가 ----
p("\n" + "-" * 10, "(b) 업종 단위: 업종별 log(타시도/동일시도) 회귀의 계수 분포", "-" * 10)
vt = core.groupby(["MCT_SGG_CD", "MCT_RY_CD", "visitor", "date"])["TS_AT"].sum().unstack("visitor")
rows = []
for r in elig.itertuples():
    key = (r.region, r.industry)
    if key not in vt.index.droplevel(-1).unique():
        continue
    s = vt.loc[key]
    s = s.dropna()
    s = s[(s[True] > 0) & (s[False] > 0)]
    if len(s) < n_days * 0.9:
        continue
    res = fit_log(r.region, np.log(s[True]) - np.log(s[False]))
    rows.append({"region": r.region, "industry": r.industry, **res})
bi = pd.DataFrame(rows)
for region, g in bi.groupby("region"):
    for t in ["rain_light", "rain_heavy"]:
        v = g[f"{t}_pct"]
        n_neg = int((v < 0).sum())
        # 부호검정: 업종 절반이 음수일 것이라는 귀무가설
        from scipy.stats import binomtest
        bp = binomtest(n_neg, len(v), 0.5).pvalue
        p(f"[{region}] {t}: 업종 {len(v)}개 중 타시도가 더 줄어든 업종 {n_neg}개 ({n_neg/len(v):.0%}), "
          f"중앙값 {v.median():.1f}%, 평균 {v.mean():.1f}%, 부호검정 p={bp:.3f}")

# ================= (a) 레저·야외 vs 생활 업종 =================
p("\n" + "=" * 15, "(a) 레저·야외 업종 vs 생활 업종", "=" * 15)
OUTDOOR = ["실내/실외골프장", "종합레저타운/놀이동산", "스포츠/레저용품", "스포츠시설", "호텔/콘도", "모텔,여관,기타숙박", "여행사/항공사"]
DAILY = ["할인점/슈퍼마켓/양판점", "편의점", "약국", "일반병원", "종합병원", "치과병원", "한의원", "주유소", "LPG가스",
         "농수산물", "정육점", "제과점", "기타식품", "한식", "세탁소", "미용실", "통신요금(이동,시내전화)", "보험", "학원/학습지"]
p("분류 기준(사전 정의): 레저·야외 =", OUTDOOR)
p("                    생활 =", DAILY)
p("※ 이 분류는 이전 결과(골프장·놀이동산이 크게 감소)를 본 뒤에 정했으므로 결과에 유리하게 정해졌을 위험이 있음 → 아래 '분류 없는 대리 지표'로 교차 확인\n")
eff["group"] = np.where(eff["industry"].isin(OUTDOOR), "레저·야외", np.where(eff["industry"].isin(DAILY), "생활", "기타"))
for region, g in eff.groupby("region"):
    a, b = g[g["group"] == "레저·야외"], g[g["group"] == "생활"]
    p(f"[{region}] 레저·야외 {len(a)}개: {a['industry'].tolist()}")
    p(f"          생활 {len(b)}개")
    for t in ["rain_light_pct", "rain_heavy_pct"]:
        if len(a) >= 2 and len(b) >= 2:
            obs, pv = perm_diff(a[t], b[t])
            p(f"  {t}: 레저·야외 평균 {a[t].mean():.1f}%, 생활 평균 {b[t].mean():.1f}%, 차이 {obs:.1f}%p, 순열검정 p={pv:.3f}")
        else:
            p(f"  {t}: 그룹 표본 부족(레저·야외 {len(a)}개)")

# 분류 없는 대리 지표: 주말/평일 소비 비율 (재량·여가 소비일수록 주말 비중이 큼)
p("\n" + "-" * 10, "(a) 분류 없는 대리 지표: 업종별 주말/평일 소비 비율 vs 비 효과 (스피어만)", "-" * 10)
hol = m.drop_duplicates("date").set_index("date")["is_holiday"]
ind = core.groupby(["MCT_SGG_CD", "MCT_RY_CD", "date"])["TS_AT"].sum().reset_index()
ind["holiday"] = ind["date"].map(hol)
ind = ind[~ind["holiday"]]
ind["wkend"] = ind["date"].dt.dayofweek >= 5
wr = ind.groupby(["MCT_SGG_CD", "MCT_RY_CD", "wkend"])["TS_AT"].mean().unstack("wkend")
wr["weekend_ratio"] = wr[True] / wr[False]
wr = wr["weekend_ratio"].rename_axis(["region", "industry"]).reset_index()
e2 = eff.merge(wr, on=["region", "industry"], how="left")
for region, g in e2.groupby("region"):
    g = g.dropna(subset=["weekend_ratio"])
    for t in ["rain_light_pct", "rain_heavy_pct"]:
        rho, pv = spearmanr(g["weekend_ratio"], g[t])
        p(f"[{region}] 업종 {len(g)}개: 주말비율 vs {t} rho={rho:.3f} (p={pv:.3f})  ※ rho<0 이면 주말형(여가형) 업종일수록 비에 더 줄어듦")

# ================= (c) 시간대별 =================
p("\n" + "=" * 15, "(c) 호우일 시간대별 충격 — 하루 소비 중 시간대 비중의 변화", "=" * 15)
p("종속변수 = log(시간대 금액 / 그날 전체 금액). 0이면 그 시간대만 유독 줄거나 늘지 않았다는 뜻 (전체가 줄어든 것은 제외됨)")
d1 = pd.read_csv(os.path.join(BASE, "data", "shinhan_card", "신한카드_빅콘테스트2026_데이터1.txt"), sep="\t", encoding="utf-8-sig")
d1 = d1[(d1["SEX_CCD"] != "법인") & (~d1["MCT_RY_CD"].isin(EXCL))].copy()
d1["date"] = pd.to_datetime(d1["TA_YMD"].astype(str), format="%Y%m%d")
tb = d1.groupby(["MCT_SGG_CD", "date", "TIME_GB"])["TS_AT"].sum().unstack("TIME_GB")
rows = []
for region in tb.index.get_level_values(0).unique():
    t = tb.loc[region]
    total = t.sum(axis=1)
    for band in t.columns:
        r = fit_log(region, np.log(t[band] / total))
        rows.append({"region": region, "time": band, **r})
p(pd.DataFrame(rows).drop(columns=["heat_day_pct", "heat_day_p"]).round(3).to_string(index=False))
p("\n참고: 시간대는 6시간 단위 4개뿐이고 호우일은 14~18일. 비의 '시간대'(언제 왔는지)는 반영하지 않고 하루 강수량만 씀")
out.close()
print("done")
