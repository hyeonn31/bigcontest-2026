import glob
import os
import pandas as pd

BASE = r"C:\Users\user\Downloads\SH\bigcontest"
PROC = os.path.join(BASE, "data", "processed")
WEATHER_FILES = sorted(glob.glob(os.path.join(BASE, "data", "weather", "OBS_ASOS_TIM_*.csv")))
LOG = os.path.join(BASE, "eda_output", "merge_log.txt")

REGION_MAP = {"서울": "서울 강남구", "춘천": "강원 춘천시"}

# ---------- 1. 기상: 시간자료 -> 일자료 ----------
# 여러 번 나눠 받은 파일을 이어 붙이고, 겹치는 시각(지점+일시)은 하나만 남김
w = pd.concat([pd.read_csv(fp, encoding="utf-8-sig") for fp in WEATHER_FILES], ignore_index=True)
w = w.drop_duplicates(["지점", "일시"])
w["dt"] = pd.to_datetime(w["일시"])
# 기상청 관례: 01시~24시(=다음날 00시)가 하루. 00:00 관측치는 전날에 속함
w["date"] = (w["dt"] - pd.Timedelta(hours=1)).dt.normalize()
w["region"] = w["지점명"].map(REGION_MAP)
# 강수량 빈칸(QC플래그 9 포함)은 "강수 없음"으로 간주 (가정)
w["precip"] = w["강수량(mm)"].fillna(0)

weather = (
    w.groupby(["region", "date"])
    .agg(
        temp_mean=("기온(°C)", "mean"),
        temp_max=("기온(°C)", "max"),
        temp_min=("기온(°C)", "min"),
        precip_sum=("precip", "sum"),
        precip_max_1h=("precip", "max"),
        rain_hours=("precip", lambda s: int((s > 0).sum())),
        wind_max=("풍속(m/s)", "max"),
        wind_mean=("풍속(m/s)", "mean"),
        humidity_mean=("습도(%)", "mean"),
        n_hours=("dt", "count"),
    )
    .reset_index()
)

# 기후 이벤트 플래그 (기상청 특보 기준을 단순화한 대리 기준 — 임계값은 가정)
weather["heat_day"] = weather["temp_max"] >= 33          # 폭염일: 일 최고기온 33도 이상
weather["tropical_night"] = weather["temp_min"] >= 25    # 열대야(단순화): 일 최저기온 25도 이상
weather["cold_day"] = weather["temp_min"] <= -10         # 강추위(단순화): 일 최저기온 -10도 이하
weather["rain_day"] = weather["precip_sum"] >= 1         # 강수일: 일 강수량 1mm 이상
weather["heavy_rain_day"] = weather["precip_sum"] >= 30  # 호우(단순화): 일 강수량 30mm 이상

weather.to_csv(os.path.join(PROC, "weather_daily.csv"), index=False, encoding="utf-8-sig")

# ---------- 2. 신한카드 일x지역 ----------
def load_daily(name, prefix):
    d = pd.read_csv(os.path.join(PROC, name), encoding="utf-8-sig")
    d["date"] = pd.to_datetime(d["TA_YMD"].astype(str), format="%Y%m%d")
    d = d.rename(columns={"MCT_SGG_CD": "region"})
    return d.drop(columns="TA_YMD").rename(columns={"TS_AT": f"{prefix}_amt", "USE_CNT": f"{prefix}_cnt"})

s1_all = load_daily("shinhan1_daily_region_all.csv", "s1_all")
s1_cons = load_daily("shinhan1_daily_region_consumer_only.csv", "s1_cons")
s2 = load_daily("shinhan2_daily_region.csv", "s2")

def load_visitor(name, prefix):
    # 주의: "지역주민"은 고객 거주지(시도)가 가맹점 시도와 같다는 뜻 -> 강남구는 서울 전체, 춘천시는 강원도 전체
    vt = pd.read_csv(os.path.join(PROC, name), encoding="utf-8-sig")
    vt["date"] = pd.to_datetime(vt["TA_YMD"].astype(str), format="%Y%m%d")
    vt = vt.rename(columns={"MCT_SGG_CD": "region"})
    vt["vtype"] = vt["visitor_type"].map({"지역주민": "local", "외부방문객": "visitor", "정보없음": "unknown"})
    wide = vt.pivot_table(index=["date", "region"], columns="vtype", values=["TS_AT", "USE_CNT"], aggfunc="sum")
    wide.columns = [f"{prefix}_{v}_{'amt' if m == 'TS_AT' else 'cnt'}" for m, v in wide.columns]
    return wide.reset_index()


