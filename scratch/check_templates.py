import pandas as pd

df = pd.read_csv('outputs/train_data.csv')
import re

df['base_text'] = df['ad_text'].apply(lambda x: re.sub(r' Great for interest \d+\.', '', x).strip())
print("Unique templates:")
print(df['base_text'].value_counts())

print("\nWin rate of templates:")
df['won'] = df.groupby('group_id')['cvr'].rank(method='first', ascending=False) == 1
win_rates = df.groupby('base_text')['won'].mean().sort_values(ascending=False)
print(win_rates)
df['age_group'] = df['age'].apply(lambda x: x.split('-')[0] if '-' in str(x) else '35')
df['age_group'] = df['age_group'].astype(int)

df['won_int'] = df['won'].astype(int)

pivot = pd.pivot_table(df, values='won_int', index='base_text', columns=['gender', 'age_group'], aggfunc=['mean', 'count'])
print("\nDemographic Pivot Table (Mean Win Rate & Count):")
print(pivot)
