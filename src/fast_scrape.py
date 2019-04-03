import selenium
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import string
from string import ascii_lowercase
import time
import numpy as np
import pandas as pd
from functions import *
from sys import argv, exit
import pymongo

if __name__ == '__main__':
    if len(argv) != 3:
        print("Usage: python {} <search_term> <num_pages>".format(argv[0]))
        exit(1)
    keyword = argv[1]
    num_pages = int(argv[2])
    # Connect to MongoClient and get collection handles
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    results_coll = db['search_results']
    users_coll = db['users']
    # Launch headless browser with selenium
    options = Options()
    options.headless = True
    capabilities = DesiredCapabilities().CHROME
    capabilities['pageLoadStrategy'] = 'none'
    browser = Chrome(desired_capabilities=capabilities, options=options)
    # Go to homepage and search 
    search_allrecipes(keyword, browser, typo_rate=0.1, sleep=10)
    time.sleep(10)
    populate_search_page(browser, num_pages=num_pages, scroll_delay=10)
    add_results_to_collection(browser, results_coll)
    count = 0
    next_recipe = results_coll.find_one({'viewed':0})
    while next_recipe:
        browser.get(next_recipe['href'])
        time.sleep(10)
        try:
            recipes_coll.insert_one(get_recipe_info(browser))
            mark_as_viewed(next_recipe['id'], results_coll)
            count += 1
            print('Last recipe: {}'.format(next_recipe['name']))
            print('{} recipes collected'.format(count))
        except:
            mark_as_viewed(next_recipe['id'], results_coll, error=True)
            print('Error reading recipe: {}'.format(next_recipe['name']))
        next_recipe = results_coll.find_one({'viewed':0})
    print('Search complete. {} recipes found'.format(count))
