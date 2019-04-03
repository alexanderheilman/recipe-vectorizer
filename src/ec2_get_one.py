import selenium
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import string
from string import ascii_lowercase
import time
import numpy as np
from functions import *
import pymongo

if __name__ == '__main__':
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
    next_recipe = results_coll.find_one({'viewed':0})
    # Go to recipe page and scrape data
    print('Getting {}...'.format(next_recipe['href']))
    browser.get(next_recipe['href'])
    try:
        recipes_coll.insert_one(get_recipe_info(browser))
        mark_as_viewed(next_recipe['id'], results_coll)
        print('Recipe name: {}'.format(next_recipe['name']))
        print('Collected!')
    except:
        mark_as_viewed(next_recipe['id'], results_coll, error=True)
        print('Error reading recipe: {}'.format(next_recipe['name']))
