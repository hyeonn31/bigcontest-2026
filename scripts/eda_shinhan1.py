import pandas as pd

path = r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터1.txt"
out_path = r"C:\Users\user\Downloads\SH\bigcontest\eda_output\eda_shinhan1_result.txt"

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

    p('\n=== TIME_GB 값 분포 ===')
    p(df['TIME_GB'].value_counts())

    p('\n=== MCT_SGG_CD 값 분포 ===')
    p(df['MCT_SGG_CD'].value_counts())

    p('\n=== MCT_RY_CD (업종) 고유값 개수 ===')
    p(df['MCT_RY_CD'].nunique())
    p(df['MCT_RY_CD'].value_counts().head(20))

    p('\n=== SEX_CCD 값 분포 ===')
    p(df['SEX_CCD'].value_counts())

    p('\n=== AGE_CCD 값 분포 ===')
    p(df['AGE_CCD'].value_counts())

    p('\n=== TS_AT (결제금액) 기술통계 ===')
    p(df['TS_AT'].describe())

    p('\n=== USE_CNT (결제건수) 기술통계 ===')
    p(df['USE_CNT'].describe())

    p('\n=== TS_AT 상위 5개 행 ===')
    p(df.sort_values('TS_AT', ascending=False).head(5).to_string())

    p('\n=== 법인 관련 행 개수 (SEX_CCD == 법인) ===')
    p((df['SEX_CCD'] == '법인').sum())

print('done, wrote to', out_path)
