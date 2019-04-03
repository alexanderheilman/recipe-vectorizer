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
    if len(argv) != 3:
        print("Usage: python {} <keyword> <max_pages>".format(argv[0]))
        exit(1)
    keyword = argv[1]
    max_pages = int(argv[2])
    # Connect to MongoClient and get collection handles
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    results_coll = db['search_results']
    # Launch headless browser with selenium
    options = Options()
    options.headless = True
    capabilities = DesiredCapabilities().CHROME
    capabilities['pageLoadStrategy'] = 'none'
    browser = Chrome(desired_capabilities=capabilities, options=options)
    for i in range(1,max_pages+1):
        url = create_search_url(keyword, i)
        browser.get(url)
        time.sleep(10)
        add_results_to_collection(browser, results_coll)
        print('{} result pages collected.'.format(i))
    browser.quit()
    print('Search complete!')