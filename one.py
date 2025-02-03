import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# 读取数据
athletes = pd.read_csv('summerOly_athletes.csv')
host = pd.read_csv('summerOly_hosts.csv')
medal_counts = pd.read_csv('summerOly_medal_counts.csv')
NOC_map = pd.read_csv("ioc_country_codes.csv")

# ========== 数据预处理阶段 ==========

# 清理 NOC_map
NOC_map['Code'] = NOC_map['Code'].str.strip()
NOC_map = NOC_map.set_index('Code')

# 清理 host 数据
host['Host'] = host['Host'].str.replace(r'\s+', ' ', regex=True).str.strip()
host['Host'] = host['Host'].str.replace('Cancelled (WWII – Tokyo had been awarded)', 'None')
host['Host'] = host['Host'].str.split(', ', expand=True)[1]
host['Host'] = host['Host'].replace({
    'Japan (postponed to 2021 due to the coronavirus pandemic)': 'Japan',
    'Soviet Union': 'ROC'
})
host = host.set_index('Year')

# 清理 medal_counts 数据
medal_counts['NOC'] = medal_counts['NOC'].replace({'Soviet Union': 'ROC', 'Russia': 'ROC'})

# ========== 运动员数据处理 ==========

# 清洗运动员数据
athletes['NOC'] = athletes['NOC'].apply(
    lambda x: NOC_map.loc[x, 'National Olympic Committee'] if x in NOC_map.index else x)

# 去重处理：每个运动员在每一年每个国家只保留一条记录
unique_athletes = athletes.drop_duplicates(subset=['Name', 'Year', 'NOC'])

# 统计每个国家每年的参赛人数
athlete_counts = unique_athletes.groupby(['NOC', 'Year']).size().reset_index(name='Athlete_Count')

# ========== 合并数据到 medal_counts ==========

# 将参赛人数合并到 medal_counts
medal_counts = pd.merge(
    medal_counts,
    athlete_counts,
    how='left',
    on=['NOC', 'Year']
).fillna({'Athlete_Count': 0})

# ========== 后续处理流程 ==========

# 标记主办国
medal_counts['Host'] = medal_counts.apply(
    lambda row: 1 if (row['Year'] in host.index) and (host.loc[row['Year'], 'Host'] == row['NOC']) else 0,
    axis=1
)

# 运动项目奖牌统计（原有逻辑）
sport_medals = {}
for i, row in athletes.iterrows():
    country = row['NOC']
    sport = row['Sport']
    year = row['Year']

    sport_medals.setdefault(country, {}).setdefault(year, {}).setdefault(sport, 0)
    sport_medals[country][year][sport] += 1

# 合并运动项目数据
for country, years in sport_medals.items():
    for year, sports in years.items():
        mask = (medal_counts['NOC'] == country) & (medal_counts['Year'] == year)
        if mask.any():
            idx = medal_counts[mask].index
            for sport, count in sports.items():
                if sport not in medal_counts.columns:
                    medal_counts[sport] = 0
                medal_counts.loc[idx, sport] += count
        else:
            new_row = {'NOC': country, 'Year': year, 'Athlete_Count': 0}
            new_row.update(sports)
            medal_counts = pd.concat([medal_counts, pd.DataFrame([new_row])], ignore_index=True)

# 最终处理
medal_counts.fillna(0, inplace=True)
medal_counts['game_sum'] = medal_counts.loc[:, "Basketball":"Racquets"].sum(axis=1)
medal_counts = medal_counts.drop(medal_counts.loc[:, "Basketball":"Racquets"], axis=1)
medal_counts = medal_counts.groupby("NOC").filter(lambda x: x['Year'].max() >= 2024)
print(medal_counts)
time = 2
medal_counts2 = medal_counts[medal_counts["Year"] > 2024 - time * 4].groupby("NOC").filter(lambda x: len(x) >= time)
static_data = medal_counts2[["NOC", "Rank", "Gold", "Silver", "Bronze", "Total"]].groupby("NOC").agg(["mean", "std"])
static_data = static_data.fillna(1)
print(static_data)
medal_counts.to_csv('summer.csv', index=False)
