import pandas as pd

path = r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터2_수정.txt"
out_path = r"C:\Users\user\Downloads\SH\bigcontest\eda_output\eda_shinhan2_result.txt"

df = pd.read_csv(path, sep='\t', encoding='utf-8-sig')

with open(out_path, 'w', encoding='utf-8') as f:
    def p(*args):
        f.write(' '.join(str(a) for a in args) + '\n')

    p('=== shape ===')
    p(df.shape)

    p('\n=== dtypes ===')
    p(df.dtypes)

    p('\n=== 결측치 개수 ===')
    p(df.isna().sum())

    p('\n=== TA_YMD 범위 ===')
    p('min:', df['TA_YMD'].min(), 'max:', df['TA_YMD'].max())
    p('고유 날짜 수:', df['TA_YMD'].nunique())

    p('\n=== MCT_SGG_CD (가맹점 위치) 값 분포 ===')
    p(df['MCT_SGG_CD'].value_counts())

    p('\n=== CLN_SGG_CD (고객 거주지) 값 분포 (상위 20) ===')
    p(df['CLN_SGG_CD'].value_counts().head(20))
    p('고유 거주지 수:', df['CLN_SGG_CD'].nunique())

    p('\n=== 가맹점위치 x 고객거주지 교차표 (상위 15) ===')
    cross = df.groupby(['MCT_SGG_CD', 'CLN_SGG_CD'])['USE_CNT'].sum().sort_values(ascending=False).head(15)
    p(cross)

    p('\n=== MCT_RY_CD (업종) 고유값 개수 ===')
    p(df['MCT_RY_CD'].nunique())

    p('\n=== SEX_CCD 값 분포 ===')
    p(df['SEX_CCD'].value_counts())

    p('\n=== AGE_CCD 값 분포 ===')
    p(df['AGE_CCD'].value_counts())

    p('\n=== TS_AT (결제금액) 기술통계 ===')
    p(df['TS_AT'].describe())

    p('\n=== USE_CNT (결제건수) 기술통계 ===')
    p(df['USE_CNT'].describe())

    p('\n=== 데이터1과 비교: 데이터2에만 있는 컬럼 ===')
    p('CLN_SGG_CD (고객 거주지) — 데이터1엔 없음, TIME_GB(시간대)는 반대로 데이터2엔 없음')

print('done, wrote to', out_path)
