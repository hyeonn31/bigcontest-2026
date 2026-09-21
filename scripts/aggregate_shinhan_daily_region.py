import pandas as pd
import os

OUT_DIR = r"C:\Users\user\Downloads\SH\bigcontest\data\processed"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터1: 법인 포함 원본, 법인 제외본 둘 다 만든다
path1 = r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터1.txt"
df1 = pd.read_csv(path1, sep='\t', encoding='utf-8-sig')

agg_all = df1.groupby(['TA_YMD', 'MCT_SGG_CD'])[['TS_AT', 'USE_CNT']].sum().reset_index()
agg_all.to_csv(os.path.join(OUT_DIR, 'shinhan1_daily_region_all.csv'), index=False, encoding='utf-8-sig')

df1_consumer = df1[df1['SEX_CCD'] != '법인']
agg_consumer = df1_consumer.groupby(['TA_YMD', 'MCT_SGG_CD'])[['TS_AT', 'USE_CNT']].sum().reset_index()
agg_consumer.to_csv(os.path.join(OUT_DIR, 'shinhan1_daily_region_consumer_only.csv'), index=False, encoding='utf-8-sig')

# 데이터2: 법인 이미 제외됨, 고객 거주지까지 살아있는 채로 날짜x가맹점지역 집계
path2 = r"C:\Users\user\Downloads\SH\bigcontest\data\shinhan_card\신한카드_빅콘테스트2026_데이터2_수정.txt"
df2 = pd.read_csv(path2, sep='\t', encoding='utf-8-sig')

agg2 = df2.groupby(['TA_YMD', 'MCT_SGG_CD'])[['TS_AT', 'USE_CNT']].sum().reset_index()
agg2.to_csv(os.path.join(OUT_DIR, 'shinhan2_daily_region.csv'), index=False, encoding='utf-8-sig')

# 데이터2: 지역주민(거주지==가맹점 시도) vs 외부방문객 구분한 집계도 만든다
def local_flag(row):
    mct = row['MCT_SGG_CD']  # 예: '서울 강남구'
    cln = row['CLN_SGG_CD']  # 예: '서울'
    mct_sido = mct.split(' ')[0]
    return '지역주민' if mct_sido == cln else ('정보없음' if cln == '정보없음' else '외부방문객')

df2['visitor_type'] = df2.apply(local_flag, axis=1)
agg2_visitor = df2.groupby(['TA_YMD', 'MCT_SGG_CD', 'visitor_type'])[['TS_AT', 'USE_CNT']].sum().reset_index()
agg2_visitor.to_csv(os.path.join(OUT_DIR, 'shinhan2_daily_region_visitor_type.csv'), index=False, encoding='utf-8-sig')

# 핵심 소비: 세금공과금(전체의 28%)·ZZ_나머지(미분류, 22%)는 상권 소비가 아니고
# 소수의 거액 결제가 일 합계를 좌우하므로 제외한 버전을 따로 만든다
CORE_EXCLUDE = ['세금공과금', 'ZZ_나머지']
df2_core = df2[~df2['MCT_RY_CD'].isin(CORE_EXCLUDE)]
agg2_core = df2_core.groupby(['TA_YMD', 'MCT_SGG_CD'])[['TS_AT', 'USE_CNT']].sum().reset_index()
agg2_core.to_csv(os.path.join(OUT_DIR, 'shinhan2_daily_region_core.csv'), index=False, encoding='utf-8-sig')
agg2_visitor_core = df2_core.groupby(['TA_YMD', 'MCT_SGG_CD', 'visitor_type'])[['TS_AT', 'USE_CNT']].sum().reset_index()
agg2_visitor_core.to_csv(os.path.join(OUT_DIR, 'shinhan2_daily_region_visitor_type_core.csv'), index=False, encoding='utf-8-sig')

log_path = r"C:\Users\user\Downloads\SH\bigcontest\eda_output\aggregate_shinhan_log.txt"
with open(log_path, 'w', encoding='utf-8') as f:
    f.write(f"shinhan1_daily_region_all.csv shape={agg_all.shape}\n")
    f.write(f"shinhan1_daily_region_consumer_only.csv shape={agg_consumer.shape}\n")
    f.write(f"shinhan2_daily_region.csv shape={agg2.shape}\n")
    f.write(f"shinhan2_daily_region_visitor_type.csv shape={agg2_visitor.shape}\n")
    f.write("\nvisitor_type value_counts:\n")
    f.write(str(df2['visitor_type'].value_counts()) + "\n")

print('done ->', log_path)
