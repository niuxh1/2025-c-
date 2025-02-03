import pandas as pd
import matplotlib.pyplot as plt
from pmdarima import auto_arima
from statsmodels.tsa.arima.model import ARIMA
import warnings
from scipy.optimize import minimize
import numpy as np

# 忽略警告
warnings.filterwarnings('ignore')

# 读取 CSV 文件
df = pd.read_csv("summerOly_medal_counts.csv")

# 将 "Year" 列设置为索引,并转换为日期时间格式
df.set_index("Year", inplace=True)
df.index = pd.to_datetime(df.index, format='%Y')

# 创建一个空的字典来存储每个国家的数据
countries_data = {}

# 遍历 DataFrame 的每一行
for index, row in df.iterrows():
    noc = row["NOC"]  # NOC 代表国家奥委会代码
    if noc not in countries_data:
        countries_data[noc] = pd.DataFrame(columns=["Gold", "Silver", "Bronze", "Total"])
    countries_data[noc].loc[index] = [row["Gold"], row["Silver"], row["Bronze"], row["Total"]]

# 将年份索引转换为 DatetimeIndex
for noc, data in countries_data.items():
    countries_data[noc].index = pd.to_datetime(countries_data[noc].index, format='%Y')

# 用于存储所有国家的预测结果
forecast = {}
medal_types = ["Gold", "Silver", "Bronze", "Total"]

# 存储优化前的初始预测值
initial_forecasts = {}

# 对每个国家进行循环
for noc, data in countries_data.items():
    print(f"----- {noc} -----")
    forecast[noc] = {}
    # plt.figure(figsize=(10, 6))
    # plt.title(noc)

    # 首先预测奖牌总数
    stepwise_model_total = auto_arima(data["Total"], seasonal=False, stepwise=True,
                                      suppress_warnings=True,
                                      error_action='ignore',
                                      with_intercept=False)
    if stepwise_model_total.order == (0, 0, 0):  # 处理ARIMA(0,0,0)的情况
        forecast[noc]["Total"] = round(data["Total"].mean())
    else:
        model_total = ARIMA(data["Total"], order=stepwise_model_total.order)
        try:
            model_fit_total = model_total.fit()
            forecast_result_total = model_fit_total.get_forecast(steps=1)
            forecast[noc]["Total"] = round(forecast_result_total.predicted_mean.iloc[0])
        except:  # 模型拟合失败则使用平均值
            forecast[noc]["Total"] = round(data["Total"].mean())

    # 使用ARIMA分别预测金、银、铜牌数量
    for medal_type in ["Gold", "Silver", "Bronze"]:
        print(f"  Predicting {medal_type} medals...")
        stepwise_model = auto_arima(data[medal_type], seasonal=False, stepwise=True,
                                    suppress_warnings=True,
                                    error_action='ignore',
                                    with_intercept=False)

        if stepwise_model.order == (0, 0, 0):  # 处理ARIMA(0,0,0)
            forecast[noc][medal_type] = round(data[medal_type].mean())
        else:
            model = ARIMA(data[medal_type], order=stepwise_model.order)
            try:
                model_fit = model.fit()
                forecast_result = model_fit.get_forecast(steps=1)
                forecast[noc][medal_type] = round(forecast_result.predicted_mean.iloc[0])
            except:  # 模型拟合失败则使用平均值
                forecast[noc][medal_type] = round(data[medal_type].mean())

    initial_forecasts[noc] = forecast[noc].copy()  # 存储初始预测值

# 全局优化，跨所有国家

# 准备优化数据
all_nocs = list(countries_data.keys())  # 所有国家的NOC列表
initial_guess = []  # 优化算法的初始猜测值
for noc in all_nocs:
    initial_guess.extend(
        [initial_forecasts[noc]["Gold"], initial_forecasts[noc]["Silver"], initial_forecasts[noc]["Bronze"]])
initial_guess = np.array(initial_guess)


# 定义全局优化目标函数
def global_objective_function(x):
    total_squared_diff = 0  # 总的平方差
    for i, noc in enumerate(all_nocs):  # 遍历所有国家
        gold = x[i * 3]  # 当前国家的金牌预测值
        silver = x[i * 3 + 1]  # 当前国家的银牌预测值
        bronze = x[i * 3 + 2]  # 当前国家的铜牌预测值

        # 计算每个国家的预测奖牌总数与之前预测的总数之差的平方，并加总
        total_squared_diff += (gold + silver + bronze - initial_forecasts[noc]['Total']) ** 2
    return total_squared_diff


# 定义约束条件（所有国家的每种奖牌类型的总和）
constraints = []
total_golds_forecasted = sum(initial_forecasts[noc]["Gold"] for noc in all_nocs)  # 所有国家金牌预测值的总和
total_silvers_forecasted = sum(initial_forecasts[noc]["Silver"] for noc in all_nocs)  # 所有国家银牌预测值的总和
total_bronzes_forecasted = sum(initial_forecasts[noc]["Bronze"] for noc in all_nocs)  # 所有国家铜牌预测值的总和

print(f"Total golds forecasted: {total_golds_forecasted}")
print(f"Total silvers forecasted: {total_silvers_forecasted}")
print(f"Total bronzes forecasted: {total_bronzes_forecasted}")
# 约束条件：所有国家的金/银/铜牌总数保持不变
constraints.append(
    {'type': 'eq', 'fun': lambda x: sum(x[i * 3] for i in range(len(all_nocs))) - total_golds_forecasted})
constraints.append(
    {'type': 'eq', 'fun': lambda x: sum(x[i * 3 + 1] for i in range(len(all_nocs))) - total_silvers_forecasted})
constraints.append(
    {'type': 'eq', 'fun': lambda x: sum(x[i * 3 + 2] for i in range(len(all_nocs))) - total_bronzes_forecasted})

# 边界：所有奖牌预测值应为非负数
bounds = [(0, None) for _ in range(len(initial_guess))]

# 执行全局优化
result = minimize(global_objective_function, initial_guess, bounds=bounds, constraints=constraints)
optimized_medals = result.x  # 获取优化后的奖牌数量

# 使用优化后的值更新预测值
for i, noc in enumerate(all_nocs):
    forecast[noc]["Gold"] = round(optimized_medals[i * 3])
    forecast[noc]["Silver"] = round(optimized_medals[i * 3 + 1])
    forecast[noc]["Bronze"] = round(optimized_medals[i * 3 + 2])
    forecast[noc]['Total'] = round(forecast[noc]["Gold"] + forecast[noc]["Silver"] + forecast[noc]["Bronze"])

# 绘图部分 (使用更新后的 forecast 值)
for noc, data in countries_data.items():
    if noc != "Germany":
        continue
    plt.figure(figsize=(10, 6))
    plt.title(noc)
    for medal_type in medal_types:
        print(f"  Forecasted {medal_type} medals: {forecast[noc][medal_type]}")
        plt.plot(data.index, data[medal_type], marker='o', linestyle='-', markersize=4, label=medal_type)

        # 绘制预测结果
        last_year = data.index[-1]
        forecast_year = pd.to_datetime(last_year.year + 4, format='%Y')
        plt.scatter(forecast_year, forecast[noc][medal_type], color='black', marker='X', s=50)

        # 添加虚线连接
        plt.plot([last_year, forecast_year], [data[medal_type].iloc[-1], forecast[noc][medal_type]], color='black',
                 linestyle='--')

    plt.legend()
    plt.xticks(rotation=30)
    plt.show()
