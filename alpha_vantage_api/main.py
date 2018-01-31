from configparser import ConfigParser
from alpha_vantage_api.crawler import Crawler
import logging
import time
import psycopg2


def main():
    config = ConfigParser()
    config.read("..\\default.cfg")
    db_host = config["database"]["host"]
    db_name = config["database"]["db_name"]
    db_user = config["database"]["user"]
    db_password = config["database"]["password"]
    api_key = config["alpha_vantage"]["api_key"]
    with psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                    SELECT stock_symbol FROM stock_primary WHERE company_url IS NOT NULL 
                """)
            result = cursor.fetchall()
            symbol_list = [i[0] for i in result]
        for symbol in symbol_list:
            time.sleep(1)
            crawler = Crawler(api_key, symbol, db_host, db_name, db_user, db_password)
            crawler.set_full_mode()
            crawler.add_logging_path("../var/log/av_crawler")
            result, row_count = crawler.run()
            if result:
                print("{0} row(s) updated for {1}".format(row_count, symbol))
            else:
                print("Error occurred for {0}".format(symbol))


if __name__ == "__main__":
    main()
