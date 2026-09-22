"""SK 유동인구 활용 방안: 인과검정이 아니라 "지역 성격을 보여주는 배경 지표"로 사용한다
(SK는 월×요일 평균 패턴이라 일별 실측이 아니므로 회귀 검정에는 못 씀 — notes.md 기존 결론).

두 그래프로 "춘천은 여가/방문형, 강남은 생활/직장형" 성격 차이를 정량적으로 보여준다:
1. 시간대별 유동인구 비중(%) 곡선 — 강남은 출퇴근 쌍봉, 춘천은 낮 시간 단봉일 것으로 예상
2. 주말 vs 평일 유동인구 비중 — 춘천이 더 주말에 몰릴 것으로 예상

이건 "왜 춘천 방문객이 날씨에 더 민감한가"를 뒷받침하는 정성적(구조적) 근거로,
카드 데이터의 통계적 검정 결과와는 별개의 보조 증거임을 report에 명시.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

BASE = r"C:\SH_Antigravity\bigcontest"
FIG = os.path.join(BASE, "figures")
OUT_TXT = os.path.join(BASE, "eda_output", "sk_flow_characterization.txt")

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False
BLUE, RED, GRAY = "#3B6FA0", "#D45B5B", "#8C8C8C"

wkdy = pd.read_csv(os.path.join(BASE, "data", "processed", "sk_wkdy_region_month.csv"), encoding="utf-8-sig")
time = pd.read_csv(os.path.join(BASE, "data", "processed", "sk_time_region_month.csv"), encoding="utf-8-sig")

out = open(OUT_TXT, "w", encoding="utf-8")


def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n")
    print(line)


p("SK 유동인구 특성 비교 (6개월 평균, 월별 요일/시간대 평균 패턴 기준)\n")

# ---- 1. 주말 비중 ----
wkdy_g = wkdy.groupby("region")[["FLOW_POP_CNT_MON", "FLOW_POP_CNT_TUS", "FLOW_POP_CNT_WED",
                                   "FLOW_POP_CNT_THU", "FLOW_POP_CNT_FRI", "FLOW_POP_CNT_SAT",
                                   "FLOW_POP_CNT_SUN"]].mean()
weekend_share = (wkdy_g["FLOW_POP_CNT_SAT"] + wkdy_g["FLOW_POP_CNT_SUN"]) / wkdy_g.sum(axis=1) * 100
p("[주말(토+일) 유동인구 비중]")
for r, v in weekend_share.items():
    p(f"  {r}: {v:.1f}% (7일 균등 분배 시 기준값 28.6%)")

# ---- 2. 시간대별 유동인구 비중(%) ----
time_cols = [f"TMST_{h:02d}" for h in range(24)]
time_g = time.groupby("region")[time_cols].mean()
time_pct = time_g.div(time_g.sum(axis=1), axis=0) * 100

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

ax = axes[0]
for r, color in [("서울 강남구", BLUE), ("강원 춘천시", RED)]:
    ax.plot(range(24), time_pct.loc[r], "o-", color=color, label=r, linewidth=2.5, markersize=4)
ax.set_xlabel("시간대")
ax.set_ylabel("하루 유동인구 중 비중 (%)")
ax.set_title("시간대별 유동인구 패턴", fontsize=15, fontweight="bold")
ax.legend()
ax.set_xticks(range(0, 24, 3))
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)

ax = axes[1]
regions = ["서울 강남구", "강원 춘천시"]
vals = [weekend_share[r] for r in regions]
bars = ax.bar(regions, vals, color=[BLUE, RED], width=0.5)
ax.axhline(28.6, color=GRAY, linestyle="--", linewidth=1.5, label="7일 균등 분배 기준(28.6%)")
for i, v in enumerate(vals):
    ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=16, fontweight="bold")
ax.set_ylabel("주말(토+일) 유동인구 비중 (%)")
ax.set_title("주말 쏠림 정도", fontsize=15, fontweight="bold")
ax.legend(fontsize=9)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)

fig.suptitle("SK 유동인구로 본 지역 성격: 강남(직장/생활형) vs 춘천(여가/방문형)", fontsize=15, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "pt_04_sk_flow_character.png"), dpi=150, bbox_inches="tight")
plt.close()

p("\n[시간대별 패턴 요약]")
for r in regions:
    peak_hour = time_pct.loc[r].idxmax()
    p(f"  {r}: 최대 시간대 {peak_hour}, 출근시간대(08-09시) 비중 {time_pct.loc[r, ['TMST_08','TMST_09']].sum():.1f}%, "
      f"퇴근시간대(18-19시) 비중 {time_pct.loc[r, ['TMST_18','TMST_19']].sum():.1f}%")

p(f"\nsaved: {os.path.join(FIG, 'pt_04_sk_flow_character.png')}")
p("\n주의: 이 그래프는 인과 검정이 아니라 SK 유동인구를 '지역 성격을 보여주는 배경 지표'로 쓴 것.")
p("SK는 월x요일 평균 패턴이라 일별 실측이 아니므로 회귀 검정(카드소비 분석)에는 사용하지 않음.")
out.close()
