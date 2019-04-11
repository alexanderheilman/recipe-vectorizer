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
    remove_duplicates_and_update_search_results()
    
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
        # If redirected to different url, id# has been changed and must be updated
        if next_recipe['href'] != browser.current_url:
            update_results_collection(next_recipe, browser.current_url, results_coll)
        try:
            info = get_recipe_info(browser)
            # If recipe in database, update rating info...
            if list(recipes_coll.find({'id':info['id']})):
                recipes_coll.update_one({'id':info['id']},
                                        {"$set":{'rating_info': info['rating_info']}},
                                        upsert=False)
            # Else if recipe is in database under outdated recipe_id, update rating and id
            elif list(recipes_coll.find({'id':next_recipe['id']})):
                recipes_coll.update_one({'id':next_recipe['id']},
                                        {"$set":{'rating_info': info['rating_info'],
                                                 'id' : info['id'],
                                                 'href' : info['href']}},
                                        upsert=False)
            # Else insert new entry
            else:
                recipes_coll.insert_one(info)
            mark_as_viewed(info['id'], results_coll)
            count += 1
            print('Last recipe:\nID : {0}\nName : {1}'.format(info['id'],
                                                              info['name']))
            if count >= max_count:
                break
            print('{} recipes collected\n'.format(count))
        except:
            mark_as_viewed(next_recipe['id'], results_coll, error=True)
            print('Error reading recipe: {}'.format(next_recipe['name']))
        next_recipe = get_next_recipe(results_coll, reverse=reverse)
        # If attempting to collect repeat recipe, purge duplicates 
        # (not sure why but it appears to work)
        if next_recipe['name'] == info['name']:
            remove_duplicates_and_update_search_results()
        next_recipe = get_next_recipe(results_coll, reverse=reverse)
    browser.quit()
    print('Search complete. {} recipes found'.format(count))