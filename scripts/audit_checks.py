import glob
import os
import numpy as np
import pandas as pd

BASE = r"C:\Users\user\Downloads\SH\bigcontest"
OUT = os.path.join(BASE, "eda_output", "audit_checks.txt")
f = open(OUT, "w", encoding="utf-8")


def p(*a):
    f.write(" ".join(str(x) for x in a) + "\n")
    f.flush()


# ---------- A. SK 파일별 구조 점검 (12월 파일이 2배 크기인 이유) ----------
p("=" * 20, "A. SK 파일별 점검", "=" * 20)
rows = []
for fp in sorted(glob.glob(os.path.join(BASE, "data", "sk_flow_pop", "*.csv"))):
    d = pd.read_csv(fp, sep="|", encoding="utf-8-sig", low_memory=False)
    d["region"] = np.where(d["X_COORD"] < 983000, "gangnam", "chuncheon")
    key = d.duplicated(["STD_YM", "BLOCK_CD", "X_COORD", "Y_COORD"]).sum()
    xy = d.duplicated(["STD_YM", "X_COORD", "Y_COORD"]).sum()
    rows.append({
        "file": os.path.basename(fp),
        "rows": len(d),
        "STD_YM_values": ",".join(map(str, sorted(d["STD_YM"].unique()))),
        "cells_gangnam": int((d["region"] == "gangnam").sum()),
        "cells_chuncheon": int((d["region"] == "chuncheon").sum()),
        "dup_pk": int(key),
        "dup_xy": int(xy),
        "n_block_cd": d["BLOCK_CD"].nunique(),
    })
p(pd.DataFrame(rows).to_string(index=False))

# ---------- C. 강수량 QC플래그 9의 정체 ----------
p("\n" + "=" * 20, "C. 강수량 빈칸(QC=9)은 정말 '비 없음'인가", "=" * 20)
w = pd.read_csv(os.path.join(BASE, "data", "weather", "OBS_ASOS_TIM_20260918173259.csv"), encoding="utf-8-sig")
w["grp"] = np.select(
    [w["강수량(mm)"] > 0, w["강수량(mm)"] == 0, w["강수량 QC플래그"] == 9],
    ["값>0 (비 옴)", "값=0.0 (기록됨)", "빈칸+QC9"],
    default="빈칸+QC없음",
)
w["기온-이슬점"] = w["기온(°C)"] - w["이슬점온도(°C)"]
p(w.groupby("grp").agg(n=("grp", "size"), 습도평균=("습도(%)", "mean"),
                        전운량평균=("전운량(10분위)", "mean"), 기온이슬점차=("기온-이슬점", "mean")).round(2).to_string())

# ---------- D. 신한카드 업종 구성 / 이상치 ----------
p("\n" + "=" * 20, "D. 신한카드 데이터2 업종 구성", "=" * 20)
d2 = pd.read_csv(os.path.join(BASE, "data", "shinhan_card", "신한카드_빅콘테스트2026_데이터2_수정.txt"),
                 sep="\t", encoding="utf-8-sig")
tot = d2["TS_AT"].sum()
by_ind = d2.groupby("MCT_RY_CD")["TS_AT"].sum().sort_values(ascending=False)
p("전체 금액 대비 업종 비중 상위 10:")
p((by_ind.head(10) / tot).round(4).to_string())
p("\n지역별 세금공과금 + ZZ_나머지 비중:")
for reg, g in d2.groupby("MCT_SGG_CD"):
    s = g[g["MCT_RY_CD"].isin(["세금공과금", "ZZ_나머지"])]["TS_AT"].sum() / g["TS_AT"].sum()
    p(reg, round(s, 4))

p("\nUSE_CNT<10 인 행 비중 (소규모 셀 마스킹 흔적):", round((d2["USE_CNT"] < 10).mean(), 4))
p("USE_CNT 최솟값:", d2["USE_CNT"].min())

# ---------- E. 방문객 정의 ----------
p("\n" + "=" * 20, "E. '지역주민' 정의 점검 (고객거주지는 시도 단위)", "=" * 20)
ct = d2.groupby(["MCT_SGG_CD", "CLN_SGG_CD"])["TS_AT"].sum().reset_index()
for reg, g in ct.groupby("MCT_SGG_CD"):
    g = g.assign(share=g["TS_AT"] / g["TS_AT"].sum()).sort_values("share", ascending=False).head(4)
    p(reg, "거주지 상위:", ", ".join(f"{r.CLN_SGG_CD} {r.share:.1%}" for r in g.itertuples()))

# ---------- F. 일별 이상치가 어떤 업종 때문인지 ----------
p("\n" + "=" * 20, "F. 소비지수 극단일과 원인 업종", "=" * 20)
m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"), encoding="utf-8-sig", parse_dates=["date"])
m = m.dropna(subset=["temp_mean"]).copy()
cell = m.groupby(["region", "month", "weekday"])["s2_amt"].transform("mean")
m["idx"] = m["s2_amt"] / cell
ext = m.assign(dev=(m["idx"] - 1).abs()).sort_values("dev", ascending=False).head(8)
day_ind = d2.groupby(["TA_YMD", "MCT_SGG_CD", "MCT_RY_CD"])["TS_AT"].sum()
for r in ext.itertuples():
    key = (int(r.date.strftime("%Y%m%d")), r.region)
    s = day_ind.xs(key, level=[0, 1]).sort_values(ascending=False)
    top = s.index[0]
    p(f"{r.date.date()} {r.region} idx={r.idx:.2f} 요일={r.weekday} 최대업종={top} 그날비중={s.iloc[0] / s.sum():.1%}")

# 세금공과금/ZZ_나머지 제외 시 재검정
p("\n" + "=" * 20, "G. 세금공과금·ZZ_나머지 제외 후 재검정 (순열검정 10,000회)", "=" * 20)
ex = d2[~d2["MCT_RY_CD"].isin(["세금공과금", "ZZ_나머지"])]
ex_daily = ex.groupby(["TA_YMD", "MCT_SGG_CD"])["TS_AT"].sum().reset_index()
ex_daily["date"] = pd.to_datetime(ex_daily["TA_YMD"].astype(str), format="%Y%m%d")
ex_daily = ex_daily.rename(columns={"MCT_SGG_CD": "region", "TS_AT": "ex_amt"})[["date", "region", "ex_amt"]]
m = m.merge(ex_daily, on=["date", "region"])
cell = m.groupby(["region", "month", "weekday"])["ex_amt"].transform("mean")
m["ex_idx"] = m["ex_amt"] / cell
rng = np.random.default_rng(1)
res = []
for reg, g in m.groupby("region"):
    for flag in ["heavy_rain_day", "rain_day", "heat_day", "tropical_night", "cold_day"]:
        fl = g[flag].astype(bool).to_numpy()
        x = g["ex_idx"].to_numpy()
        k = int(fl.sum())
        if k < 3:
            continue
        obs = x[fl].mean() - x[~fl].mean()
        perm = np.array([(lambda i: x[i[:k]].mean() - x[i[k:]].mean())(rng.permutation(len(x))) for _ in range(10000)])
        res.append((reg, flag, k, round(obs, 3), round((np.abs(perm) >= abs(obs)).mean(), 4)))
p(pd.DataFrame(res, columns=["region", "flag", "n_days", "diff", "p"]).to_string(index=False))
f.close()
print("done")
