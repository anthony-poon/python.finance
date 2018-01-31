import logging
import psycopg2
import os
import shutil
import configparser
import re
from math import log

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('stock_name_crawler')
formatter = logging.Formatter('%(levelname)s: [%(asctime)s] %(message)s')
fh = logging.FileHandler('stock_name_crawler.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

url_main = "http://www.hkexnews.hk/hyperlink/hyperlist.HTM"
url_growth_market = "http://www.hkexnews.hk/hyperlink/hyperlist_gem.HTM"

if not os.path.exists("default.cfg"):
    shutil.copy("default_dist.cfg", "default.cfg")
config = configparser.ConfigParser()
config.read("default.cfg")

with psycopg2.connect(
    host=config["database"]["host"],
    database=config["database"]["db_name"],
    user=config["database"]["user"],
    password=config["database"]["password"],
) as conn:
    with conn.cursor() as cursor:
        response = requests.get(url_main)
        if response.status_code != 200:
            logger.error("HTTP response code: " + response.status_code)
            logger.error(response.text)
        else:
            parser = BeautifulSoup(response.text, "html.parser")
            for row_element in parser.find_all("tr", {
                "class": ["tr_normal ms-rteTableOddRow-BlueTable_ENG", "tr_normal ms-rteTableEvenRow-BlueTable_ENG"]
            }):
                all_td = row_element.find_all("td")

                stock_symbol = re.sub("[^\d]", "", all_td[0].text.strip(), flags=re.ASCII)
                stock_name = re.sub("[^\w\s\d.,&()''\-%]", "", all_td[1].text.strip(), flags=re.ASCII)
                url = re.sub("[^\w\s\d://.\-?=\#]", "", all_td[2].text.strip(), flags=re.ASCII)

                stock_data = {
                    "stock_symbol": stock_symbol + "%",
                    "stock_name": stock_name,
                    "url": url,
                    "type": "normal"
                }
                cursor.execute("""
                    UPDATE stock_primary SET 
                        stock_name = %(stock_name)s, 
                        company_url = %(url)s,
                        stock_type = %(type)s 
                    WHERE stock_symbol LIKE %(stock_symbol)s
                """, stock_data)

        response = requests.get(url_growth_market)
        if response.status_code != 200:
            logger.error("HTTP response code: " + response.status_code)
            logger.error(response.text)
        else:
            parser = BeautifulSoup(response.text, "html.parser")
            for row_element in parser.find_all("tr", {
                "class": "tr_normal"
            }):
                all_td = row_element.find_all("td")

                stock_symbol = re.sub("[^\d]", "", all_td[0].text.strip(), flags=re.ASCII)
                stock_name = re.sub("[^\w\s\d.,&()''\-%]", "", all_td[1].text.strip(), flags=re.ASCII)
                url = re.sub("[^\w\s\d://.\-?=\#]", "", all_td[2].text.strip(), flags=re.ASCII)

                stock_data = {
                    "stock_symbol": stock_symbol + "%",
                    "stock_name": stock_name,
                    "url": url,
                    "type": "growth_market"
                }
                cursor.execute("""
                    UPDATE stock_primary SET 
                        stock_name = %(stock_name)s, 
                        company_url = %(url)s,
                        stock_type = %(type)s 
                    WHERE stock_symbol LIKE %(stock_symbol)s
                """, stock_data)