from stock_object import Stock
import matplotlib.pyplot as plt
import os
import shutil


path = ".\\var\\daily_adj_close_graph\\"
if os.path.exists(path):
    shutil.rmtree(path)
os.mkdir(path)
with open("symbol_list.txt", "r") as symbol_file:
    for symbol in symbol_file.read().split("\n"):
        print(symbol)
        stock_obj = Stock(symbol)
        plt.plot(stock_obj.get_daily_adj_close_price())
        plt.savefig(path + symbol + ".png")
        plt.clf()
