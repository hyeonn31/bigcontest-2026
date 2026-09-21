import pandas as pd

path = r"C:\Users\user\Downloads\SH\bigcontest\data\sk_flow_pop\flow_age_pop_202507.csv"
df = pd.read_csv(path, sep='|', encoding='utf-8-sig')

out_path = r"C:\Users\user\Downloads\SH\bigcontest\eda_output\sk_region_explore.txt"
with open(out_path, 'w', encoding='utf-8') as f:
    def p(*a):
        f.write(' '.join(str(x) for x in a) + '\n')

    p('=== shape ===')
    p(df.shape)
    p(df.columns.tolist())

    p('\n=== BLOCK_CD 고유값 개수 ===')
    p(df['BLOCK_CD'].nunique())

    blocks = df[['BLOCK_CD', 'X_COORD', 'Y_COORD']].drop_duplicates()
    p('\n=== 격자 개수 (고유 좌표) ===')
    p(len(blocks))

    p('\n=== X_COORD 기술통계 ===')
    p(blocks['X_COORD'].describe())
    p('\n=== Y_COORD 기술통계 ===')
    p(blocks['Y_COORD'].describe())

    # X, Y 값을 정렬해서 큰 gap(간격)이 있는지 확인 -> 두 지역이 떨어져 있으면 gap이 보일 것
    xs = blocks['X_COORD'].sort_values().reset_index(drop=True)
    x_diffs = xs.diff().fillna(0)
    top_gaps_x = x_diffs.sort_values(ascending=False).head(5)
    p('\n=== X_COORD 정렬 후 가장 큰 간격 5개 (인덱스: 값) ===')
    for idx in top_gaps_x.index:
        p('gap=', x_diffs[idx], ' at value=', xs[idx], ' prev=', xs[idx-1] if idx > 0 else None)

    ys = blocks['Y_COORD'].sort_values().reset_index(drop=True)
    y_diffs = ys.diff().fillna(0)
    top_gaps_y = y_diffs.sort_values(ascending=False).head(5)
    p('\n=== Y_COORD 정렬 후 가장 큰 간격 5개 ===')
    for idx in top_gaps_y.index:
        p('gap=', y_diffs[idx], ' at value=', ys[idx], ' prev=', ys[idx-1] if idx > 0 else None)

print('done ->', out_path)
