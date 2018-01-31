import numpy as np
import datetime
from stock_object import Stock
from alpha_vantage_api.data_viewer import DataViewer
from linear_regressor import StockLinearRegressor
import matplotlib.pyplot as plt
import os
import shutil


start_date = "2017-10-01"
end_date = "2017-11-22"
start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
viewer = DataViewer()
path = ".\\var\\linear_regression\\"
if os.path.exists(path):
    shutil.rmtree(path)
os.mkdir(path)
with open("symbol_list.txt", "r") as symbol_file:
    regr = StockLinearRegressor()
    for symbol in symbol_file.read().split("\n"):
        print("Regressing " + symbol)
        stock_obj = Stock(symbol, start_date=start_date, end_date=end_date)
        data = stock_obj.get_daily_adj_close_price(mode='percentage')
        time_index = []
        regr_data = []
        for x in range(0, len(data)):
            if data[x] is not None:
                time_index.append(x)
                regr_data.append(data[x])
        regr.fit(symbol, time_index, regr_data)
    top_stock_sym, top_stock_coeff = regr.get_top()
    print("Result:")
    for symbol in top_stock_sym:
        stock_obj = Stock(symbol, start_date=start_date, end_date=end_date)
        print(stock_obj)
        data_node = stock_obj.get_daily_adj_close_price()
        plt.plot(data_node)
        plt.savefig(path + symbol + ".png")
        plt.clf()
