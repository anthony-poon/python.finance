import os
import shutil
import psycopg2
import requests
import logging
import re
import configparser


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: [%(asctime)s] %(message)s')
    fh = logging.FileHandler('stock_name_crawler.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if not os.path.exists("..\\default.cfg"):
        shutil.copy("..\\default_dist.cfg", "..\\default.cfg")
    config = configparser.ConfigParser()
    config.read("..\\default.cfg")

    result_url_prefix = "https://www.hkex.com.hk/eng/csm/"
    url_template = "https://www.hkex.com.hk/eng/csm/ws/Result.asmx/GetData?location=companySearch&" \
          "SearchMethod=2&" \
          "LangCode=en&" \
          "StockCode=&" \
          "StockName=&" \
          "Ranking=ByName&" \
          "StockType=ALL&" \
          "mkt=hk&" \
          "PageNo={0}&" \
          "ATypeSHEx=&" \
          "AType=&" \
          "FDD=&" \
          "FMM=&" \
          "FYYYY=&" \
          "TDD=&" \
          "TMM=&T" \
          "YYYY="
    is_done = False
    page_number = 1
    open("..\\var\\stock_info_dump.txt", "w").close()
    dump_file = open("..\\var\\stock_info_dump.txt", "a")
    with psycopg2.connect(
        host=config["database"]["host"], database=config["database"]["db_name"],
            user=config["database"]["user"], password=config["database"]["password"]
    ) as conn:
        with conn.cursor() as cursor:
            while not is_done:
                url = url_template.format(page_number)
                response = requests.get(url)
                if response.status_code == 200:
                    json_data = response.json()
                    update_timestamp = json_data["LastUpdateDate"]
                    content_data = json_data["data"][0]["content"][0]["table"][0]["tr"]
                    # content_data will have at least 1 row
                    if len(content_data) > 1:
                        for row in content_data:
                            if not row["thead"]:
                                stock_data = {
                                    "stock_code": re.sub("[^\d]", "", row["td"][0][1]).zfill(4) + ".HK",
                                    "stock_name": row["td"][0][2].strip(),
                                    "url": result_url_prefix + row["link"].strip()
                                }
                                print("{0:<10}{1:<70}{2}\n".format(stock_data["stock_code"], stock_data["stock_name"], stock_data["url"]))
                                dump_file.writelines("{0:<10}{1:<70}{2}\n".format(stock_data["stock_code"], stock_data["stock_name"], stock_data["url"]))
                                cursor.execute("""
                                    INSERT INTO stock_primary (stock_symbol, stock_name, company_url) 
                                    VALUES 
                                        (%(stock_code)s, 
                                        %(stock_name)s,
                                        %(url)s) 
                                    ON CONFLICT (stock_symbol) DO UPDATE 
                                        SET stock_symbol = %(stock_code)s,
                                        stock_name = %(stock_name)s,
                                        company_url = %(url)s
                                """, stock_data)
                                if cursor.rowcount < 1:
                                    print(stock_data)
                    else:
                        is_done = True
                    page_number += 1
                else:
                    logger.error("HTTP code " + str(response.status_code))
                    is_done = True
    dump_file.close()
