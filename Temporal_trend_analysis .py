import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datacleaning

df_clean = datacleaning.df_clean.copy()

df_time = df_clean.rename(columns={
    'birthCountryLabel': 'birth',
    'mainResearchCountry': 'research',
    'awardYear': 'year'
})

df_time['year'] = df_time['year'].astype(int)
df_time = df_time[(df_time['year'] >= 1901) & (df_time['year'] <= 2024)]
df_time['decade'] = (df_time['year'] // 10) * 10


def assign_period(y):
    if y <= 1945:
        return "1901–1945"
    elif y <= 1990:
        return "1946–1990"
    else:
        return "1991–2024"


df_time['period'] = df_time['year'].apply(assign_period)

df_time['migrated'] = df_time['birth'] != df_time['research']
df_time['stayed'] = df_time['birth'] == df_time['research']

trend_mobility = df_time.groupby('decade').agg(
    migration_rate=('migrated', 'mean'),
    stay_rate=('stayed', 'mean'),
    count=('birth', 'size')
).reset_index()

print(" Mobility trend by decade ")
print(trend_mobility)

plt.figure(figsize=(7, 4))
plt.plot(trend_mobility['decade'], trend_mobility['migration_rate'], marker='o', label='Migration rate')
plt.plot(trend_mobility['decade'], trend_mobility['stay_rate'], marker='o', label='Stay rate')
plt.xlabel('Decade')
plt.ylabel('Proportion')
plt.title('Nobel Laureate Mobility vs Stay Rate Over Time')
plt.legend()
plt.tight_layout()
plt.savefig('trend_migration_stay_by_decade.png', dpi=300)
plt.show()

country_decade = (
    df_time
    .groupby(['decade', 'research'])
    .size()
    .reset_index(name='count')
)

total_decade = (
    df_time
    .groupby('decade')
    .size()
    .reset_index(name='total_count')
)

country_decade = country_decade.merge(total_decade, on='decade')
country_decade['share'] = country_decade['count'] / country_decade['total_count']

print("  shares by decade and research country ")
print(country_decade.head())

top_countries = (
    country_decade.groupby('research')['count']
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index
    .tolist()
)

print("Top countries by total Nobel laureates")
print(top_countries)

country_decade['research_group'] = np.where(
    country_decade['research'].isin(top_countries),
    country_decade['research'],
    'Other'
)

country_decade_grouped = (
    country_decade
    .groupby(['decade', 'research_group'])
    .agg(count=('count', 'sum'))
    .reset_index()
)

country_decade_grouped = country_decade_grouped.merge(total_decade, on='decade')
country_decade_grouped['share'] = country_decade_grouped['count'] / country_decade_grouped['total_count']

print(" Grouped counts & shares (Top countries + Other")
print(country_decade_grouped.head())

plt.figure(figsize=(8, 5))
for c in sorted(country_decade_grouped['research_group'].unique()):
    sub = country_decade_grouped[country_decade_grouped['research_group'] == c]
    plt.plot(sub['decade'], sub['share'], marker='o', label=c)

plt.xlabel('Decade')
plt.ylabel('Share of Nobel Laureates (research location)')
plt.title('Geographical Trend of Nobel Prize-winning Research (by decade)')
plt.legend()
plt.tight_layout()
plt.savefig('trend_geography_share_by_decade.png', dpi=300)
plt.show()

results = []
for c, sub in country_decade_grouped.groupby('research_group'):
    if len(sub) < 2:
        continue
    x = sub['decade'].values.astype(float)
    y = sub['share'].values.astype(float)
    slope, intercept = np.polyfit(x, y, 1)
    results.append({
        'country_group': c,
        'slope': slope,
        'intercept': intercept
    })

reg_df = pd.DataFrame(results).sort_values('slope', ascending=False)
print(" Linear trend (share ~ decade) for each country group ")
print(reg_df)

period_country = (
    df_time
    .merge(country_decade[['research', 'research_group']].drop_duplicates(),
           on='research', how='left')
)

period_summary = (
    period_country
    .groupby(['period', 'research_group'])
    .size()
    .reset_index(name='count')
)

period_total = (
    period_country
    .groupby('period')
    .size()
    .reset_index(name='total_count')
)

period_summary = period_summary.merge(period_total, on='period')
period_summary['share'] = period_summary['count'] / period_summary['total_count']

print("Period-level share by country group ")
print(period_summary)

plt.figure(figsize=(8, 5))

period_order = ["1901–1945", "1946–1990", "1991–2024"]
for c in sorted(period_summary['research_group'].unique()):
    sub = period_summary[period_summary['research_group'] == c]
    sub = sub.set_index('period').reindex(period_order).reset_index()
    plt.plot(sub['period'], sub['share'], marker='o', label=c)

plt.xlabel('Period')
plt.ylabel('Share of Nobel Laureates (research location)')
plt.title('Geographical Shift of Nobel Prize-winning Research by Period')
plt.legend()
plt.tight_layout()
plt.savefig('trend_geography_share_by_period.png', dpi=300)
plt.show()

concentration = (
    country_decade_grouped
    .groupby('decade')
    .apply(lambda g: (g['share'] ** 2).sum())
    .reset_index(name='herfindahl_index')
)

print(" Concentration of Nobel research by decade (Herfindahl index) ")
print(concentration)

plt.figure(figsize=(7, 4))
plt.plot(concentration['decade'], concentration['herfindahl_index'], marker='o')
plt.xlabel('Decade')
plt.ylabel('Concentration Index (Herfindahl)')
plt.title('Concentration of Nobel Prize-winning Research Over Time')
plt.tight_layout()
plt.savefig('trend_concentration_by_decade.png', dpi=300)
plt.show()

volatility = (
    country_decade_grouped
    .groupby('research_group')['share']
    .agg(std_share='std', mean_share='mean')
    .reset_index()
    .sort_values('std_share', ascending=False)
)

print(" Volatility of research share by country group ")
print(volatility)
