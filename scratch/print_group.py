import pandas as pd
from scripts.holdout_validation_real import fix_data_columns
df = pd.read_csv('data/data.csv')
df = fix_data_columns(df)
df['group_id'] = df['age'].astype(str) + '-' + df['gender'].astype(str) + '-' + df['interest1'].astype(str) + '-' + df['interest2'].astype(str) + '-' + df['interest3'].astype(str)
group = df[df['group_id'] == '30-34-F-10-13-14']
print(group[['ad_id', 'impressions', 'total_conversion']])
