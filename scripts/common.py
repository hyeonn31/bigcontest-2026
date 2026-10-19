"""[공통 모듈] 분석 스크립트 공통: 경로, 병합 데이터 로드, 로그선형 회귀(HAC).

모든 검정은 같은 틀을 쓴다: log(y) ~ 월 + 요일 더미 + terms, HAC(3일) 표준오차.
스크립트마다 다른 건 terms(통제·기후 변수)뿐이라 그것만 인자로 받는다.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAVY_MM = 30  # 호우 기준: 일 강수량 30mm 이상


def load_merged():
    """merged_daily.csv + 기후 플래그(float). 약한 비 = 1~30mm, 호우 = 30mm+"""
    m = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_daily.csv"),
                    encoding="utf-8-sig", parse_dates=["date"])
    m["rain_light"] = ((m["precip_sum"] >= 1) & (m["precip_sum"] < HEAVY_MM)).astype(float)
    m["rain_heavy"] = (m["precip_sum"] >= HEAVY_MM).astype(float)
    m["heat_day"] = m["heat_day"].astype(float)
    m["is_holiday"] = m["is_holiday"].astype(float)
    return m


def fit_hac(g, y, terms):
    """y(이미 로그) ~ 월+요일 더미 + g[terms], HAC(3일). y의 인덱스에 맞춰 g 행을 고른다"""
    # 월·요일을 범주(더미)로 통제 → "같은 달·같은 요일끼리 비교한 비 효과"가 됨.
    # drop_first: 첫 범주(7월·월요일)를 기준으로 빼서 상수항과 겹치지 않게 함(다중공선성 방지)
    X = pd.get_dummies(g[["month", "weekday"]].astype(str), drop_first=True, dtype=float)
    for c in terms:
        X[c] = g[c].astype(float)
    X = sm.add_constant(X).loc[y.index]
    # HAC(Newey-West): 오늘 소비가 어제·그제와 비슷한 자기상관이 있어도 표준오차를 바르게 잡음.
    # maxlags=3 → 최대 3일 전까지의 상관을 반영
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})


def pct_ci(res, term):
    """로그 계수 → (효과%, 95% 하한%, 상한%, p값)"""
    coef, se = res.params[term], res.bse[term]
    # log(y) 회귀의 계수 b는 "y가 exp(b)배가 된다"는 뜻 → (exp(b)-1)*100 = 변화율(%)
    # 신뢰구간도 로그 단위에서 계수±1.96*SE로 구한 뒤 같은 방식으로 %로 바꿈
    to_pct = lambda b: (np.exp(b) - 1) * 100
    return to_pct(coef), to_pct(coef - 1.96 * se), to_pct(coef + 1.96 * se), res.pvalues[term]
