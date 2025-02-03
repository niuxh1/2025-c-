import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plot
from doc.source.images.hero import title

data = pd.read_csv("summer.csv")
data_country = data.set_index("NOC")
result = data_country.groupby('NOC').agg(lambda x: x.tolist())
# print(result.loc["Japan"])

host = pd.read_csv("summerOly_hosts.csv")
host.loc[:, "Host"] = host.loc[:, "Host"].str.split(",", expand=True)[1].str.strip()

# print(host)
for i in range(len(host)):

    now_host = host.loc[i, "Host"]
    now_year=host.loc[i,"Year"]
    if now_host is None:
        continue
    print(now_host)
    # print(data_country.loc[now_host])

    datas_host= data_country.loc[now_host,"Rank":"Year"]
    matrix_host = data_country.loc[now_host,"Host"]
    datas_host=datas_host.set_index("Year")
    datas_host = datas_host.sort_values(by='Year')
    print(datas_host)
    ax = datas_host.plot(title=f"the {now_year}'s host is {now_host}")
    ax.scatter(now_year, datas_host.loc[now_year,"Rank"], color='red', zorder=5)
    ax.annotate(f'({now_year}, {datas_host.loc[now_year,"Rank"]})',
                xy=(now_year, datas_host.loc[now_year,"Rank"]),
                xytext=(now_year + 1, datas_host.loc[now_year,"Rank"] + 1),  # 标注文本的位置
                arrowprops=dict(facecolor='black', shrink=0.05))
    ax.set_xlabel("Year")
    ax.set_ylabel("medal_num")
    ax2 = ax.twinx()
    ax.set_ylabel("Rank")
    plt.show()
