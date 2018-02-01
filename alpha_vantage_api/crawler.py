import requests
import json
import os
import logging
import psycopg2
import pendulum
import time


class Crawler():
    def __init__(self, api_key, symbol, db_host, db_name, db_user, db_password):
        self._db_name = db_name
        self._db_password = db_password
        self._db_host = db_host
        self._db_user = db_user
        self._symbol = symbol
        self._logger_level = logging.WARNING
        self._api_key = api_key
        self._mode = "compact"
        self._url = "https://www.alphavantage.co/query?function={0}&symbol={1}&outputsize={2}&datatype={3}&apikey={4}"
        self._max_retry_count = 5
        self._retry_sleep = 5
        self._log_path = None

    def set_compact_mode(self):
        self._mode = "compact"

    def set_full_mode(self):
        self._mode = "full"

    def set_logging_level(self, level):
        if level not in {
            logging.NOTSET,
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL
        }:
            raise ValueError("Please provide a valid logging level")
        self._logger_level = level
        return self

    def set_logging_path(self, path):
        if os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
            path = path + "/" + self._symbol.replace(".", "_") + ".log"
        self._log_path = path
        return self

    def _get_daily_adjusted(self):
        url = self._url.format(
            "TIME_SERIES_DAILY_ADJUSTED",
            self._symbol,
            self._mode,
            "json",
            self._api_key
        )
        json_obj = None
        data_arr = None
        retry_count = 0
        while data_arr is None and 0 == retry_count < self._max_retry_count:
            response = requests.get(url)
            json_obj = response.json()
            if "Error Message" in json_obj:
                raise ConnectionError(json_obj["Error Message"])
            # stock_symbol = json_obj["Meta Data"]["2. Symbol"]
            if "Time Series (Daily)" not in json_obj:
                retry_count += 1
                print("Retry {0}...".format(retry_count))
                time.sleep(self._retry_sleep)
            else:
                data_arr = []
                for date in json_obj["Time Series (Daily)"]:
                    data_point = json_obj["Time Series (Daily)"][date]
                    data_arr.append({
                        "entry_date": date,
                        "open_price": data_point["1. open"],
                        "high_price": data_point["2. high"],
                        "low_price": data_point["3. low"],
                        "close_price": data_point["4. close"],
                        "adj_close_price": data_point["5. adjusted close"],
                        "volume": data_point["6. volume"],
                        "dividend": data_point["7. dividend amount"],
                        "split_coefficient": data_point["8. split coefficient"],
                    })
        if data_arr is not None:
            return data_arr
        raise ConnectionError("Connection failed after {0} retries. Json dump: {1}".format(str(self._max_retry_count), json.dumps(json_obj)))

    def _db_write(self, data_arr):
        if data_arr is not False:
            with psycopg2.connect(
                host=self._db_host, database=self._db_name, user=self._db_user, password=self._db_password,
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                            INSERT INTO stock_primary (stock_symbol) 
                            VALUES (%s)                         
                            ON CONFLICT DO NOTHING 
                            RETURNING stock_uid""",
                        (self._symbol,))
                    cursor.execute("""
                        SELECT stock_uid FROM stock_primary 
                        WHERE stock_symbol LIKE (%s)
                    """, (self._symbol,))
                    result = cursor.fetchone()
                    row_count = 0
                    for row in data_arr:
                        # check for 0 value
                        valid_entry = True
                        for data_field in [
                            "open_price", "high_price", "low_price", "close_price", "adj_close_price"
                        ]:
                            if valid_entry and float(row[data_field]) < 0.0001:
                                valid_entry = False
                        if valid_entry:
                            row["stock_uid"] = result[0]
                            cursor.execute("""
                                INSERT INTO public.daily_adj_price (
                                    entry_date, 
                                    open_price, 
                                    close_price, 
                                    high_price, 
                                    low_price, 
                                    adj_close_price, 
                                    volume, 
                                    dividend, 
                                    split_coefficient,
                                    stock_uid) 
                                VALUES (
                                    %(entry_date)s, 
                                    %(open_price)s, 
                                    %(close_price)s, 
                                    %(high_price)s, 
                                    %(low_price)s, 
                                    %(adj_close_price)s, 
                                    %(volume)s, 
                                    %(dividend)s, 
                                    %(split_coefficient)s,
                                    %(stock_uid)s)
                                ON CONFLICT DO NOTHING;
                            """, row)
                            conn.commit()
                            row_count += cursor.rowcount
                    return row_count

    def run(self):
        logger = logging.getLogger(__name__ + "_" + self._symbol)
        logger.setLevel(logging.WARNING)
        file_handler = None
        if self._log_path is not None:
            file_handler = logging.FileHandler(self._log_path, mode='w', delay=True)
            formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s ")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        logger.addHandler(stream_handler)
        try:
            json_obj = self._get_daily_adjusted()
            row_count = self._db_write(json_obj)
            logger.info("{0} updated. Row count = {1}".format(self._symbol, row_count))
        except Exception as ex:
            logger.error(str(ex))
            return False, 0
        finally:
            if file_handler is not None:
                file_handler.flush()
                file_handler.close()
            stream_handler.flush()
            stream_handler.close()

        return True, row_count