vt_wide = load_visitor("shinhan2_daily_region_visitor_type.csv", "s2")
# 핵심 소비: 세금공과금·ZZ_나머지 제외 (s2c_*)
s2c = load_daily("shinhan2_daily_region_core.csv", "s2c")
vtc_wide = load_visitor("shinhan2_daily_region_visitor_type_core.csv", "s2c")

merged = (
    s1_all.merge(s1_cons, on=["date", "region"])
    .merge(s2, on=["date", "region"])
    .merge(vt_wide, on=["date", "region"])
    .merge(s2c, on=["date", "region"])
    .merge(vtc_wide, on=["date", "region"])
)

# ---------- 3. SK 유동인구: 월x요일 평균 패턴을 각 날짜의 요일에 대입 (일별 실측이 아님) ----------
sk = pd.read_csv(os.path.join(PROC, "sk_wkdy_region_month.csv"), encoding="utf-8-sig")
wk_cols = {
    0: "FLOW_POP_CNT_MON", 1: "FLOW_POP_CNT_TUS", 2: "FLOW_POP_CNT_WED", 3: "FLOW_POP_CNT_THU",
    4: "FLOW_POP_CNT_FRI", 5: "FLOW_POP_CNT_SAT", 6: "FLOW_POP_CNT_SUN",
}
sk_long = sk.melt(id_vars=["STD_YM", "region"], value_vars=list(wk_cols.values()),
                  var_name="col", value_name="sk_flow_baseline")
inv = {v: k for k, v in wk_cols.items()}
sk_long["weekday"] = sk_long["col"].map(inv)

merged["month"] = merged["date"].dt.year * 100 + merged["date"].dt.month
merged["weekday"] = merged["date"].dt.weekday
merged["is_weekend"] = merged["weekday"] >= 5
# 2025 하반기 공휴일: 광복절 8/15, 개천절~한글날 10/3~10/9(추석 연휴+대체공휴일 포함), 성탄절 12/25 (검색으로 확인, 2026-09-21)
HOLIDAYS = pd.to_datetime(["2025-08-15", "2025-12-25"] + [d.strftime("%Y-%m-%d") for d in pd.date_range("2025-10-03", "2025-10-09")])
merged["is_holiday"] = merged["date"].isin(HOLIDAYS)
merged = merged.merge(
    sk_long[["STD_YM", "region", "weekday", "sk_flow_baseline"]],
    left_on=["month", "region", "weekday"], right_on=["STD_YM", "region", "weekday"], how="left",
).drop(columns="STD_YM")

merged = merged.merge(weather, on=["date", "region"], how="left")
merged = merged.sort_values(["region", "date"]).reset_index(drop=True)
merged.to_csv(os.path.join(PROC, "merged_daily.csv"), index=False, encoding="utf-8-sig")

# ---------- 4. 로그 + 첫 탐색 ----------
with open(LOG, "w", encoding="utf-8") as f:
    def p(*a):
        f.write(" ".join(str(x) for x in a) + "\n")

    p("=== merged_daily shape ===", merged.shape)
    p("날짜 범위:", merged["date"].min().date(), "~", merged["date"].max().date())
    p("\n=== 기상 결측(NaN) 날짜 ===")
    p(merged[merged["temp_mean"].isna()][["date", "region"]].to_string())
    p("\n=== SK baseline 결측 개수 ===", merged["sk_flow_baseline"].isna().sum())
    p("\n=== 기상 하루 관측시간 수 분포 (24여야 정상) ===")
    p(weather["n_hours"].value_counts())

    p("\n=== 지역별 기후 이벤트 일수 ===")
    flags = ["heat_day", "tropical_night", "cold_day", "rain_day", "heavy_rain_day"]
    p(weather.groupby("region")[flags].sum())
    p("\n=== 지역별 기온/강수 요약 ===")
    p(weather.groupby("region")[["temp_mean", "temp_max", "temp_min", "precip_sum"]].describe().T.to_string())

    # 첫 탐색: 같은 (지역, 월, 요일) 평균 대비 당일 소비 비율
    m = merged.dropna(subset=["temp_mean"]).copy()
    for col in ["s2_amt", "s2c_amt", "s2c_local_amt", "s2c_visitor_amt"]:
        cell_mean = m.groupby(["region", "month", "weekday"])[col].transform("mean")
        m[f"{col}_idx"] = m[col] / cell_mean
    idx_cols = [c for c in m.columns if c.endswith("_idx")]

    p("\n=== [탐색용] 기후 플래그별 소비지수 평균 (1.0 = 같은 지역·월·요일 평균). 표본 수 작으면 해석 주의 ===")
    for flag in flags:
        p(f"\n-- {flag} --")
        t = m.groupby(["region", flag])[idx_cols].mean()
        t["n_days"] = m.groupby(["region", flag]).size()
        p(t.round(3).to_string())

print("done ->", LOG)
