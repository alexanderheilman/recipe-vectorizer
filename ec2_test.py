import selenium
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import string
from string import ascii_lowercase
import time
import numpy as np
import pandas as pd
from functions import *
from sys import argv, exit
import pymongo

if __name__ == '__main__':
    if len(argv) != 2:
        print("Usage: python {} <food_item>".format(argv[0]))
        exit(1)
    food = argv[1]
    # Connect to MongoClient and get collection handles
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    results_coll = db['search_results']
    users_coll = db['users']
    # Launch headless browser with selenium
    options = Options()
    options.headless = True
    browser = Chrome(options=options)
    # Go to homepage and search 
    search_allrecipes(food, browser, typo_rate=0.1)
    add_results_to_collection(browser, results_coll)
    count = 0
    while True:
        # Find next unviewed recipe; or load more results
        next_recipe = results_coll.find_one({'viewed':0})
        if next_recipe:
            # Check for relevance; break if consecutive items are not
            if food.lower() not in next_recipe['name'].lower().split():
                if irrelevant:
                    break
                irrelevant = True
            else:
                irrelevant = False
            # Go to recipe page, scrape data, and return
            search_page = browser.current_url
            browser.get(next_recipe['href'])
            time.sleep(5)
            recipes_coll.insert_one(get_recipe_info(browser))
            mark_as_viewed(next_recipe['id'], results_coll)
            count += 1
            print('Last recipe: {}'.format(next_recipe['name']))
            print('{} recipes collected'.format(count))
            browser.get(search_page)
        else:
            populate_search_page(browser, num_pages=1)
            add_results_to_collection(browser, results_coll)
    print('Search complete. {} recipes found'.format(count))