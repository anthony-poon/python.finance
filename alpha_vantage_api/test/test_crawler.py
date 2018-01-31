from unittest import TestCase
from configparser import ConfigParser
from alpha_vantage_api.crawler import Crawler
import os
import logging
import json
from pprint import pprint
from pythonjsonlogger import jsonlogger

class TestCrawler(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCrawler, self).__init__(*args, **kwargs)
        config = ConfigParser()
        print(os.getcwd())
        config.read("../../default.cfg")
        self._db_host = config["database"]["host"]
        self._db_name = config["database"]["db_name"]
        self._db_user = config["database"]["user"]
        self._db_password = config["database"]["password"]
        self._api_key = config["alpha_vantage"]["api_key"]

    def test_set_logging_level(self):
        stock_symbol = "0700.HK"
        crawler = Crawler(self._api_key, stock_symbol, self._db_host, self._db_name, self._db_user, self._db_password)
        crawler.set_logging_level(logging.INFO)
        self.assertEqual(crawler._logger.getEffectiveLevel(), logging.INFO)
        crawler.set_logging_level(logging.DEBUG)
        self.assertEqual(crawler._logger.getEffectiveLevel(), logging.DEBUG)

    def test_add_logging_path(self):
        stock_symbol = "0700.HK"
        crawler = Crawler(self._api_key, stock_symbol, self._db_host, self._db_name, self._db_user, self._db_password)
        crawler.add_logging_path("./log")
        crawler.add_logging_path("./log/testing.txt")

    def test_get_daily_adjusted(self):
        stock_symbol = "0700.HK"
        crawler = Crawler(self._api_key, stock_symbol, self._db_host, self._db_name, self._db_user, self._db_password)
        result = crawler._get_daily_adjusted()
        self.assertIsNotNone(result)
        dump_path = "./log/data_dump.txt"
        if os.path.exists(dump_path):
            os.remove(dump_path)
        with open(dump_path, "w") as output_file:
            output_file.write(json.dumps(result, indent=4))
        stock_symbol = "fake"
        crawler = Crawler(self._api_key, stock_symbol, self._db_host, self._db_name, self._db_user, self._db_password)
        with self.assertRaises(ConnectionError) as exception:
            crawler._get_daily_adjusted()