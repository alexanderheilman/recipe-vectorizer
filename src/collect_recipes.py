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
        print("Usage: python {} <max_count> <reverse?>".format(argv[0]))
        exit(1)
    max_count = int(argv[1])
    reverse = bool(int(argv[2]))
    # Connect to MongoClient and get collection handles
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    results_coll = db['search_results']
    remove_duplicates_and_update_serach_results()
    
    # Launch headless browser with selenium
    options = Options()
    options.headless = True
    capabilities = DesiredCapabilities().CHROME
    capabilities['pageLoadStrategy'] = 'none'
    browser = Chrome(desired_capabilities=capabilities, options=options)
    # Go to individual recipe pages and scrape
    count = 0
    next_recipe = get_next_recipe(results_coll, reverse=reverse)
    while next_recipe:
        browser.get(next_recipe['href'])
        time.sleep(10)
        try:
            recipes_coll.insert_one(get_recipe_info(browser))
            mark_as_viewed(next_recipe['id'], results_coll)
            count += 1
            print('Last recipe: {}'.format(next_recipe['name']))
            if count >= max_count:
                break
            print('{} recipes collected'.format(count))
        except:
            mark_as_viewed(next_recipe['id'], results_coll, error=True)
            print('Error reading recipe: {}'.format(next_recipe['name']))
        next_recipe = get_next_recipe(results_coll, reverse=reverse)
    browser.quit()
    print('Search complete. {} recipes found'.format(count))