import pandas as pd

path = r"C:\Users\user\Downloads\SH\bigcontest\data\weather\OBS_ASOS_TIM_20260918173259.csv"
out_path = r"C:\Users\user\Downloads\SH\bigcontest\eda_output\weather_explore.txt"

df = pd.read_csv(path, encoding='utf-8-sig')
df['일시'] = pd.to_datetime(df['일시'])

with open(out_path, 'w', encoding='utf-8') as f:
    def p(*a):
        f.write(' '.join(str(x) for x in a) + '\n')

    p('=== 컬럼 ===')
    p(df.columns.tolist())

    p('\n=== 지점별 일시 범위/행수 ===')
    p(df.groupby('지점명')['일시'].agg(['min', 'max', 'count']))

    p('\n=== 강수량: 값 유무 x QC플래그 교차표 ===')
    p(pd.crosstab(df['강수량(mm)'].notna().rename('강수량_값있음'),
                  df['강수량 QC플래그'].fillna('blank')))

    p('\n=== 강수량 QC플래그 값 분포 ===')
    p(df['강수량 QC플래그'].value_counts(dropna=False))

    p('\n=== 강수량 값이 있는 행의 통계 ===')
    p(df['강수량(mm)'].describe())

    p('\n=== 기온 결측 행 ===')
    p(df[df['기온(°C)'].isna()][['지점명', '일시', '기온(°C)', '기온 QC플래그']])

    p('\n=== 풍속/습도 결측 개수 ===')
    p(df[['풍속(m/s)', '습도(%)']].isna().sum())

    p('\n=== 지점별 강수량 QC플래그 9 개수 ===')
    p(df[df['강수량 QC플래그'] == 9].groupby('지점명').size())

    # 강수량 QC 9인 시각이 하루 중 어디에 몰려있는지
    q9 = df[df['강수량 QC플래그'] == 9]
    p('\n=== QC플래그 9 행이 몰린 날짜 상위 10 ===')
    p(q9.groupby([q9['지점명'], q9['일시'].dt.date]).size().sort_values(ascending=False).head(10))

    p('\n=== 월별 강수량 합계 (blank=0 가정) ===')
    tmp = df.copy()
    tmp['강수량(mm)'] = tmp['강수량(mm)'].fillna(0)
    p(tmp.groupby(['지점명', tmp['일시'].dt.to_period('M')])['강수량(mm)'].sum())

print('done ->', out_path)
