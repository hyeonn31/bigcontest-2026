import os
import numpy as np
import pandas as pd

BASE = r"C:\Users\user\Downloads\SH\bigcontest"
f = open(os.path.join(BASE, "eda_output", "audit_checks2.txt"), "w", encoding="utf-8")


def p(*a):
    f.write(" ".join(str(x) for x in a) + "\n")
    f.flush()


# 1. SK 12월 중복행이 값까지 완전히 같은가
p("== 1. SK 12월 중복 행: 값까지 완전 동일한가 ==")
for name in ["flow_time_pop_202512.csv", "flow_wkdy_pop_202512.csv"]:
    d = pd.read_csv(os.path.join(BASE, "data", "sk_flow_pop", name), sep="|", encoding="utf-8-sig", low_memory=False)
    n_all = len(d)
    n_full_dup = int(d.duplicated().sum())
    n_key_dup = int(d.duplicated(["STD_YM", "BLOCK_CD", "X_COORD", "Y_COORD"]).sum())
    p(name, "전체", n_all, "| 모든 컬럼 동일한 중복행", n_full_dup, "| 키 중복행", n_key_dup)

# 2. 신한카드 중복 행
p("\n== 2. 신한카드 중복 점검 ==")
d1 = pd.read_csv(os.path.join(BASE, "data", "shinhan_card", "신한카드_빅콘테스트2026_데이터1.txt"), sep="\t", encoding="utf-8-sig")
k1 = ["TA_YMD", "TIME_GB", "MCT_SGG_CD", "MCT_RY_CD", "SEX_CCD", "AGE_CCD"]
p("데이터1 키 중복행:", int(d1.duplicated(k1).sum()), "/ 전체 동일행:", int(d1.duplicated().sum()))
d2 = pd.read_csv(os.path.join(BASE, "data", "shinhan_card", "신한카드_빅콘테스트2026_데이터2_수정.txt"), sep="\t", encoding="utf-8-sig")
k2 = ["TA_YMD", "MCT_SGG_CD", "MCT_RY_CD", "CLN_SGG_CD", "SEX_CCD", "AGE_CCD"]
p("데이터2 키 중복행:", int(d2.duplicated(k2).sum()), "/ 전체 동일행:", int(d2.duplicated().sum()))

# 3. QC9 행이 '비 올 때 누락'처럼 보이는지
p("\n== 3. QC9 행 중 '비 오는 조건'(습도>=93 & 기온-이슬점<1.5) 비율 ==")
w = pd.read_csv(os.path.join(BASE, "data", "weather", "OBS_ASOS_TIM_20260918173259.csv"), encoding="utf-8-sig")
w["dep"] = w["기온(°C)"] - w["이슬점온도(°C)"]
wet = (w["습도(%)"] >= 93) & (w["dep"] < 1.5)
grp = np.select([w["강수량(mm)"] > 0, w["강수량(mm)"] == 0, w["강수량 QC플래그"] == 9], ["비옴(값>0)", "0.0기록", "QC9"], default="빈칸(플래그없음)")
p(pd.Series(wet.groupby(grp).mean().round(3)).to_string())
p("QC9 중 wet 조건 행 수:", int(wet[grp == "QC9"].sum()), "/", int((grp == "QC9").sum()))
f.close()
print("done")
