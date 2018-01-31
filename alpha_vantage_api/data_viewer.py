import psycopg2
import configparser
import os
import shutil
import re
import psycopg2.extras
import pendulum

class DataViewer:
    def __init__(self):
        if not os.path.exists(".\\default.cfg"):
            shutil.copy(".\\default_dist.cfg", ".\\default.cfg")
        config = configparser.ConfigParser()
        config.read(".\default.cfg")
        self._conn = psycopg2.connect(
            host=config["database"]["host"],
            database=config["database"]["db_name"],
            user=config["database"]["user"],
            password=config["database"]["password"],
        )

    def get_daily_price(self, stock_symbol, start_date, end_date, sparse=False):
        """
                :param: stock_symbol
                :param: start_date
                :param: end_date
                :param: sparse
                :rtype: (list[datetime], list(dict[
                        stock_uid,
                        stock_symbol,
                        entry_date,
                        open_price,
                        close_price,
                        high_price,
                        low_price,
                        adj_close_price
                ]))
                """
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            assert re.match("^\d{1,4}.?(HK)?$", str(stock_symbol).zfill(4), re.IGNORECASE), "Invalid stock symbol format"
            start_date_obj = pendulum.parse(start_date)
            end_date_obj = pendulum.parse(end_date)
            assert end_date_obj > start_date_obj, "End date must be after start date"
            cursor.execute("""
                SELECT
                    stock_primary.stock_uid,
                    stock_primary.stock_symbol,
                    entry_date, 
                    open_price,
                    close_price,
                    high_price,
                    low_price,
                    adj_close_price,
                    volume                  
                FROM stock_primary 
                LEFT JOIN daily_adj_price 
                ON stock_primary.stock_uid = daily_adj_price.stock_uid 
                WHERE stock_primary.stock_symbol LIKE %(stock_symbol)s 
                AND entry_date BETWEEN %(start_date)s AND %(end_date)s
            """, {
                "stock_symbol": "%" + str(stock_symbol).zfill(4) + "%",
                "start_date": start_date_obj.to_date_string(),
                "end_date": end_date_obj.to_date_string()
            })
            value_list = []
            date_list = []
            for row in cursor.fetchall():
                date_list.append(row["entry_date"])
                value_list.append({
                    "stock_uid": row["stock_uid"],
                    "stock_symbol": row["stock_symbol"],
                    "entry_date": row["entry_date"],
                    "open_price": row["open_price"],
                    "close_price": row["close_price"],
                    "high_price": row["high_price"],
                    "low_price": row["low_price"],
                    "adj_close_price": row["adj_close_price"],
                    "volume": row["volume"],
                })
            if sparse:
                date = start_date_obj
                while date <= end_date_obj:
                    if date.weekday() <= 4 and date.date() not in date_list:
                        date_list.append(date.date())
                        value_list.append(None)
                    date = date.add(days=1)
            return sorted(date_list), [x for y, x in sorted(zip(date_list, value_list))]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()