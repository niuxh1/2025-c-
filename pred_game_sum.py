import pandas as pd
import numpy as np
import math
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 读取数据
df = pd.read_csv('summer2.csv')  # 请根据实际路径调整

# 抛弃 Year 小于 2016 的数据
df = df[df['Year'] >= 2016]

# 按 NOC 分组
grouped = df.groupby('NOC')

# 存储预测结果
predictions = {}

# 获取 2024 年的数据
data_2024 = df[df['Year'] == 2024]

# 计算 2024 年的总和并向上取整目标值
total_game_sum_2024 = data_2024['game_sum'].sum()
total_athlete_count_2024 = data_2024['Athlete_Count'].sum()

# 目标总和：至少是 2024 年的 1_medal.05 倍（向上取整保证整数）
target_total_game_sum = math.ceil(total_game_sum_2024 * 1.05)
target_total_athlete_count = math.ceil(total_athlete_count_2024 * 1.05)

# 遍历每个 NOC 组
for noc, group in grouped:
    try:
        print(f"正在处理 {noc}...")

        # ---- 数据预处理 ----
        group_sorted = group.sort_values('Year')
        X = group_sorted[['Year']]
        y = group_sorted[['game_sum', 'Athlete_Count']]

        # 标准化特征
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # ---- 训练模型 ----
        model = RandomForestRegressor(random_state=42)
        model.fit(X_scaled, y)

        # ---- 预测 2028 年 ----
        year_2028 = np.array([[2028]])
        year_2028_scaled = scaler.transform(year_2028)
        pred_2028 = model.predict(year_2028_scaled)

        # 四舍五入并确保最小值为0或1
        pred_game_sum = max(0, int(round(pred_2028[0][0])))
        pred_athlete_count = max(1, int(round(pred_2028[0][1])))

        predictions[noc] = {
            'game_sum': pred_game_sum,
            'Athlete_Count': pred_athlete_count
        }

    except Exception as e:
        print(f"{noc} 预测失败: {str(e)}")
        continue

# ---- 后处理：强制调整总和 ----
# 计算初始预测总和
total_pred_game_sum = sum(v['game_sum'] for v in predictions.values())
total_pred_athlete_count = sum(v['Athlete_Count'] for v in predictions.values())


# 计算调整因子并应用
def adjust_values(predictions, total_pred, target_total, key):
    if total_pred == 0:
        return predictions  # 防止除零错误

    # 计算调整因子
    adjustment_factor = target_total / total_pred

    # 应用线性调整并四舍五入
    adjusted_total = 0
    adjusted_predictions = {}
    for noc in predictions:
        adjusted_value = predictions[noc][key] * adjustment_factor
        adjusted_value = max(0, int(round(adjusted_value))) if key == 'game_sum' else max(1, int(round(adjusted_value)))
        adjusted_predictions[noc] = adjusted_value
        adjusted_total += adjusted_value

    # 微调差异（确保整数调整）
    delta = target_total - adjusted_total
    if delta != 0:
        # 找到最大值的NOC进行调整
        max_noc = max(predictions.keys(), key=lambda x: adjusted_predictions[x])
        adjusted_predictions[max_noc] += delta
        # 确保调整后的值合法
        if key == 'game_sum':
            adjusted_predictions[max_noc] = max(0, adjusted_predictions[max_noc])
        else:
            adjusted_predictions[max_noc] = max(1, adjusted_predictions[max_noc])

    # 更新predictions字典
    for noc in predictions:
        predictions[noc][key] = adjusted_predictions[noc]

    return predictions


# 调整game_sum
predictions = adjust_values(predictions, total_pred_game_sum, target_total_game_sum, 'game_sum')

# 调整Athlete_Count
predictions = adjust_values(predictions, total_pred_athlete_count, target_total_athlete_count, 'Athlete_Count')

# ---- 最终验证 ----
final_game_sum = sum(v['game_sum'] for v in predictions.values())
final_athlete_count = sum(v['Athlete_Count'] for v in predictions.values())

print(f"\n最终game_sum总和: {final_game_sum} (目标: {target_total_game_sum})")
print(f"最终Athlete_Count总和: {final_athlete_count} (目标: {target_total_athlete_count})")

# ---- 结果保存 ----
result_df = pd.DataFrame.from_dict(predictions, orient='index').reset_index()
result_df.rename(columns={'index': 'NOC'}, inplace=True)
result_df['Year'] = 2028
result_df['Host'] = np.where(result_df['NOC'] == "United States", 1, 0)
result_df = result_df[['NOC', 'Year', 'Athlete_Count', 'Host', 'game_sum']]

# 确保所有数值列存储为整数
result_df = result_df.astype({
    'Athlete_Count': 'int32',
    'game_sum': 'int32',
    'Host': 'int8',
    'Year': 'int16'
})

result_df.to_csv('predictions.csv', index=False)
print("\n调整后的预测结果：")
print(result_df.to_string(index=False))