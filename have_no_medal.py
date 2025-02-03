import pandas as pd

# 读取数据
data = pd.read_csv('summer2.csv')

# 将 Year 列转换为整数
data['Year'] = data['Year'].astype(int)

# 按 NOC 分组
groups = data.groupby('NOC')

# 存储 2024 年之前从未获得奖牌的国家
no_medal_before_2028 = []

# 遍历每个国家/地区
for name, group in groups:
    # 筛选 2024 年之前的数据
    group_before_2028 = group[group['Year'] < 2028]

    # 检查是否从未获得奖牌
    if group_before_2028['Total'].sum() == 0:
        no_medal_before_2028.append(name)

# 打印结果
print("2024 年之前从未获得奖牌的国家：")
print(no_medal_before_2028)

# 保存结果到 CSV 文件（可选）
no_medal_df = pd.DataFrame(no_medal_before_2028, columns=['NOC'])
no_medal_df.to_csv('no_medal_before_2028.csv', index=False)