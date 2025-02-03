import pandas as pd


url = "https://en.wikipedia.org/wiki/List_of_IOC_country_codes"
tables = pd.read_html(url)


ioc_table = tables[0]


print(ioc_table.head())

ioc_table = ioc_table[["Code", "National Olympic Committee"]]


ioc_table.to_csv("ioc_country_codes.csv", index=False)