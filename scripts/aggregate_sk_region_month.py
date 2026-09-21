import pandas as pd
import glob
import os

DATA_DIR = r"C:\Users\user\Downloads\SH\bigcontest\data\sk_flow_pop"
OUT_DIR = r"C:\Users\user\Downloads\SH\bigcontest\data\processed"
os.makedirs(OUT_DIR, exist_ok=True)

X_SPLIT = 983000  # X_COORD < 983000 => 서울 강남구, else 강원 춘천시


def region_of(x):
    return '서울 강남구' if x < X_SPLIT else '강원 춘천시'


def aggregate(file_prefix, out_name):
    files = sorted(glob.glob(os.path.join(DATA_DIR, f"{file_prefix}_*.csv")))
    frames = []
    for fp in files:
        df = pd.read_csv(fp, sep='|', encoding='utf-8-sig', low_memory=False)
        # 12월 time/wkdy 파일은 모든 행이 통째로 2번씩 들어 있음(값까지 동일) -> 중복 제거
        df = df.drop_duplicates()
        df['region'] = df['X_COORD'].apply(region_of)
        value_cols = [c for c in df.columns if c not in ('STD_YM', 'BLOCK_CD', 'X_COORD', 'Y_COORD', 'region')]
        g = df.groupby(['STD_YM', 'region'])[value_cols].sum().reset_index()
        # 격자(block) 개수도 같이 남겨서, 이후 지역별 커버리지 확인 가능하게 함
        block_cnt = df.groupby(['STD_YM', 'region'])['BLOCK_CD'].nunique().reset_index(name='BLOCK_CNT')
        g = g.merge(block_cnt, on=['STD_YM', 'region'])
        frames.append(g)
    result = pd.concat(frames, ignore_index=True).sort_values(['STD_YM', 'region'])
    out_path = os.path.join(OUT_DIR, out_name)
    result.to_csv(out_path, index=False, encoding='utf-8-sig')
    return result, out_path


results_log = []
for prefix, out_name in [
    ('flow_age_pop', 'sk_age_region_month.csv'),
    ('flow_time_pop', 'sk_time_region_month.csv'),
    ('flow_wkdy_pop', 'sk_wkdy_region_month.csv'),
]:
    result, out_path = aggregate(prefix, out_name)
    results_log.append((out_name, out_path, result.shape))

log_path = os.path.join(r"C:\Users\user\Downloads\SH\bigcontest\eda_output", 'aggregate_sk_log.txt')
with open(log_path, 'w', encoding='utf-8') as f:
    for out_name, out_path, shape in results_log:
        f.write(f"{out_name} -> {out_path}  shape={shape}\n")

print('done, see', log_path)
