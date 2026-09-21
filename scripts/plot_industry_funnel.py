import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\user\Downloads\SH\bigcontest"
res = pd.read_csv(os.path.join(BASE, "data", "processed", "industry_rain_effects.csv"), encoding="utf-8-sig")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(2, 2, figsize=(15, 10), sharex=True)
for j, (col, label) in enumerate([("rain_light", "약한 비(1~30mm)"), ("rain_heavy", "호우(30mm+)")]):
    for i, (region, g) in enumerate(res.groupby("region")):
        ax = axes[i][j]
        sig = g[f"{col}_q"] < 0.10
        x = np.log10(g["mean_daily_cnt"])
        ax.scatter(x[~sig], g.loc[~sig, f"{col}_pct"], c="#B0B0B0", s=28, label="유의하지 않음")
        ax.scatter(x[sig], g.loc[sig, f"{col}_pct"], c="#C44E52", s=42, label="FDR q<0.1")
        for r in g[sig].itertuples():
            ax.annotate(r.industry, (np.log10(r.mean_daily_cnt), getattr(r, f"{col}_pct")), fontsize=8,
                        xytext=(4, 3), textcoords="offset points")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(f"{region} · {label}", fontsize=11)
        if i == 1:
            ax.set_xlabel("업종 규모: 하루 평균 결제건수 (log10)")
        if j == 0:
            ax.set_ylabel("비 안 온 평범한 날 대비 소비 변화 (%)")
        if i == 0 and j == 0:
            ax.legend(loc="lower right", fontsize=9)
fig.suptitle("업종별 강수 효과 — 작은 업종일수록 값이 크게 흔들림 (깔때기 모양)", fontsize=13)
plt.tight_layout()
plt.savefig(os.path.join(BASE, "figures", "industry_rain_effects.png"), dpi=110)
print("done")
