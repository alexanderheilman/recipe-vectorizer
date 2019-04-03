import selenium
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import string
from string import ascii_lowercase
import time
import numpy as np
from functions import *
from sys import argv, exit
import pymongo

if __name__ == '__main__':
    if len(argv) != 4:
        print("Usage: python {} <keyword> <starting_page> <ending_page>".format(argv[0]))
        exit(1)
    keyword = argv[1]
    start_pg = int(argv[2])
    end_pg = int(argv[3])
    # Connect to MongoClient and get collection handles
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    results_coll = db['search_results']
    start_len = len(list(results_coll.find()))
    # Launch headless browser with selenium
    options = Options()
    options.headless = True
    capabilities = DesiredCapabilities().CHROME
    capabilities['pageLoadStrategy'] = 'none'
    browser = Chrome(desired_capabilities=capabilities, options=options)
    for i in range(start_pg, end_pg+1):
        url = create_search_url(keyword, i)
        browser.get(url)
        time.sleep(10)
        add_results_to_collection(browser, results_coll)
        print('Page {} collected.'.format(i))
    browser.quit()
    end_len = len(list(results_coll.find()))
    diff = end_len - start_len
    print('Search complete. {} new recipes found.'.format(diff))