import os
import shutil
import configparser
import psycopg2
import pendulum
from alpha_vantage_api.data_viewer import DataViewer
import numpy as np
from sklearn import linear_model


class Stock:
    def __init__(self, stock_symbol, start_date=None, end_date=None):
        if not os.path.exists(".\default.cfg"):
            shutil.copy(".\default_dist.cfg", ".\default.cfg")
        self._config = configparser.ConfigParser()
        self._config.read(".\default.cfg")
        with psycopg2.connect(
            host=self._config["database"]["host"],
            database=self._config["database"]["db_name"],
            user=self._config["database"]["user"],
            password=self._config["database"]["password"],
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        stock_uid,
                        stock_name 
                    FROM stock_primary 
                    WHERE stock_symbol LIKE %(stock_symbol)s
                """, {
                    "stock_symbol": "%" + str(stock_symbol) + "%"
                })
                result = cursor.fetchone()
                if result is None:
                    raise Exception("Unknown stock symbol")
                self._stock_uid = result[0]
                self._stock_name = result[1]
                self._stock_symbol = stock_symbol

                # Populate data
                if start_date is None or end_date is None:
                    start_date = pendulum.now().subtract(years=1).to_date_string()
                    end_date = pendulum.now().date().to_date_string()
                viewer = DataViewer()
                self._date_index, data_row = viewer.get_daily_price(stock_symbol, start_date, end_date, sparse=True)
                self._close_price = []
                self._low_price = []
                self._high_price = []
                self._adj_close_price = []
                self._volume = []
                for row in data_row:
                    if row is not None:
                        self._close_price.append(row["close_price"])
                        self._low_price.append(row["low_price"])
                        self._high_price.append(row["high_price"])
                        self._adj_close_price.append(row["adj_close_price"])
                        self._volume.append(row["volume"])
                    else:
                        self._close_price.append(None)
                        self._low_price.append(None)
                        self._high_price.append(None)
                        self._adj_close_price.append(None)
                        self._volume.append(None)

    def __str__(self):
        return "%-8s %s" % (self._stock_symbol, self._stock_name)

    def fill_sparse(self, factor=10):
        self._fill_sparse(self._close_price, factor)
        self._fill_sparse(self._low_price, factor)
        self._fill_sparse(self._high_price, factor)
        self._fill_sparse(self._adj_close_price, factor)
        self._fill_sparse(self._volume, factor)

    def _fill_sparse(self, array_like, factor):
        regr = linear_model.LinearRegression()
        indept = []
        dept = []
        for x in range(0, len(self._date_index)):
            if array_like[x] is not None:
                indept.append(x)
                dept.append(array_like[x])
        indept = np.array(indept).reshape(-1, 1)
        dept = np.array(dept).reshape(-1, 1)
        regr.fit(indept, dept)
        intercept = regr.intercept_[0]
        slope = regr.coef_[0][0]
        for x in range(0, len(self._date_index)):
            if array_like[x] is None:
                array_like[x] = intercept + x * slope

    def get_daily_percentage_change(self):
        data_arr = self._adj_close_price
        return_arr = []
        first_number = None
        for x in range(0, len(data_arr) - 1):
            if first_number is None:
                if data_arr[x] is not None:
                    first_number = data_arr[x]
                    return_arr.append(0)
                else:
                    return_arr.append(0)
            else:
                if data_arr[x] is None:
                    return_arr.append(None)
                else:
                    delta_change = (data_arr[x] - first_number) / first_number
                    return_arr.append(delta_change)
        return return_arr

    def get_daily_adj_close_price(self):
        return self._adj_close_price
